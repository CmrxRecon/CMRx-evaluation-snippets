"""
命令行工具：标记最新提交

使用方式：python mark_latest.py --write <input_dir>

--write: 用于控制是否回写json

example:
python mark_latest.py --write /app/test_utils/CMRx2026/submission/json

- 先读取目录下的所有json文件
- 然后获取所有的唯一组合：(type, team_name)
- 对于每个组合，找到最新的提交，（uid随着时间依次递增）并标记每次提交是否为最新提交
"""

import argparse
import json
import sys
from pathlib import Path


def load_submissions(input_dir):
    """读取目录下所有 json 文件，返回提交记录列表（每条记录附带文件路径）"""
    submissions = []
    for path in sorted(Path(input_dir).glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[warn] 跳过无法解析的文件 {path}: {e}", file=sys.stderr)
            continue
        data["_file"] = str(path)
        submissions.append(data)
    return submissions


def mark_latest(submissions):
    """按 (type, team_name) 分组，每组按 uid 升序（uid 随时间递增），将 uid 最大的记录标记为 is_latest=True"""
    groups = {}
    for sub in submissions:
        key = (sub.get("type"), sub.get("team_name"))
        groups.setdefault(key, []).append(sub)

    for group in groups.values():
        # uid 随着提交时间依次递增，因此 uid 最大即最新提交
        group.sort(key=lambda s: s.get("uid", 0))
        for i, sub in enumerate(group):
            sub["is_latest"] = i == len(group) - 1
    return groups


def print_groups(groups):
    """打印每个 (type, team_name) 组合的提交列表，并标注是否最新"""
    for (type_name, team_name), group in sorted(groups.items()):
        print(f"=== {type_name} / {team_name} (共 {len(group)} 次提交) ===")
        for sub in group:
            flag = "最新" if sub["is_latest"] else "    "
            print(
                f"  [{flag}] uid={sub.get('uid'):<4} "
                f"submit_time={sub.get('submit_time')}  "
                f"final={sub.get('final_submission')}"
            )
        print()


def write_back(groups):
    """将 is_latest 标记写回对应的 json 文件"""
    for group in groups.values():
        for sub in group:
            with open(sub["_file"], "w", encoding="utf-8") as f:
                json.dump({k: v for k, v in sub.items() if not k.startswith("_")},
                          f, ensure_ascii=False, indent=4)


def main():
    parser = argparse.ArgumentParser(description="标记每个 (type, team_name) 组合中的最新提交")
    parser.add_argument("input_dir", help="存放提交 json 文件的目录")
    parser.add_argument("--write", action="store_true", help="将 is_latest 标记写回 json 文件")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"[error] 目录不存在: {input_dir}", file=sys.stderr)
        sys.exit(1)

    submissions = load_submissions(input_dir)
    if not submissions:
        print(f"[warn] 目录中没有 json 文件: {input_dir}", file=sys.stderr)
        sys.exit(1)

    groups = mark_latest(submissions)
    print_groups(groups)

    latest_count = sum(1 for group in groups.values() for sub in group if sub["is_latest"])
    print(f"共 {len(submissions)} 次提交，{len(groups)} 个组合，最新提交 {latest_count} 个")

    if args.write:
        write_back(groups)
        print(f"已将 is_latest 标记写回 {len(submissions)} 个 json 文件")


if __name__ == "__main__":
    main()
