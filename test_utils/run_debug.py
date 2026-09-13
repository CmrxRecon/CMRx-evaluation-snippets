from ast import Not, arg
from datetime import datetime
import docker
import os
import json
import logging
from docker.models.containers import Container
from docker.types.containers import DeviceRequest

import status
from t4u import file_tree


logger = logging.getLogger(__name__)


class ExecutationRequest:
    def __init__(self, request: dict) -> None:
        self.workplace = ''
        self._data = request
        r = request
        self.uid = r['uid']
        self.type = r['type']
        self.image = r['image']
        self.team_name = r['team_name']
        self.email = r['email']
        self.synapse_address = r['synapse_address'],
        # 后期加入的字段
        self.is_latest = r.get('is_latest')
        self.comment = r.get('comment')

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
    def __init__(self, competition_name: str, submission_json: str) -> None:
        self.competition_name = competition_name
        self.submission_json = submission_json

    def score_check(self, r: ExecutationRequest):
        assert r.rel_path('score/Result/resuts.json')


class MRIx2026Handler(SubmissionHandler):
    def __init__(self, competition_name: str, submission_json: str) -> None:
        super().__init__(competition_name, submission_json)
        self.r = None
        # TODO 自动根据 submission_json 加载

    def score_check(self, r: ExecutationRequest):
        assert r.rel_path('score/Result/resuts.json')
    
    def dedicate_check_score(self, r: ExecutationRequest):
        """
        预处理动作
        for i in `seq 1 130`;do echo Checking $i;python3 run_debug.py --action=check_score MRIx2026/test.json 0 MRIx2026/submissions/$i.json; done
        """

        resuslt_path = r.rel_path('score/Result/results.json')
        if r.type != 'Task3' and os.path.exists(resuslt_path):
            # 检查 Avg_T1W_Dice_adj
            results = json.loads(open(resuslt_path).read())
            t1w_dice = results.get('Avg_T1W_Dice_adj', None)
            submission = json.loads(open(args.submission_json).read())
            if t1w_dice is not None and t1w_dice < 0.3:
                print(f"----- {r.uid}--{r.is_latest} {resuslt_path} ------")
                print(f"----- {args.submission_json} {submission.get('comment')} ------")
                print(r.email)
                print(f'MRIx2026 test phase submission {r.uid} feedback')
                print(f"Hi {r.team_name},\n")
                print(f"Your score metric `'Avg_T1W_Dice_adj': {results['Avg_T1W_Dice_adj']}` is abnormal. This is most likely caused by a coordinate system issue. Please fix it and resubmit as soon as possible.")
                print(submission)
                print("-----------\n\n")
                return False
        return True


client = docker.from_env()
api = client.api

def pull_and_run(r: ExecutationRequest, input_dir: os.PathLike, workplace: os.PathLike, gpu_id="0", prefix='Unknown'):
    image = r.image
    # image = 'dev.passer.zyheal.com:8087/passer/passer-vtk-rendering-server:CI-devel_latest'
    # logger.info(f'pulling image: {image}')
    # client.images.pull(image)
    FIXED_NAME = f'{prefix}-test-phase-{r.uid}-gpu{gpu_id}'
    with open(os.path.join(workplace, 'infer.log'), 'wb') as f:
        f.write(bytes(f'{datetime.now()}, start container \n image: {image}\n {r.json()}\n', encoding='utf8'))
    container = client.containers.run(image,
                         volumes=[
                             f'{input_dir}:/input/:ro',
                             f'{r.output_path}:/output'
                         ],
                         name=FIXED_NAME,
                        stderr=True,
                        network_mode=None,
                        shm_size='64g',
                        #  remove=True,
                        # tty=True,
                        detach=True,
                         device_requests=[DeviceRequest(device_ids=[gpu_id], capabilities=[['gpu']])],
                        #  entrypoint='ls -alh /input'
                         )
    # print(str(logs_bytes, 'utf-8'))
    container.wait()
    c = client.containers.get(FIXED_NAME)
    logs_bytes = container.logs()
    # print(str(logs_bytes))
    with open(os.path.join(workplace, 'infer.log'), 'ab') as f:
        f.write(bytes(f'{datetime.now()}, container stopped\n', encoding='utf8'))
        f.write(logs_bytes)
        # if len(logs_bytes) != 0: return
    # container.remove()


