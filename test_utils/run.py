from tokenize import Special
import docker
import os
import json
import logging
from docker.models.containers import Container
from docker.types.containers import DeviceRequest

import status
from t4u import mail


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
        self.synapse_address = r['synapse_address']

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


client = docker.from_env()
api = client.api

def pull_and_run(r: ExecutationRequest, input_dir: os.PathLike, workplace: os.PathLike, gpu_id="0", prefix='Unknown'):
    image = r.image
    # image = 'dev.passer.zyheal.com:8087/passer/passer-vtk-rendering-server:CI-devel_latest'
    # logger.info(f'pulling image: {image}')
    # client.images.pull(image)
    FIXED_NAME = f'{prefix}-test-phase-{r.uid}'
    container = client.containers.run(image,
                         volumes=[
                             f'{input_dir}:/input/:ro',
                             f'{r.output_path}:/output'
                         ],
                         name=FIXED_NAME,
                        stderr=True,
                        network_mode=None,
                        shm_size='32g',
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
    with open(os.path.join(workplace, 'infer.log'), 'wb') as f:
        f.write(bytes(f'image: {image}\n {r.json()}\n', encoding='utf8'))
        f.write(logs_bytes)
        # if len(logs_bytes) != 0: return
    container.remove()

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



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run test-phase evaluation pipeline')
    parser.add_argument('task_describe', help='任务描述 JSON 文件路径')
    parser.add_argument('gpu_id', help='指定使用的 GPU ID')
    parser.add_argument('submission_json', help='提交信息 JSON 文件路径')
    args = parser.parse_args()

    task_describe = args.task_describe
    gpu_id = args.gpu_id
    submission_json = args.submission_json

    with open(submission_json) as f:
        request = json.load(f)
        task_type = request['type']

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
    r.workplace = os.path.join(output_dir, str(r.uid))

    uid = str(r.uid)
    workplace = os.path.join(output_dir, uid)
    os.makedirs(workplace, exist_ok=True)
    info = s.get(uid, {'status': status.UNKNOWN})
    s[uid] = info
    current_status = info['status']

    print(f"*****{info}******")
    competition_name = des["meta"]["competition"]

    # 预测阶段
    if current_status == status.UNKNOWN:
        container_prefix = f'{competition_name}-{mode}'
        pull_and_run(r, input_dir, workplace, gpu_id=gpu_id, prefix=container_prefix)
        s = status.load(state_json)
        s[uid] = {'status': status.INFERED}
        status.save(s, state_json)

    # 打分阶段
    current_status = s[uid]['status']
    if current_status == status.INFERED:
        if 'CMRx2026' == competition_name:
            score_cmrx2026(r)
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
