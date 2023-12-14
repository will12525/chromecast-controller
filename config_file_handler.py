import json

CONFIG_FILE = "config.json"


def load_js_file(filename: str = CONFIG_FILE):
    with open(filename) as f_in:
        return json.load(f_in)
