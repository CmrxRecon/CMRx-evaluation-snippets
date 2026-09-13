import json
import os

from competition import SubmissionHandler, ExecutationRequest


class MRIx2026Handler(SubmissionHandler):
    def __init__(self, workplace: str, submission_json: str) -> None:
        super().__init__('MRIx2026', workplace, submission_json)
        self.r = None
        # TODO 自动根据 submission_json 加载

    def score_check(self):
        # self._dedicate_check_score()
        r = ExecutationRequest(self._submission_obj, self.workplace, self.submission_json)
        resuslt_path = r.rel_path('score/Result/results.json')
        results = json.loads(open(resuslt_path).read())
        self._dedicate_check_score()
        return results

    def _dedicate_check_score(self):
        """
        预处理动作
        for i in `seq 1 130`;do echo Checking $i;python3 run_debug.py --action=check_score MRIx2026/test.json 0 MRIx2026/submissions/$i.json; done
        """

        r = ExecutationRequest(self._submission_obj, self.workplace, self.submission_json)
        submission = self._submission_obj

        resuslt_path = r.rel_path('score/Result/results.json')
        results = json.loads(open(resuslt_path).read())

        Num_Files = results.get('Num_Files', None)
        primary_score = results.get('primary_score', None)
        if r.type in ['Task1', 'Task2']:
            assert Num_Files == '60/60'
            assert primary_score is not None

            # 检查 Avg_T1W_Dice_adj
            t1w_dice = results.get('Avg_T1W_Dice_adj', None)
            if t1w_dice is not None and t1w_dice < 0.68:
                print(f"----- {r.uid}--{r.is_latest} {resuslt_path} ------")
                print(f"----- {self.submission_json} {submission.get('comment')} ------")
                print(r.email)
                print(f'MRIx2026 test phase submission {r.uid} feedback')
                print(f"Hi {r.team_name},\n")
                print(f"Your score metric `'Avg_T1W_Dice_adj': {results['Avg_T1W_Dice_adj']}` is abnormal. This is most likely caused by a coordinate system issue. Please fix it and resubmit as soon as possible.")
                print(submission)
                print("-----------\n\n")
                return False
        elif r.type == 'Task3':
            assert Num_Files == '120/120'
            assert primary_score is not None
        else:
            raise NotImplemented
        return True
