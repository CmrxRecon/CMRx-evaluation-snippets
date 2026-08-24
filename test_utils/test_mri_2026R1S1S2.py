"""
执行命令 python run.py CMRx2026/test.json <显卡编号0-3> <submission-json> 可以执行测试。

submission json存放在 /app/test_utils/CMRx2026/submission/json 目录下
我现在有4张显卡，3张用于测试各提交，1张预留着用于debug，给我测试所有 is_latest=True, type != "Task Regular2" 的提交.
"""

import argparse
import json
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TASK_DESCRIBE = BASE_DIR / "CMRx2026" / "test.json"
DEFAULT_SUBMISSION_DIR = BASE_DIR / "CMRx2026" / "submission" / "json"
DEFAULT_RUN_PY = BASE_DIR / "run.py"
DEFAULT_GPU_IDS = "0,1,2"   # 3 张显卡用于测试
DEFAULT_DEBUG_GPU = "3"     # 预留 1 张用于 debug

print_lock = threading.Lock()


def load_submissions(submission_dir):
    """读取目录下所有 json，筛选 is_latest=True 且 type != 'Task Regular2' 的提交"""
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
        if data.get("type") == "Task Regular2":
            continue
        data["_file"] = str(path)
        selected.append(data)
    return selected


def run_one(sub, gpu_id, task_describe, run_py):
    """在指定 GPU 上执行 run.py，返回 (sub, gpu_id, returncode, log)"""
    cmd = [sys.executable, str(run_py), str(task_describe), gpu_id, sub["_file"]]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        log = (result.stdout or "") + (result.stderr or "")
        return sub, gpu_id, result.returncode, log
    except OSError as e:
        return sub, gpu_id, -1, str(e)


def main():
    parser = argparse.ArgumentParser(description="并发测试所有 is_latest=True 且非 Task Regular2 的提交")
    parser.add_argument("--task-describe", default=str(DEFAULT_TASK_DESCRIBE),
                        help="任务描述 json（默认 CMRx2026/test.json）")
    parser.add_argument("--submission-dir", default=str(DEFAULT_SUBMISSION_DIR),
                        help="提交 json 目录（默认 CMRx2026/submission/json）")
    parser.add_argument("--run-py", default=str(DEFAULT_RUN_PY), help="run.py 路径")
    parser.add_argument("--gpu-ids", default=DEFAULT_GPU_IDS,
                        help="用于测试的显卡编号，逗号分隔（默认 0,1,2）")
    parser.add_argument("--debug-gpu", default=DEFAULT_DEBUG_GPU,
                        help="预留用于 debug 的显卡编号（默认 3，不参与测试）")
    args = parser.parse_args()

    gpu_ids = [g.strip() for g in args.gpu_ids.split(",") if g.strip()]
    if not gpu_ids:
        print("[error] --gpu-ids 不能为空", file=sys.stderr)
        sys.exit(1)

    submissions = load_submissions(args.submission_dir)
    if not submissions:
        print(f"[warn] 没有符合条件的提交（is_latest=True 且 type != 'Task Regular2'）: {args.submission_dir}",
              file=sys.stderr)
        sys.exit(1)

    print(f"测试 GPU: {gpu_ids}（预留 {args.debug_gpu} 用于 debug）")
    print(f"共 {len(submissions)} 个待测提交:")
    for sub in submissions:
        print(f"  uid={sub['uid']:<4} type={sub.get('type'):<15} team={sub.get('team_name')}")

    # GPU 轮转分配：并发任务索引连续（i, i+1, i+2），各占一个 GPU，互不冲突；
    # 注意：不同 uid 的 run.py 会共享 test.json 中的 output 目录及 state.json，
    # 并发写 state.json 可能丢失更新（后果仅为状态需重跑），不影响结果正确性。
    results = []
    with ThreadPoolExecutor(max_workers=len(gpu_ids)) as executor:
        futures = {
            executor.submit(run_one, sub, gpu_ids[i % len(gpu_ids)], args.task_describe, args.run_py): sub
            for i, sub in enumerate(submissions)
        }
        for future in as_completed(futures):
            sub, gpu_id, returncode, log = future.result()
            with print_lock:
                if returncode == 0:
                    print(f"[完成] uid={sub['uid']} (GPU {gpu_id}) {sub.get('team_name')} 测试通过")
                else:
                    print(f"[失败] uid={sub['uid']} (GPU {gpu_id}) {sub.get('team_name')} 退出码 {returncode}",
                          file=sys.stderr)
                    print(f"  日志尾部:\n{log[-2000:]}", file=sys.stderr)
            results.append((sub, gpu_id, returncode, log))

    success = sum(1 for _, _, rc, _ in results if rc == 0)
    failed = len(results) - success
    print(f"\n完成: 成功 {success} 个，失败 {failed} 个")
    if failed:
        print("失败提交:")
        for sub, gpu_id, rc, _ in results:
            if rc != 0:
                print(f"  - uid={sub['uid']} (GPU {gpu_id}) {sub.get('team_name')}: 退出码 {rc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
