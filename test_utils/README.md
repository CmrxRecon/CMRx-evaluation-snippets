## MRIx2026 分割示例
/app/MRIx2026-test/README.md

## MRIx2026 打分示例
代码 https://github.com/MRIxFields/MRIxFields2026/blob/main/Evaluation/evaluate.py

python MRIx2026-test/evaluate.py --pred_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer \n
--target_dir /mnt/nas/nas4/privateData/rawdata/PanFieldMRI/mrixfields2026/inhouse_test20_20260713/task2/gt \n
--pred_seg_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer_seg/ \n
--target_seg_dir /mnt/nas/nas4/privateData/rawdata/PanFieldMRI/mrixfields2026/inhouse_test20_20260713/task1/gt_seg/ \n
--output_csv /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/score/result.csv \n
--output_json /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/score/result.json


python MRIx2026-test/evaluate.py --pred_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer --target_dir /mnt/nas/nas4/privateData/rawdata/PanFieldMRI/mrixfields2026/inhouse_test20_20260713/task2/gt --pred_seg_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer_seg/ --target_seg_dir /mnt/nas/nas4/privateData/rawdata/PanFieldMRI/mrixfields2026/inhouse_test20_20260713/task1/gt_seg/ --output_csv /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/score/result.csv --output_json /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/score/result.json

uid=18;python3 /app/MRIx2026-test/score.py --input=/app/test_utils/MRIx2026/MRIx-test-phase/${uid}/infer/ --task=task3 --pack_root=/mnt/SSD1_P1/MRIx2026/inhouse_test20_20260713 --output=/app/test_utils/MRIx2026/MRIx-test-phase/${uid}/score 

## CMRx2026 打分示例
python3 test-2026/score.py -i /mnt/HDD1_P1/guanli/CMRx2026/test-phase/2/infer/ -t R1 -s TestSet -g /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_GT -x /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_EMPTY -o /mnt/HDD1_P1/guanli/CMRx2026/test-phase/2/score

python3 test-2026/score.py -i /mnt/HDD1_P1/guanli/CMRx2026/test-phase/4/infer/ -t R1 -s TestSet -g /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_GT -x /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_EMPTY -o /mnt/HDD1_P1/guanli/CMRx2026/test-phase/4/score


## CMRx2026 排名汇集
python3 test_gather_scores_CMRx2026-R1S1S2.py --json-path /app/test_utils/CMRx2026/submissions S1

## CMRx2026 排名
task_type=S1（type=Task Special1），共 13 个最新提交

指标排名（数值(名次)，名次即积分，总分越低越靠前，'-' 表示该指标缺失）:
  排名   uid team                               SSIM_adj         nRMSE_adj        RelErr_adj        AngErr_adj  total
-------------------------------------------------------------------------------------------------------------------
   1    78 CMRx4DFlow-mi2rl_jhooons        0.980014(1)       0.029109(1)       0.227153(1)      16.009449(1)      4
   2    72 shama                            0.97512(2)       0.032644(2)       0.269773(2)      19.062522(3)      9
   3    48 MadeForLife                     0.973958(3)       0.033413(3)       0.299546(4)      19.244483(4)     14
   4    43 FeelFlows                       0.971631(4)       0.036295(4)       0.291196(3)       21.69368(6)     17
   5    95 ReconMcReconface                0.970473(5)       0.037373(5)       0.304863(5)      17.481257(2)     17
   6    20 RosettaFlow                     0.946602(8)       0.056569(8)        0.33445(6)      20.608711(5)     27
   7    28 MRAR                            0.956216(6)       0.049862(6)       0.418498(8)      24.007639(8)     28
   8    66 ETH                             0.952841(7)       0.052542(7)       0.356519(7)      22.878637(7)     28
   9    68 gameking                       0.934709(10)      0.069972(10)       0.472443(9)       29.40655(9)     38
  10    76 UCSF                             0.93754(9)       0.064859(9)      0.575812(12)     37.620381(12)     42
  11    79 NU CVMRI Group                 0.932812(11)      0.070017(11)      0.538887(11)     33.688323(10)     43
  12    38 GenMI-Star                      0.92645(12)      0.070828(12)      0.511344(10)     34.344977(11)     45
  13    54 MedMinion                      0.771504(13)       0.14615(13)      0.731073(13)      50.89178(13)     52


task_type=S2（type=Task Special2），共 13 个最新提交

