#!/usr/bin/env python3
"""使用问卷星开放平台 ApiKey 下载指定问卷的答卷数据（按文本，导出为 xlsx）。

用法:
  python3 export_wjx_responses.py <vid> <输出路径>   # 下载指定问卷（xlsx）
  python3 export_wjx_responses.py --list             # 列出账号下全部问卷

- 问卷列表:   action=1000002 (LIST_SURVEYS)
- 下载答卷:   action=1001004 (DOWNLOAD_RESPONSES), query_type=0 按文本, suffix=0 CSV
- 鉴权:       Authorization: Bearer <ApiKey>
- 说明:       API 只提供 CSV，脚本下载后转换为 xlsx
"""
import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.request

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_fetch_from_wjx import key  # noqa: E402

API_URL = "https://www.wjx.cn/openapi/default.aspx"

LIST_SURVEYS = "1000002"
DOWNLOAD_RESPONSES = "1001004"
PAGE_SIZE = 10


def call_api(action: str, params: dict, timeout: int = 180) -> dict:
    """调用问卷星开放接口，返回解析后的 JSON。"""
    body = {"action": action, **params}
    req = urllib.request.Request(
        API_URL + f"?traceid={int(time.time() * 1000)}&action={action}",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data.get("result"):
        raise RuntimeError(f"action={action} 失败: {data.get('errormsg')}")
    return data


def list_all_surveys() -> list[dict]:
    """分页获取账号下全部问卷。"""
    surveys = []
    page = 1
    while True:
        data = call_api(LIST_SURVEYS, {"page_index": page, "page_size": PAGE_SIZE})
        items = list(data["data"]["activitys"].values())
        surveys.extend(items)
        total = data["data"]["total_count"]
        if page * PAGE_SIZE >= total:
            break
        page += 1
        time.sleep(0.3)
    return surveys


def safe_filename(title: str) -> str:
    """清理标题中的非法文件名字符。"""
    title = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", title).strip()
    return title[:60] or "untitled"


def download_file(url: str, filepath: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as resp, open(filepath, "wb") as f:
        f.write(resp.read())


def download_as_xlsx(url: str, xlsx_path: str) -> None:
    """下载 CSV 答卷数据并转换为 xlsx（保持文本内容不变）。"""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        download_file(url, tmp_path)
        df = pd.read_csv(tmp_path, encoding="utf-8-sig", dtype=str)
        df.to_excel(xlsx_path, index=False)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="下载指定问卷的答卷数据（按文本，导出为 xlsx）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python3 export_wjx_responses.py 371015584 /path/to/result.xlsx\n"
            "  python3 export_wjx_responses.py 371015584 /path/to/dir/   # 目录则自动命名\n"
            "  python3 export_wjx_responses.py --list                    # 列出全部问卷 id"
        ),
    )
    parser.add_argument("vid", type=int, nargs="?", help="问卷 ID")
    parser.add_argument("output", type=str, nargs="?", help="保存路径（文件或目录）")
    parser.add_argument("--list", action="store_true", help="仅列出账号下全部问卷，不下载")
    args = parser.parse_args()

    if args.list:
        for s in list_all_surveys():
            print(f"{s['vid']}\t{s['title']}\t答卷数:{s['answer_total']}")
        return

    if args.vid is None or args.output is None:
        parser.error("需要提供 vid 和输出路径（或用 --list 查看问卷列表）")

    # 输出路径为目录时自动命名为 <vid>_<title>.xlsx；文件路径统一为 .xlsx 后缀
    output = args.output
    if os.path.isdir(output) or output.endswith(os.sep):
        os.makedirs(output, exist_ok=True)
        title = next(
            (s["title"] for s in list_all_surveys() if s["vid"] == args.vid),
            str(args.vid),
        )
        output = os.path.join(output, f"{args.vid}_{safe_filename(title)}.xlsx")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
        if output.lower().endswith(".csv"):
            output = output[:-4] + ".xlsx"
        elif not output.lower().endswith(".xlsx"):
            output += ".xlsx"

    data = call_api(
        DOWNLOAD_RESPONSES,
        {"vid": args.vid, "query_type": 0, "suffix": 0},
    )["data"]
    url = data.get("download_url")
    if not url:
        # 异步任务：需要轮询 taskid
        taskid = data.get("taskid")
        if taskid:
            raise RuntimeError(f"返回异步任务 taskid={taskid}，脚本暂不支持轮询")
        raise RuntimeError("未返回 download_url")

    download_as_xlsx(url, output)
    size_kb = os.path.getsize(output) / 1024
    print(f"下载完成: {output} （{size_kb:.1f} KB，{data.get('join_times', '?')} 份答卷）")


if __name__ == "__main__":
    main()