def score_cmrx2026(r: ExecutationRequest):
    """
    python3 test-2026/score.py -i /mnt/HDD1_P1/guanli/CMRx2026/test-phase/2/infer/ 
    -t R2 -s TestSet -g /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_GT 
    -x /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_EMPTY 
    --flowvn /mnt/nas/nas3/openData/rawdata/4dFlow/ChallengeData_FlowVN/
    -o /mnt/HDD1_P1/guanli/CMRx2026/test-phase/2/score
    """
    type_map = {
        'Task Regular1': 'R1',
        'Task Regular2': 'R2',
        'Task Special1': 'S1',
        'Task Special2': 'S2'
        }
    flowvn_dir = paths.get('flowvn', "/tmp/no-flowvn")
    empty_dir = paths['empty']
    cmd = f'python /app/test-2026/score.py -t {type_map[r.type]} -x {empty_dir} --flowvn {flowvn_dir} -s TestSet -g {gt_dir} -i {r.infer_path} -o {r.score_path}'
    print(cmd)
    os.system(cmd)
    assert os.path.isfile(os.path.join(r.score_path, f'Result/result_{type_map[r.type]}.csv'))


def score_mrix2026(r: ExecutationRequest, mode: str, paths: [str]):
    assert mode == 'test'
    task_type = r.type
    if mode == 'debug':
        # TODO 确保有64个nii.gz文件
        pass
    else:
        # TODO 检查文件数目正确
        pass

    mark_file = r.rel_path("seg_done")
    input_dir = r.rel_path("infer")
    # 只允许T1W、T2FLAIR、T2W目录存在，其余的都删掉
    for d in os.listdir(input_dir):
        if d not in ['T1W', 'T2FLAIR', 'T2W']:
            os.system(f'rm -rf {os.path.join(input_dir, d)}')

    seg_output_dir = r.rel_path(f"infer_seg")
    if task_type in ['Task1', 'Task2']:
        #  and not os.path.exists(mark_file):
        # 分割 推理
        """
        docker run --rm --gpus="device=1" --entrypoint python -v /mnt/:/mnt/ mrix2026-synthseg:rc.1 /app/synthseg-script/segment.py \
        --input_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer \
        --output_dir /mnt/HDD1_P1/guanli/MRIx2026/test-phase/6/infer_seg
        """
        container = client.containers.run("mrix2026-synthseg:rc.3",
                              volumes=[
                                  f'{input_dir}:/input/:ro',
                                  f'{seg_output_dir}:/output',
                              ],
                              name=f"MRIx2026-test-phase-seg-{r.uid}-gpu{gpu_id}",
                              detach=True,
                              device_requests=[DeviceRequest(device_ids=[gpu_id], capabilities=[['gpu']])],
                              )
        container.wait()
        # 结束了生成标记文件
        with open(mark_file, "w") as f:
            f.write("done")
        # container.remove()
    
    pack_root = paths['pack_root']
    score_py = 'python3 /app/MRIx2026-test/score.py'
    if task_type in ['Task1', 'Task2']:
        cmd = f'docker exec -ti debug-2025 {score_py} --input {input_dir} --prediction_seg_dir {seg_output_dir} --task {task_type.lower()} --pack_root {pack_root}  --output {r.score_path}'
    elif task_type == 'Task3':
        cmd = f'docker exec -ti debug-2025 {score_py} --input {input_dir} --task {task_type.lower()} --pack_root {pack_root}  --output {r.score_path}'
    os.system(cmd)
    assert os.path.isfile(os.path.join(r.score_path, f'Result/results.json'))

def fast_check_infer(r: ExecutationRequest, competition_name: str, mode: str):
    """
    快速检查输出文件是否正确
    """
    if competition_name == 'MRIx2026' and mode == 'test':
        if r.type == 'Task1' or r.type == 'Task2':
            assert file_tree.dir_stat(r.infer_path).file_count == 60
        if r.type == 'Task3':
            assert file_tree.dir_stat(r.infer_path).file_count == 120





