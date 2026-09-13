"""
读取 {result_path}/{uid}/score/Result/summary_{task_type}.csv,

- 遍历json_path，找到所有与task_type匹配的json文件，且只读取is_latest=True的json文件
- 根据json中的uid找到目录下的csv文件，第一行为表头，第一列为key，第二列为value。
- 将csv其读为dict，每个dict以uid为key
- 其中：task_type 通过命令行指定: 有R1、R2、S1、S2

使用方式：python test_gather_scores_CMRx2026-R1S1S2.py <R1|R2|S1|S2> [--result-path DIR] [--json-path DIR] [--output FILE]

example:
python test_gather_scores_CMRx2026-R1S1S2.py R1
python test_gather_scores_CMRx2026-R1S1S2.py S2 --output scores_S2.json

task_type 与 json 中 type 字段的映射: R1->Task Regular1, R2->Task Regular2, S1->Task Special1, S2->Task Special2

"""

import argparse
import csv
import json
import sys
from pathlib import Path

DEFAULT_RESULT_PATH = Path("/app/test_utils/CMRx2026/test-phase")
DEFAULT_JSON_PATH = Path("/app/test_utils/CMRx2026/submission/json")

# task_type 命令行参数 -> json 中的 type 字段
TASK_TYPE_MAP = {
    "R1": "Task Regular1",
    "R2": "Task Regular2",
    "S1": "Task Special1",
    "S2": "Task Special2",
}

# R1/S1/S2 排名指标：(指标名, 是否升序)，升序表示值越小排名越靠前
RANK_METRICS = [("SSIM_adj", False), ("nRMSE_adj", True), ("RelErr_adj", True), ("AngErr_adj", True)]


