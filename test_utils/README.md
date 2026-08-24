
python MRIx2026-test/evaluate.py --pred_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer --target_dir /mnt/nas/nas4/privateData/rawdata/PanFieldMRI/mrixfields2026/inhouse_test20_20260713/task2/gt --pred_seg_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer_seg/ --target_seg_dir /mnt/nas/nas4/privateData/rawdata/PanFieldMRI/mrixfields2026/inhouse_test20_20260713/task1/gt_seg/ --output_csv /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/score/result.csv --output_json /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/score/result.json


python MRIx2026-test/evaluate.py --pred_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer --target_dir /mnt/nas/nas4/privateData/rawdata/PanFieldMRI/mrixfields2026/inhouse_test20_20260713/task2/gt --pred_seg_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer_seg/ --target_seg_dir /mnt/nas/nas4/privateData/rawdata/PanFieldMRI/mrixfields2026/inhouse_test20_20260713/task1/gt_seg/ --output_csv /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/score/result.csv --output_json /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/score/result.json


python3 test-2026/score.py -i /mnt/HDD1_P1/guanli/CMRx2026/test-phase/2/infer/ -t R1 -s TestSet -g /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_GT -x /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_EMPTY -o /mnt/HDD1_P1/guanli/CMRx2026/test-phase/2/score

python3 test-2026/score.py -i /mnt/HDD1_P1/guanli/CMRx2026/test-phase/4/infer/ -t R1 -s TestSet -g /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_GT -x /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_EMPTY -o /mnt/HDD1_P1/guanli/CMRx2026/test-phase/4/score
