import os


submissions_id = [
    # R1 Top5
    29, 34, 32, 48, 45,
    # R2 TOP5
    30, 35, 33, 21, 47,

    49, 15, 18, 46, 58,
    16, 50, 19, 41, 57,

    # S1 和 S2
    72, 73, 80, 70, 78, 75, 68, 65, 79, 77, 62, 76, 61, 8, 9,
]

submissions_id = [73,70,78,68,77,62,9]

for id_ in submissions_id:
    print(f'Processing {id_}')
    target_json = f'/mnt/SSD1_P1/CMRx2025-perf/json/{id_}.json'
    target_folder = f'/mnt/SSD1_P1/CMRx2025-perf/json/{id_}.json.workplace'
    if os.path.exists(target_folder):
        continue
    # interpreter = '/SSDHome/home/guanli/CMRxRecon2025-snippets/performance/.venv/bin/python3'
    eval_script = '/SSDHome/home/guanli/CMRxRecon2025-snippets/performance/evaluate.py'
    cmd = f'python3 {eval_script} {target_json}'
    print(cmd)
    os.system(cmd)