指标排名（数值(名次)，名次即积分，总分越低越靠前，'-' 表示该指标缺失）:
  排名   uid team                               SSIM_adj         nRMSE_adj        RelErr_adj        AngErr_adj  total
-------------------------------------------------------------------------------------------------------------------
   1    87 CMRx4DFlow-mi2rl_jhooons        0.990543(1)       0.025154(1)       0.254024(1)      21.905005(1)      4
   2    49 MadeForLife                     0.989871(2)       0.025913(2)       0.259892(2)      22.905369(2)      8
   3    96 ReconMcReconface                0.984592(5)       0.034231(5)       0.295536(3)      23.750449(3)     16
   4    67 ETH                             0.986212(4)       0.033248(4)        0.31739(5)      25.609691(4)     17
   5    44 FeelFlows                       0.987955(3)       0.029356(3)       0.327599(6)      28.757222(7)     19
   6    73 shama                           0.984176(6)       0.036177(6)       0.307397(4)      25.904682(5)     21
   7    21 RosettaFlow                    0.968625(10)       0.048888(9)       0.361897(7)      28.211245(6)     32
   8    70 NU CVMRI Group                  0.970485(8)       0.046576(8)       0.386039(8)      30.557611(9)     33
   9    69 gameking                        0.969131(9)      0.049557(10)        0.38876(9)      30.393094(8)     36
  10    77 UCSF                            0.976949(7)       0.043587(7)      0.443412(12)     35.197942(12)     38
  11    39 GenMI-Star                     0.961666(12)      0.054336(12)      0.417344(10)     33.780217(10)     44
  12    91 MRAR                           0.966584(11)      0.051571(11)      0.432866(11)     33.784503(11)     44
  13    55 MedMinion                      0.850301(13)      0.117537(13)      0.767133(13)     45.525413(13)     52


task_type=R1（type=Task Regular1），共 20 个最新提交

指标排名（数值(名次)，名次即积分，总分越低越靠前，'-' 表示该指标缺失）:
  排名   uid team                               SSIM_adj         nRMSE_adj        RelErr_adj        AngErr_adj  total
-------------------------------------------------------------------------------------------------------------------
   1    56 CMRx4DFlow-mi2rl_jhooons        0.974236(2)       0.025072(2)       0.186777(1)      18.659129(1)      6
   2    74 MadeForLife                     0.976658(1)       0.025004(1)       0.216634(2)      20.263492(2)      6
   3    35 FeelFlows                       0.973579(3)       0.026582(3)       0.230995(3)      22.900588(6)     15
   4    94 MRAR                             0.96638(4)       0.032381(4)        0.24332(4)      22.386573(5)     17
   5    71 shama                           0.962003(6)       0.032489(5)       0.259021(7)      21.263325(3)     21
   6    18 RosettaFlow                     0.961175(7)       0.035432(8)       0.252862(6)      22.913319(7)     28
   7    58 imispl                          0.964734(5)       0.032783(6)       0.262194(8)      23.819941(9)     28
   8    30 ReconMcReconface               0.953495(11)      0.036669(10)       0.244749(5)      21.593781(4)     30
   9    82 JiannanXiao                      0.95905(9)       0.034123(7)       0.269143(9)      23.276142(8)     33
  10    41 UTORecon                        0.959744(8)       0.035583(9)      0.345299(11)     26.955593(10)     38
  11    75 UCSF                           0.956807(10)      0.039289(11)       0.34232(10)     30.541828(11)     42
  12    64 ETH                            0.937473(12)      0.047732(12)      0.395731(12)      32.25013(12)     48
  13     4 GenMI-Star                     0.925623(13)      0.056172(14)      0.453131(13)     34.699814(14)     54
  14     8 hias                            0.92251(14)      0.055577(13)      0.572941(16)     39.883815(17)     60
  15    81 NU CVMRI Group                 0.916017(15)      0.058085(15)       0.66599(19)     39.249868(15)     64
  16    16 ZhouQianya                     0.861737(19)      0.091239(19)      0.503579(14)     34.644044(13)     65
  17   102 BISPL2026                      0.891075(18)      0.080177(18)       0.50428(15)     39.694571(16)     67
  18     2 AmsterdamUMC                   0.910409(16)       0.06639(17)      0.634774(17)     44.075133(19)     69
  19    53 MedMinion                      0.909284(17)      0.065199(16)      0.657615(18)     43.779396(18)     69
  20    98 PsiSpace                       0.820774(20)      0.106333(20)      0.935156(20)     46.211316(20)     80



  