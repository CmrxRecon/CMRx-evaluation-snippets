"""
执行命令 python run.py CMRx2026/test.json <显卡编号0-3> <submission-json> 可以执行测试。

submission json存放在 /app/test_utils/CMRx2026/submission/json 目录下
我现在有4张显卡，测试只允许使用1张显卡，给我测试所有 is_latest=True, type == "Task Regular2" 的提交.


- 每次提交时独占一张显卡
- 按uid顺序对任务进行测试
- 开始测试时打印出正在测试哪个队伍、使用哪张显卡、提交的uid
- 结束时打印出队伍测试消耗的时间和uid和队伍名
- 按下ctrl + c可以退出主程序，但是不要退出已经启动的测试任务
"""

import argparse
import json
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TASK_DESCRIBE = BASE_DIR / "CMRx2026" / "test.json"
DEFAULT_SUBMISSION_DIR = BASE_DIR / "CMRx2026" / "submission" / "json"
DEFAULT_RUN_PY = BASE_DIR / "run.py"
DEFAULT_GPU_IDS = "0"       # 仅使用 1 张显卡用于测试
DEFAULT_DEBUG_GPU = "1,2,3"  # 其余 3 张不参与测试
GPU_MEM_THRESHOLD_MB = 1024  # 显存占用阈值（1GB）
GPU_CHECK_INTERVAL = 5       # 显存检查间隔（秒）

print_lock = threading.Lock()


