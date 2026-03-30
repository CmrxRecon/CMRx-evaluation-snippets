import json
import os
import pandas as pd

def xlsx_to_json(file_path):
    # 读取xlsx文件
    df = pd.read_excel(file_path, engine='openpyxl')
    # json_data = df.to_json(orient='records')
    json_data = df.to_dict(orient='records')
    parsed_data = []
    for r in json_data:
        d = {
            "uid": r['序号'],
            "team_name": r["1、Team Name"],
            "email": r["2、Email"],
            "type": r['3、Task Type'],
            "image": r['4、Docker image address'],
            "synapse_address": r['5、Your synapse project address'],
            "final_submission": r['6、Final submission?'],
            "submit_time": r['提交答卷时间']
        }
        parsed_data.append(d)
    return parsed_data

if __name__ == '__main__':
    xlsx_path = '/home/guanli/CMRxRecon2024-snippets/test-2024/test-data/275666388_按文本_CMRxRecon2024 Test phase submission_15_8.xlsx'
    xlsx_path = '/home/guanli/CMRxRecon2024-snippets/test-2024/test-data/275666388_按文本_CMRxRecon2024 Test phase submission_18_11.xlsx'
    xlsx_path = 'debug.xlsx'
    xlsx_path = '/app/test-2025/320438668_按文本_CMRxRecon2025 Test phase submission_9_9.xlsx'
    import sys
    xlsx_path = sys.argv[1]
    json_dir = 'test-data/json'
    for i in xlsx_to_json(xlsx_path):
        print(i)
        json_name = f'{i["uid"]}.json'
        full_path = os.path.join(json_dir, json_name)
        if os.path.exists(full_path):
            continue
        with open(full_path, 'w') as f:
            json.dump(i, f, ensure_ascii=False, indent=4)
