"""
读取指定目录的json文件，获取image字段的值，用 docker pull <image ref> 拉取镜像

使用方式：python pull_all.py <input_dir> [--concurrency 4] [--retry 1] [--dry-run]
example:
python pull_all.py /app/test_utils/CMRx2026/submission/json

前置条件：先运行 mark_latest.py --write <input_dir> 生成 is_latest 标记
- 读取目录下的所有json文件，仅提取 is_latest=True 提交的 image 字段并去重
- 然后并发执行 docker pull <image> 拉取镜像（失败自动重试）
- 最后汇总成功/失败的镜像
"""

import argparse
import json
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PULL_TIMEOUT = 3600  # 单个镜像拉取超时时间（秒）
print_lock = threading.Lock()


def load_images(input_dir):
    """读取目录下所有 json 文件，仅提取 is_latest=True 记录的 image 字段（去重）

    返回 (去重后的镜像列表, image -> 关联 uid 列表 的映射)
    """
    images = []
    image_uids = {}
    seen = set()
    missing_flag = 0
    for path in sorted(Path(input_dir).glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[warn] 跳过无法解析的文件 {path}: {e}", file=sys.stderr)
            continue
        if "is_latest" not in data:
            missing_flag += 1
            continue
        if not data.get("is_latest"):
            continue
        image = data.get("image")
        if not image:
            continue
        uid = data.get("uid")
        if uid is not None and uid not in image_uids.setdefault(image, []):
            image_uids[image].append(uid)
        if image not in seen:
            seen.add(image)
            images.append(image)
    if missing_flag:
        print(
            f"[warn] 有 {missing_flag} 个文件缺少 is_latest 字段（请先运行 mark_latest.py --write），已跳过",
            file=sys.stderr,
        )
    return images, image_uids


def image_exists(image):
    """检测本地是否已存在指定镜像（docker image inspect 返回 0 即存在）"""
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image],
            capture_output=True, text=True, timeout=PULL_TIMEOUT,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def pull_image(image, retry):
    """本地已存在则跳过，否则执行 docker pull；失败时按 retry 次数重试，返回 (image, success, info)"""
    if image_exists(image):
        return image, True, "本地已存在，跳过拉取"
    for attempt in range(1, retry + 2):  # 初始 1 次 + retry 次重试
        try:
            result = subprocess.run(
                ["docker", "pull", image],
                capture_output=True, text=True, timeout=PULL_TIMEOUT,
            )
            if result.returncode == 0:
                return image, True, f"第 {attempt} 次尝试"
            err = (result.stderr or result.stdout).strip()
        except subprocess.TimeoutExpired:
            err = f"超过 {PULL_TIMEOUT}s 超时"
        except OSError as e:
            return image, False, f"执行失败: {e}"
        if attempt <= retry:
            print(f"[retry] {image} 第 {attempt} 次失败，准备重试...", file=sys.stderr)
    return image, False, err


def uid_str(image_uids, image):
    """返回镜像关联的 uid 字符串，如 '1,86'，无 uid 时返回 '-'"""
    uids = image_uids.get(image)
    return ",".join(str(u) for u in uids) if uids else "-"


def main():
    parser = argparse.ArgumentParser(description="读取 json 中的 image 字段并用 docker pull 拉取镜像")
    parser.add_argument("input_dir", help="存放提交 json 文件的目录")
    parser.add_argument("--concurrency", type=int, default=4, help="并发拉取数量（默认 4）")
    parser.add_argument("--retry", type=int, default=1, help="失败后的重试次数（默认 1）")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要拉取的镜像列表，不实际执行")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"[error] 目录不存在: {input_dir}", file=sys.stderr)
        sys.exit(1)

    if shutil.which("docker") is None:
        print("[error] 未找到 docker 命令，请确认 Docker 已安装", file=sys.stderr)
        sys.exit(1)

    images, image_uids = load_images(input_dir)
    if not images:
        print(f"[warn] 目录中没有 json 文件或未找到 image 字段: {input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"共发现 {len(images)} 个唯一镜像:")
    for i, image in enumerate(images, 1):
        print(f"  {i:>3}. {image}")

    if args.dry_run:
        print("[dry-run] 仅打印镜像列表，未执行 docker pull")
        return

    success, failed = [], []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        futures = {executor.submit(pull_image, img, args.retry): img for img in images}
        for future in as_completed(futures):
            image, ok, info = future.result()
            with print_lock:
                if ok:
                    success.append(image)
                    print(f"[成功] {image}（{info}）")
                else:
                    failed.append((image, info))
                    print(f"[失败] {image} (uid={uid_str(image_uids, image)}): {info}", file=sys.stderr)

    print(f"\n完成: 成功 {len(success)} 个，失败 {len(failed)} 个")
    if failed:
        print("失败镜像:")
        for image, err in failed:
            print(f"  - {image} (uid={uid_str(image_uids, image)}): {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