def get_gpu_memory_used(gpu_id):
    """查询指定 GPU 的显存占用（MB），查询失败返回 -1 并输出原因"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "-i", str(gpu_id)],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            with print_lock:
                print(f"[warn] nvidia-smi 查询 GPU {gpu_id} 失败: {(result.stderr or result.stdout).strip()}",
                      file=sys.stderr)
            return -1
        # 兼容 "2048" / "2048 MiB" 等输出格式，取第一行中的数字
        for line in result.stdout.strip().splitlines():
            match = re.search(r"(\d+(?:\.\d+)?)", line)
            if match:
                return int(float(match.group(1)))
    except (subprocess.TimeoutExpired, OSError) as e:
        with print_lock:
            print(f"[warn] nvidia-smi 查询 GPU {gpu_id} 异常: {e}", file=sys.stderr)
    return -1


def wait_for_gpu_free(gpu_id, stop_event):
    """等待 GPU 显存降到阈值以下，被中断时返回 False；查询失败不放行，持续重试；仅在状态变化时打印日志避免刷屏"""
    notified = False
    while not stop_event.is_set():
        used = get_gpu_memory_used(gpu_id)
        if used == -1:
            if not notified:
                with print_lock:
                    print(f"[等待] GPU {gpu_id} 显存查询失败（nvidia-smi 异常），等待重试...", file=sys.stderr, flush=True)
                notified = True
        elif used < GPU_MEM_THRESHOLD_MB:
            if notified:
                with print_lock:
                    print(f"[等待] GPU {gpu_id} 显存已释放（{used}MB），继续执行", flush=True)
            return True
        else:
            if not notified:
                with print_lock:
                    print(f"[等待] GPU {gpu_id} 显存占用 {used}MB > {GPU_MEM_THRESHOLD_MB}MB，等待释放...", flush=True)
                notified = True
        if stop_event.wait(GPU_CHECK_INTERVAL):
            return False
    return False


def load_submissions(submission_dir):
    """读取目录下所有 json，筛选 is_latest=True 且 type == 'Task Regular2' 的提交"""
    selected = []
    for path in sorted(Path(submission_dir).glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[warn] 跳过无法解析的文件 {path}: {e}", file=sys.stderr)
            continue
        if not data.get("is_latest"):
            continue
        if data.get("type") != "Task Regular2":
            continue
        data["_file"] = str(path)
        selected.append(data)
    selected.sort(key=lambda s: s["uid"])  # 按 uid 顺序测试
    return selected


def run_one(sub, gpu_id, task_describe, run_py):
    """独占指定 GPU 执行 run.py，返回 (sub, gpu_id, returncode, elapsed, log)

    使用 start_new_session=True 使子进程不受主进程组 SIGINT 影响，
    确保 Ctrl+C 退出主程序时不会终止已启动的测试任务。
    """
    with print_lock:
        print(f"[开始] 队伍={sub.get('team_name')} 显卡={gpu_id} uid={sub['uid']}")
    start = time.monotonic()
    cmd = [sys.executable, str(run_py), str(task_describe), gpu_id, sub["_file"]]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            start_new_session=True,
        )
        stdout, stderr = proc.communicate()
        log = (stdout or "") + (stderr or "")
        elapsed = time.monotonic() - start
        return sub, gpu_id, proc.returncode, elapsed, log
    except OSError as e:
        elapsed = time.monotonic() - start
        return sub, gpu_id, -1, elapsed, str(e)


def main():
    parser = argparse.ArgumentParser(description="测试所有 is_latest=True 且 type 为 Task Regular2 的提交")
    parser.add_argument("--task-describe", default=str(DEFAULT_TASK_DESCRIBE),
                        help="任务描述 json（默认 CMRx2026/test.json）")
    parser.add_argument("--submission-dir", default=str(DEFAULT_SUBMISSION_DIR),
                        help="提交 json 目录（默认 CMRx2026/submission/json）")
    parser.add_argument("--run-py", default=str(DEFAULT_RUN_PY), help="run.py 路径")
    parser.add_argument("--gpu-ids", default=DEFAULT_GPU_IDS,
                        help="用于测试的显卡编号，逗号分隔（默认 0，仅用 1 张）")
    parser.add_argument("--debug-gpu", default=DEFAULT_DEBUG_GPU,
                        help="不参与测试的显卡编号（默认 1,2,3）")
    args = parser.parse_args()

    gpu_ids = [g.strip() for g in args.gpu_ids.split(",") if g.strip()]
    if not gpu_ids:
        print("[error] --gpu-ids 不能为空", file=sys.stderr)
        sys.exit(1)

    submissions = load_submissions(args.submission_dir)
    if not submissions:
        print(f"[warn] 没有符合条件的提交（is_latest=True 且 type == 'Task Regular2'）: {args.submission_dir}",
              file=sys.stderr)
        sys.exit(1)

    print(f"测试 GPU: {gpu_ids}（预留 {args.debug_gpu} 用于 debug）")
    print(f"共 {len(submissions)} 个待测提交:")
    for sub in submissions:
        print(f"  uid={sub['uid']:<4} type={sub.get('type'):<15} team={sub.get('team_name')}")

    # Ctrl+C 优雅退出：停止派发新任务，但不终止已启动的子进程（子进程在新会话中）
    stop_event = threading.Event()

    def sigint_handler(sig, frame):
        if not stop_event.is_set():
            print("\n[info] 收到中断信号 (Ctrl+C)，停止派发新任务，等待已启动的任务完成...", file=sys.stderr)
            stop_event.set()

    signal.signal(signal.SIGINT, sigint_handler)

    # 任务队列 + worker 线程模式：每个 GPU 一个 worker，完成一个取下一个（支持中断时停止派发）
    task_queue = queue.Queue()
    for sub in submissions:
        task_queue.put(sub)

    results = []
    result_lock = threading.Lock()

    def worker(gpu_id):
        while True:
            if stop_event.is_set():
                break
            try:
                sub = task_queue.get_nowait()
            except queue.Empty:
                break
            # 提交前检查显存，超过阈值则等待释放
            if not wait_for_gpu_free(gpu_id, stop_event):
                break
            if stop_event.is_set():
                break
            # 执行测试（子进程在新会话中，不受主进程 Ctrl+C 影响）
            result = run_one(sub, gpu_id, args.task_describe, args.run_py)
            s, gid, returncode, elapsed, log = result
            with print_lock:
                if returncode == 0:
                    print(f"[完成] 队伍={s.get('team_name')} 耗时 {elapsed:.1f}s uid={s['uid']} (GPU {gid}) 测试通过")
                else:
                    print(f"[失败] 队伍={s.get('team_name')} 耗时 {elapsed:.1f}s uid={s['uid']} (GPU {gid}) 退出码 {returncode}",
                          file=sys.stderr)
                    print(f"  日志尾部:\n{log[-2000:]}", file=sys.stderr)
            with result_lock:
                results.append(result)
            task_queue.task_done()

    threads = []
    for gpu in gpu_ids:
        t = threading.Thread(target=worker, args=(gpu,), daemon=False)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # 汇总结果（包括被中断跳过的任务）
    success = sum(1 for _, _, rc, _, _ in results if rc == 0)
    failed = len(results) - success
    skipped = len(submissions) - len(results)
    print(f"\n完成: 成功 {success} 个，失败 {failed} 个，跳过 {skipped} 个")
    if failed:
        print("失败提交:")
        for s, gid, rc, elapsed, _ in results:
            if rc != 0:
                print(f"  - 队伍={s.get('team_name')} uid={s['uid']} (GPU {gid}) 耗时 {elapsed:.1f}s: 退出码 {rc}", file=sys.stderr)
    if failed or skipped:
        sys.exit(1)


if __name__ == "__main__":
    main()

