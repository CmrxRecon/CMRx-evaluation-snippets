import json


UNKNOWN = 'unknown'
INFERING = 'infering'
INFERED = 'infered'
SCORED = 'scored' 
DEBUGING = 'debuging'
NOTIFIED = 'notified'


def load(state_json):
    with open(state_json) as f:
        return json.load(f)


def save(status: dict, state_json):
    with open(state_json, 'w') as f:
        json.dump(status, f, ensure_ascii=False, indent=4)
