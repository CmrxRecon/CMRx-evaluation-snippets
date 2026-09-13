python /app/score-status-dashboard/test_gather_result.py /app/test_utils/MRIx2026/MRIx-test-phase /app/score-status-dashboard/mrixfields.github.io/2026/test-phase/mrix2026-state.json
cd /app/score-status-dashboard/mrixfields.github.io/
git config pull.rebase false
git pull
git commit -am "chore(mrix2026): update test phase state"
git push
cd -