def load_latest_submissions(json_path, task_type):
    """遍历 json 目录，筛选 is_latest=True 且 type 与 task_type 匹配的提交

    返回按 uid 升序的 (uid, team_name, email) 列表
    """
    expected_type = TASK_TYPE_MAP[task_type]
    selected = []
    for path in sorted(Path(json_path).glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[warn] 跳过无法解析的文件 {path}: {e}", file=sys.stderr)
            continue
        if not data.get("is_latest"):
            continue
        if data.get("type") != expected_type:
            continue
        uid = data.get("uid")
        if uid is None:
            print(f"[warn] json 缺少 uid 字段: {path}", file=sys.stderr)
            continue
        selected.append((uid, data.get("team_name", ""), data.get("email", "")))
    selected.sort(key=lambda x: x[0])
    return selected


def read_summary_csv(csv_path):
    """读取 summary csv：第一行为表头，第一列为 key，第二列为 value，返回 dict

    跳过空行和不足两列的行，key 与 value 去除首尾空白
    """
    result = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳过表头行
        for row in reader:
            if len(row) < 2:
                continue
            key, value = row[0].strip(), row[1].strip()
            if not key:
                continue
            result[key] = value
    return result


def rank_R1_S12(scores, team_map=None, email_map=None):
    """对 scores（uid -> {key: value}）进行指标排名

    - SSIM_adj 降序（越大越好），nRMSE_adj、RelErr_adj、AngErr_adj 升序（越小越好）
    - 各指标排名位次即积分（第 1 名得 1 分），总分 = 各指标积分之和，总分越低排名越靠前
    - 并列时名次相同（1,2,2,4 排法）；缺失某指标的提交不参与该指标排名（该指标积分为 '-'，不计入总分）
    - team_map 为 uid -> 队伍名称 的映射，email_map 为 uid -> 邮箱 的映射（缺省时对应列显示 '-'）
    返回按总分升序的 dict: uid -> {"ranks": {指标: 名次}, "total": 总分, "final_rank": 总分/指标数}，并在内部打印排名表
    - 排名表需要uid、Rank、Team Name、SSIM_adj、SSIM_adj Rank、nRMSE_adj、nRMSE_adj Rank、
      RelErr_adj、RelErr_adj Rank、AngErr_adj、AngErr_adj Rank和Final Rank（各指标Rank加起来除以4）、email
    """
    # (指标名, 是否升序)：升序表示值越小排名越靠前
    metrics = RANK_METRICS
    ranked = {uid: {"ranks": {}} for uid in scores}
    team_map = team_map or {}
    email_map = email_map or {}

    for metric, ascending in metrics:
        # 仅收集该指标可解析为数值的提交
        valid = []
        for uid, metrics_dict in scores.items():
            try:
                value = float(metrics_dict[metric])
            except (KeyError, TypeError, ValueError):
                continue
            valid.append((uid, value))
        valid.sort(key=lambda x: x[1], reverse=not ascending)
        # 排名：相同数值并列同名次，后续名次跳过（1,2,2,4 排法）
        prev_value, prev_rank = None, 0
        for i, (uid, value) in enumerate(valid, 1):
            if prev_value is not None and value == prev_value:
                rank = prev_rank
            else:
                prev_rank = rank = i
            prev_value = value
            ranked[uid]["ranks"][metric] = rank

    # 总分 = 各指标积分之和；全部指标缺失时为 None（排最后）
    # Final Rank = 总分 / 指标数（4），缺失指标不计入总分
    for uid in ranked:
        total = sum(ranked[uid]["ranks"].values()) or None
        ranked[uid]["total"] = total
        ranked[uid]["final_rank"] = total / len(metrics) if total is not None else None
    ordered = dict(sorted(ranked.items(), key=lambda kv: (kv[1]["total"] is None, kv[1]["total"])))

    # 打印排名表：Rank、uid、Team Name、各指标数值与 Rank、Final Rank、email
    metric_names = [m for m, _ in metrics]
    rank_col_names = [f"{m} Rank" for m in metric_names]
    team_width = max([len("team")] + [len(str(team_map.get(uid, ""))) for uid in scores] + [1]) + 1
    team_width = min(team_width, 30)  # 队伍名称过长时截断
    email_width = max([len("email")] + [len(str(email_map.get(uid, ""))) for uid in scores] + [1]) + 1
    email_width = min(email_width, 48)  # 邮箱过长时截断
    value_width = max(len(m) for m in metric_names) + 2  # 指标数值列宽
    rank_width = max(len(n) for n in rank_col_names) + 1  # 指标 Rank 列宽
    final_width = len("Final Rank") + 1

    print(f"\n指标排名（名次即积分，Final Rank = 各指标 Rank 之和 / {len(metrics)}，'-' 表示该指标缺失）:")
    header = (f"{'Rank':>5} {'uid':>5} {'team':<{team_width}}"
              + "".join(f"{m:>{value_width}}{n:>{rank_width}}" for m, n in zip(metric_names, rank_col_names))
              + f"{'Final Rank':>{final_width}} {'email':<{email_width}}")
    print(header)
    print("-" * len(header))
    for i, (uid, info) in enumerate(ordered.items(), 1):
        team = str(team_map.get(uid, "")) or "-"
        if len(team) > team_width:
            team = team[:team_width - 1] + "…"
        email = str(email_map.get(uid, "")) or "-"
        if len(email) > email_width:
            email = email[:email_width - 1] + "…"
        row = f"{i:>5} {uid:>5} {team:<{team_width}}"
        for m in metric_names:
            value = scores[uid].get(m, "-")
            rank = info["ranks"].get(m)
            row += f"{str(value):>{value_width}}{str(rank) if rank is not None else '-':>{rank_width}}"
        final_rank = info["final_rank"]
        row += f"{f'{final_rank:.2f}' if final_rank is not None else '-':>{final_width}} {email:<{email_width}}"
        print(row)
    return ordered


def write_rank_to_xlsx(ranked, scores, team_map=None, email_map=None, output_path="ranking.xlsx", task_type=""):
    """将排名结果写入 xlsx 文件

    - 表头：Rank、uid、Team Name、各指标数值与 Rank、Final Rank、email，行序与排名一致（总分升序）
    - 指标数值可解析为 float 时写入数值，否则写入 '-'；Final Rank 保留 2 位小数
    """
    from openpyxl import Workbook

    team_map = team_map or {}
    email_map = email_map or {}
    metric_names = [m for m, _ in RANK_METRICS]

    wb = Workbook()
    ws = wb.active
    ws.title = f"Ranking_{task_type}" if task_type else "Ranking"
    header = ["Rank", "uid", "Team Name"]
    for m in metric_names:
        header += [m, f"{m} Rank"]
    header += ["Final Rank", "email"]
    ws.append(header)

    for i, (uid, info) in enumerate(ranked.items(), 1):
        metrics_dict = scores[uid]
        row = [i, uid, team_map.get(uid, "-")]
        for m in metric_names:
            try:
                value = float(metrics_dict.get(m))
            except (TypeError, ValueError):
                value = "-"
            row += [value, info["ranks"].get(m, "-")]
        final_rank = info["final_rank"]
        row += [round(final_rank, 2) if final_rank is not None else "-", email_map.get(uid, "-")]
        ws.append(row)

    wb.save(output_path)
    print(f"\n排名结果已写入: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="收集各最新提交的评分 summary csv，汇总为 uid -> 分数 dict")
    parser.add_argument("task_type", choices=sorted(TASK_TYPE_MAP), help="任务类型: R1/R2/S1/S2")
    parser.add_argument("--result-path", default=str(DEFAULT_RESULT_PATH),
                        help=f"测试结果根目录（默认 {DEFAULT_RESULT_PATH}）")
    parser.add_argument("--json-path", default=str(DEFAULT_JSON_PATH),
                        help=f"提交 json 目录（默认 {DEFAULT_JSON_PATH}）")
    parser.add_argument("--output", default=None, help="将汇总结果写入 json 文件（默认仅打印表格）")
    parser.add_argument("--output-xlsx", default=None,
                        help="排名结果写入的 xlsx 路径（默认 ranking_{task_type}.xlsx，仅 R1/S1/S2）")
    args = parser.parse_args()

    task_type = args.task_type.upper()
    expected_type = TASK_TYPE_MAP[task_type]

    selected = load_latest_submissions(args.json_path, task_type)
    if not selected:
        print(f"[warn] 没有 is_latest=True 且 type={expected_type} 的提交: {args.json_path}", file=sys.stderr)
        sys.exit(1)

    print(f"task_type={task_type}（type={expected_type}），共 {len(selected)} 个最新提交")

    scores = {}
    missing = []
    for uid, team, _ in selected:
        csv_path = Path(args.result_path) / str(uid) / "score" / "Result" / f"summary_{task_type}.csv"
        if not csv_path.is_file():
            missing.append((uid, team))
            print(f"[warn] 缺少评分文件: {csv_path}（uid={uid}, team={team}）", file=sys.stderr)
            continue
        try:
            scores[uid] = read_summary_csv(csv_path)
        except OSError as e:
            missing.append((uid, team))
            print(f"[warn] 读取评分文件失败: {csv_path}（uid={uid}）: {e}", file=sys.stderr)

    if not scores:
        print(f"[error] 没有任何评分文件可读取，请确认测试已完成: {args.result_path}", file=sys.stderr)
        sys.exit(1)

    # R2 为流场任务，指标构成不同，不参与 R1/S1/S2 的排名（函数内部打印排名表）
    if task_type != "R2":
        ranked = rank_R1_S12(scores,
                             {uid: team for uid, team, _ in selected},
                             {uid: email for uid, _, email in selected})
        # 将排名结果写入 xlsx 文件
        write_rank_to_xlsx(ranked, scores,
                           {uid: team for uid, team, _ in selected},
                           {uid: email for uid, _, email in selected},
                           args.output_xlsx or f"ranking_{task_type}.xlsx",
                           task_type)

    # 打印汇总表格：行为 uid，列为各评分指标（取所有 uid 的 key 并集）
    keys = []
    for metrics in scores.values():
        for key in metrics:
            if key not in keys:
                keys.append(key)
    width = max([len("uid")] + [len(str(uid)) for uid in scores]) + 1
    print(f"\n汇总 {len(scores)} 个提交的评分（缺失评分文件 {len(missing)} 个，'-' 表示无此指标）:")
    header = f"{'uid':<{width}}" + "".join(f"{key:>18}" for key in keys)
    print(header)
    print("-" * len(header))
    team_map = {uid: team for uid, team, _ in selected}
    for uid in sorted(scores):
        metrics = scores[uid]
        row = f"{uid:<{width}}"
        for key in keys:
            value = metrics.get(key, "-")
            row += f"{value:>18}"
        print(row)

    # 汇总缺失情况
    if missing:
        print(f"\n缺失评分文件的提交（{len(missing)} 个）:", file=sys.stderr)
        for uid, team in missing:
            print(f"  - uid={uid}, team={team}", file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
        print(f"\n已写入: {args.output}")


if __name__ == "__main__":
    main()
