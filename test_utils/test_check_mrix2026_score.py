import json
from mrix2026 import MRIx2026Handler

submissions = MRIx2026Handler.get_all_submissions(
    '/app/test_utils/MRIx2026/submissions',
    '/app/test_utils/MRIx2026/MRIx-test-phase'
)
with open('/app/test_utils/MRIx2026/state.json') as f:
    state_obj = json.load(f)
for s in submissions:
    state = state_obj.get(str(s.uid), {})
    if s.is_latest is None:
        print(s.uid, 'is_latest is None')
    if s.is_latest and state.get('status', '') == 'scored':
        s_handler = MRIx2026Handler(s.workplace, s.submission_file)
        res = s_handler.score_check()
        print('Checking submission: ', s.uid, res['primary_score'])
