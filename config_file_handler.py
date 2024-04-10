import json
from json import JSONDecodeError

CONFIG_FILE = "config.json"


def load_js_file(filename: str = CONFIG_FILE):
    with open(filename) as f_in:
        return json.load(f_in)


def save_txt_file_content(txt_file_path, txt_file_content):
    if ".txt" in txt_file_path:
        with open(txt_file_path, 'w+', encoding="utf-8") as f:
            f.write(txt_file_content)
    else:
        print(f"Not a txt file: {txt_file_path}")


def load_txt_file_content(file_path):
    if file_path.suffix == ".txt" and file_path.is_file():
        with open(file_path, 'r', encoding="utf-8") as f:
            return f.readlines()
    else:
        print(f"Not a txt file: {file_path}")
    return []


def save_json_file_content(txt_file_content, file_path):
    if ".json" in file_path:
        with open(file_path, "w+", encoding="utf-8") as of:
            json.dump(txt_file_content, of)
    else:
        print(f"Not a json file: {file_path}")


def load_json_file_content(file_path):
    try:
        if file_path.suffix == ".json" and file_path.is_file():
            with open(file_path, 'r', encoding="utf-8") as f:
                return json.loads(f.read())
        else:
            print(f"Not a json file: {file_path}")
    except JSONDecodeError as e:
        pass
    return {}
