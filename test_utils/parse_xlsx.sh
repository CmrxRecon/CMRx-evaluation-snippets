echo $1
python /app/scripts/xlsx2json.py $1
submission_dir=`dirname $1`
json_dir=$submission_dir/submissions
python /app/test_utils/mark_latest.py --write $json_dir