if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run test-phase evaluation pipeline')
    parser.add_argument('task_describe', help='任务描述 JSON 文件路径')
    parser.add_argument('gpu_id', help='指定使用的 GPU ID')
    parser.add_argument('submission_json', help='提交信息 JSON 文件路径')
    parser.add_argument('--action', type=str, default=None, help='预处理动作')
    args = parser.parse_args()

    task_describe = args.task_describe
    gpu_id = args.gpu_id
    submission_json = os.path.abspath(args.submission_json)

    with open(submission_json) as f:
        request = json.load(f)
        task_type = request['type']
        is_latest = request.get('is_latest', False)

    with open(task_describe) as f:
        des = json.load(f)

    mode = des['meta']['mode']
    task_des = None
    for i in des['tasks']:
        if task_type == i['task_type']:
            task_des = i
            break
    if not task_des:
        raise Exception('No describle files of ')
    
    competition_name = des["meta"]["competition"]

    paths = task_des['paths']
    input_dir = paths['input']
    output_dir = paths['output']
    gt_dir = paths['ground_truth']

    os.makedirs(output_dir, exist_ok=True)
    state_json = os.path.join(output_dir, 'state.json')
    r = ExecutationRequest(request)
    
    if 'debug' == mode:
        pass
    if 'test' == mode:
        pass
    
    if os.path.exists(state_json):
        s = status.load(state_json)
    else:
        s = {}
        status.save(s, state_json)

    uid = str(r.uid)
    workplace = os.path.join(output_dir, uid)
    r.workplace = workplace

    os.makedirs(workplace, exist_ok=True)
    # 复制json到workplace
    os.system(f'cp {submission_json} {r.rel_path("submission.json")}')
    if 'MRIx2026' == competition_name:
        handler = MRIx2026Handler(competition_name, submission_json)
        handler.r = r
        if args.action == 'check_score':
            passed = handler.dedicate_check_score(r)
            if not passed:
                s = status.load(state_json)
                s[uid] = {'status': status.DEBUGING}
                status.save(s, state_json)
            exit(0)
    if not is_latest:
        # 等文件复制完成再提示非latest，方便查看
        raise Exception('Only latest submission is allowed')

    info = s.get(uid, {'status': status.UNKNOWN})
    s[uid] = info
    current_status = info['status']

    print(f"*****{info}******")

    # 预测阶段
    if current_status == status.UNKNOWN:
        container_prefix = f'{competition_name}-{mode}'
        
        s = status.load(state_json)
        s[uid] = {'status': status.INFERING}
        status.save(s, state_json)
        try:
            pull_and_run(r, input_dir, workplace, gpu_id=gpu_id, prefix=container_prefix)
            fast_check_infer(r, competition_name, mode)
        except Exception as e:
            # 推理失败
            s = status.load(state_json)
            s[uid] = {'status': status.DEBUGING}
            status.save(s, state_json)

            exit(-1)
            
        s = status.load(state_json)
        s[uid] = {'status': status.INFERED}
        status.save(s, state_json)

    # 打分阶段
    current_status = s[uid]['status']
    if current_status == status.INFERED:
        #  or current_status == status.SCORED:
        if 'CMRx2026' == competition_name:
            score_cmrx2026(r)
        elif 'MRIx2026' == competition_name:
            score_mrix2026(r, mode, paths)
            handler: MRIx2026Handler
            check_passed = handler.dedicate_check_score(r)
            if not check_passed:
                s = status.load(state_json)
                s[uid] = {'status': status.DEBUGING}
                status.save(s, state_json)
        else:
            raise Exception(f'Unknown competition: {competition_name}')

        s = status.load(state_json)
        s[uid] = {'status': status.SCORED}
        status.save(s, state_json)

    current_status = s[uid]['status']
    if current_status == status.SCORED:
        # TODO notification
        # notification(request)
        # s[r.uid]['status'] = status.NOTIFIED
        # status.save(s)
        pass
