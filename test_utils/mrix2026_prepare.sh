WORKDIR=/app/test_utils/MRIx2026
python export_wjx_responses.py 371015584 $WORKDIR/submissions.xlsx
./parse_xlsx.sh $WORKDIR/submissions.xlsx
python pull_all.py $WORKDIR/submissions
