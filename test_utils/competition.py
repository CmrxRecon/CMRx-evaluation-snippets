import json
import os


class ExecutationRequest:
    def __init__(self, request: dict, workplace: os.PathLike = None, 
                 submission_file: os.PathLike = None) -> None:
        self.workplace = ''
        self._data = request
        r = request
        self.uid = r['uid']
        self.type = r['type']
        self.image = r['image']
        self.team_name = r['team_name']
        self.email = r['email']
        self.synapse_address = r['synapse_address']
        self.is_latest = r.get('is_latest')

        self.workplace = workplace
        self.submission_file = submission_file

    def json(self):
        return self._data

    @property
    def output_path(self):
        return os.path.join(self.workplace, 'infer')

    @property
    def infer_path(self):
        return os.path.join(self.workplace, 'infer')

    @property
    def score_path(self):
        return os.path.join(self.workplace, 'score')

    def rel_path(self, p: str):
        return os.path.join(self.workplace, p)



class SubmissionHandler:
    def __init__(self, competition_name: str, workplace: str, submission_json: str) -> None:
        self.competition_name = competition_name
        self.submission_json = submission_json

        self.workplace = workplace
        with open(submission_json, 'r') as f:
            self._submission_obj = json.load(f)

    def score_check(self):
        with open(self.submission_json, 'r') as f:
            sub_dict = json.load(f)
            r = ExecutationRequest(sub_dict, self.workplace, self.submission_json)
        resuslt_path = r.rel_path('score/Result/results.json')
        assert os.path.exists(resuslt_path)
        self._dedicate_check_score()

        results = json.loads(open(resuslt_path).read())
        return results

    def _dedicate_check_score(self):
        # 强制对打分结果做更多检查
        raise NotImplementedError

    @staticmethod
    def get_all_submissions(submission_dir: os.PathLike, workplace_dir: os.PathLike) -> list[ExecutationRequest]:
        submissions = []
        files = os.listdir(submission_dir)
        files.sort(key=lambda x: int(x[:-5]))
        for i in files:
            submission_file = os.path.join(submission_dir, i)
            submission_workplace = os.path.join(workplace_dir, i[:-5])
            with open(submission_file, 'r') as f:
                sub_obj = json.load(f)
                r = ExecutationRequest(sub_obj, submission_workplace, submission_file)
                submissions.append(r)
        return submissions
