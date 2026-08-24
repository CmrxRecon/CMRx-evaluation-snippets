import json


UNKNOWN = 'unknown'
INFERED = 'infered'
SCORED = 'scored' 
NOTIFIED = 'notified'


def load(state_json):
    with open(state_json) as f:
        return json.load(f)


def save(status: dict, state_json):
    with open(state_json, 'w') as f:
        json.dump(status, f, ensure_ascii=False, indent=4)
