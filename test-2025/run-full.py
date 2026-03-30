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

    def output_path(self):
        return os.path.join(self.workplace, 'infer')

    def score_path(self):
        return os.path.join(self.workplace, 'score')


client = docker.from_env()
api = client.api

def pull_and_run(r: ExecutationRequest, workplace: os.PathLike, gpu_id="0"):
    image = r.image
    # image = 'dev.passer.zyheal.com:8087/passer/passer-vtk-rendering-server:CI-devel_latest'
    # logger.info(f'pulling image: {image}')
    # client.images.pull(image)
    FIXED_NAME = f'2025-test-phase-{r.uid}'
    container = client.containers.run(image,
                         volumes=[
                             f'{input_dir}:/input/:ro',
                             f'{workplace}/infer:/output'
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

def score(r: ExecutationRequest):
    type_map = {
        'Task Regular1' : 'TaskR1',
        'Task Regular2': 'TaskR2',
        'Task Special1': 'TaskS1',
        'Task Special2': 'TaskS2'
        }
    cmd = f'python /app/test-2025/Test_Score2025.py -t {type_map[r.type]} -g {gt_dir} -i {r.output_path()} -o {r.score_path()} -e {xlsx}'
    print(cmd)
    os.system(cmd)
    assert os.path.isfile(os.path.join(r.score_path(), 'Result/results.json'))


def notification(request: ExecutationRequest):
    r = request
    # TODO send notification and the logs as attachment

    content = f"""
Dear {r.team_name}:
    
    Your Test request executed, request id: {r.uid}.

Best regards,
CMRxRecon Team
                   """
    e = os.environ
    server = mail.get_smtp_server(e['SMTP_SERVER'], int(e['SMTP_PORT']), 
                                 e['EMAIL'], e['EMAIL_TOKEN'])
    mail.send_text_mail(e['EMAIL'], 'xuziqiang@zyheal.com',
                   f'Test result notification', content,
                   server)



if __name__ == '__main__':
    import sys
    # 通过命令行指定python
    uid = sys.argv[1]
    gpu_id = sys.argv[2]
    if len(sys.argv) == 4:
        FULL_SET = sys.argv[3]
    else:
        FULL_SET = False

    storage_dir = '/mnt/nas/nas4/privateData/tmp-CMRxRecon2025-debug'
    repo_dir = '/app'

    if FULL_SET:
        # For regular tasks
        input_dir = '/mnt/nas/nas3/openData/share/Docker_Test_Undersample_FullSet'
        gt_dir = '/mnt/nas/nas3/openData/share/ChallengeData_TestSet_GroundTruth'
        xlsx = '/app/test-2025/test-data/full-CMRxRecon2025_TestData_Disease_Info_English.xlsx'
        # For special tasks
        input_dir = '/SSDHome/share/ChallengeData_TestSet_SpecialTask_UnderSample_FullSet'
        input_dir = '/SSDHome/share/ChallengeData_TestSet_SpecialTask_UnderSample'
        gt_dir = '/SSDHome/share/ChallengeData_TestSet_SpecialTask_GroundTruth'

        output_dir = f'{storage_dir}/test-output'
        state_json = f'{repo_dir}/test-2025/test-data/full-status.json'

    else:
        input_dir = f'/mnt/SSD1_P1/tmp-Docker_Test_Undersample'
        gt_dir = '/app/test-2025/debug-gt'
        output_dir = f'{storage_dir}/output-demo'
        state_json = f'{repo_dir}/test-2025/test-data/status.json'
        xlsx = '/app/test-2025/test-data/CMRxRecon2025_TestData_Disease_Info_Docker_Test_English.xlsx'
    
    s = status.load(state_json)
    with open(f'./test-data/json/{uid}.json') as f:
        request = json.load(f)
    r = ExecutationRequest(request)
    r.workplace = f'{output_dir}/{r.uid}'

    uid = str(r.uid)
    workplace = os.path.join(output_dir, uid)
    os.makedirs(workplace, exist_ok=True)
    info = s.get(uid, {'status': 'unknown'})
    s[uid] = info
    current_status = info['status']

    # 预测阶段
    if current_status == status.UNKNOWN:
        pull_and_run(r, workplace, gpu_id=gpu_id)
        s = status.load(state_json)
        s[uid] = {'status': status.INFERED}
        status.save(s, state_json)

    # 打分阶段
    current_status = s[uid]['status']
    if current_status == status.INFERED:
        score(r)
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
