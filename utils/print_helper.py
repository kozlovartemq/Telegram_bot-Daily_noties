import json


def print_json(json_type, sort_keys=False):
    print(json.dumps(json_type, sort_keys=sort_keys, indent=4, ensure_ascii=False))