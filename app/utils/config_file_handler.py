import json
import pathlib
from json import JSONDecodeError

CONFIG_FILE = "app/config.json"


def save_txt_file_content(file_path, txt_file_content):
    if file_path.suffix == ".txt":
        with open(file_path, 'w+', encoding="utf-8") as f:
            f.write(txt_file_content)
    else:
        print(f"Not a txt file: {file_path}")


def load_txt_file_content(file_path):
    if file_path.exists() and file_path.suffix == ".txt" and file_path.is_file():
        with open(file_path, 'r', encoding="utf-8") as f:
            return f.readlines()
    else:
        print(f"Not a txt file: {file_path}")
    return []


def save_json_file_content(file_path, txt_file_content):
    if file_path.suffix == ".json":
        with open(file_path, "w+", encoding="utf-8") as of:
            json.dump(txt_file_content, of)
    else:
        print(f"Not a json file: {file_path}")


def load_json_file_content(file_path=None):
    if not file_path:
        file_path = pathlib.Path(CONFIG_FILE).resolve()
    try:
        if file_path.suffix == ".json" and file_path.is_file():
            with open(file_path, 'r', encoding="utf-8") as f:
                return json.loads(f.read())
        else:
            print(f"Not a json file: {file_path}")
    except JSONDecodeError as e:
        print(e)
    return {}


def load_content_file():
    return load_json_file_content(pathlib.Path(CONFIG_FILE).resolve())
