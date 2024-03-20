import json
import subprocess
import threading
from json import JSONDecodeError

import git
import pathlib

import config_file_handler
from chromecast_handler import ChromecastHandler
from database_handler.create_database import DBCreator
from database_handler.media_metadata_collector import mp4_file_ext, txt_file_ext
import mp4_splitter


def setup_db():
    with DBCreator() as db_connection:
        db_connection.create_db()
        for media_folder_info in config_file_handler.load_js_file():
            db_connection.setup_media_directory(media_folder_info)


def save_txt_file_content(txt_file_path, txt_file_content):
    if ".txt" in txt_file_path:
        with open(txt_file_path, 'w+') as f:
            f.write(txt_file_content)
    else:
        print(f"Not a txt file: {txt_file_path}")


def load_txt_file_content(path):
    if path.suffix == ".txt" and path.is_file():
        with open(path, 'r', encoding="utf-8") as f:
            return f.read()
    else:
        print(f"Not a txt file: {path}")
    return ""


def save_json_file_content(txt_file_content, json_file_path):
    if ".json" in json_file_path:
        with open(json_file_path, "w+") as of:
            json.dump(txt_file_content, of)
        # json.dump(txt_file_content, json_file_path)
        # with open(json_file_path, 'w+') as f:
        #     f.write(txt_file_content)
    else:
        print(f"Not a txt file: {json_file_path}")


def load_json_file_content(path):
    try:
        if path.suffix == ".json" and path.is_file():
            with open(path, 'r', encoding="utf-8") as f:
                return json.loads(f.read())
        else:
            print(f"Not a json file: {path}")
    except JSONDecodeError as e:
        pass
    return {}


class BackEndHandler:
    startup_sha = None
    chromecast_handler = None
    editor_processor = mp4_splitter.SubclipProcessHandler()

    def __init__(self):
        repo = git.Repo(search_parent_directories=True)
        self.startup_sha = repo.head.object.hexsha
        print(self.startup_sha)
        self.chromecast_handler = ChromecastHandler()

    def get_startup_sha(self):
        return self.startup_sha

    def start(self):
        setup_db_thread = threading.Thread(target=setup_db, args=(), daemon=True)
        setup_db_thread.start()
        self.chromecast_handler.start()
        return setup_db_thread

    def get_chromecast_scan_list(self):
        return self.chromecast_handler.get_scan_list()

    def get_chromecast_device_id(self):
        return self.chromecast_handler.get_chromecast_id()

    def seek_media_time(self, media_time):
        self.chromecast_handler.seek_media_time(media_time)

    def send_chromecast_cmd(self, cmd):
        self.chromecast_handler.send_command(cmd)

    def connect_chromecast(self, device_id_str):
        return self.chromecast_handler.connect_chromecast(device_id_str)

    def disconnect_chromecast(self):
        self.chromecast_handler.disconnect_chromecast()

    def get_chromecast_media_controller_metadata(self):
        return self.chromecast_handler.get_media_controller_metadata()

    def play_media_on_chromecast(self, media_request_ids):
        self.chromecast_handler.play_from_sql(media_request_ids)

    def get_editor_txt_files(self, editor_raw_folder):
        raw_path = pathlib.Path(editor_raw_folder).resolve()
        editor_txt_files = []
        for editor_mp4_file in list(sorted(raw_path.rglob(mp4_file_ext))):
            if "old" not in editor_mp4_file.parts:
                editor_txt_file_path = pathlib.Path(str(editor_mp4_file).replace("mp4", "txt")).resolve()
                editor_txt_file_path.touch()
                editor_txt_files.append(editor_txt_file_path)
        return editor_txt_files

    def check_editor_txt_file_processed(self, editor_metadata_file, editor_txt_file_names):
        editor_txt_file_processed = []
        metadata_file = pathlib.Path(editor_metadata_file).resolve()
        metadata_file_content = load_json_file_content(metadata_file)
        for editor_txt_file in editor_txt_file_names:
            if editor_txt_file in metadata_file_content:
                editor_txt_file_processed.append({
                    "file_name": editor_txt_file,
                    "processed": metadata_file_content.get(editor_txt_file).get("processed")
                })
            else:
                editor_txt_file_processed.append({
                    "file_name": editor_txt_file,
                    "processed": False
                })
        return editor_txt_file_processed

    def get_editor_metadata(self, editor_metadata_file, editor_raw_folder, selected_txt_file=None):
        selected_index = 0
        editor_metadata = {}
        editor_txt_files = self.get_editor_txt_files(editor_raw_folder)
        editor_txt_file_names = [editor_txt_file.as_posix().replace(editor_raw_folder, "") for editor_txt_file in
                                 editor_txt_files]

        if editor_txt_file_names:
            if not selected_txt_file or selected_txt_file not in editor_txt_file_names:
                selected_txt_file = editor_txt_file_names[selected_index]

            selected_txt_file_path = pathlib.Path(f"{editor_raw_folder}{selected_txt_file}").resolve()

            editor_metadata = {
                "txt_file_list": self.check_editor_txt_file_processed(editor_metadata_file, editor_txt_file_names),
                "selected_txt_file_title": selected_txt_file,
                "selected_txt_file_content": load_txt_file_content(selected_txt_file_path)
            }
        editor_metadata.update(self.editor_get_process_metadata())
        return editor_metadata

    def editor_save_txt_file(self, editor_raw_folder, editor_metadata):
        sub_clip_file = f"{editor_raw_folder}{editor_metadata.get('txt_file_name')}.txt"
        save_txt_file_content(sub_clip_file, editor_metadata.get('txt_file_content'))
        print(sub_clip_file)
        print(editor_metadata.get('txt_file_content'))

    def editor_process_txt_file(self, editor_metadata_file, editor_raw_folder, editor_metadata,
                                media_output_parent_path):
        sub_clip_file = f"{editor_raw_folder}{editor_metadata.get('txt_file_name')}.txt"
        if editor_metadata.get('txt_file_content', None):
            try:
                save_txt_file_content(sub_clip_file, editor_metadata.get('txt_file_content'))
            except FileExistsError as e:
                pass
        try:
            sub_clips = self.editor_validate_txt_file(editor_raw_folder, editor_metadata)
            mp4_splitter.get_cmd_list(sub_clips, sub_clip_file, media_output_parent_path)
            self.editor_processor.add_cmds_to_queue(editor_metadata_file, sub_clips)
            editor_metadata_content = {}
            editor_metadata_file_path = pathlib.Path(editor_metadata_file).resolve()
            try:
                editor_metadata_content = load_json_file_content(editor_metadata_file_path)
            except (FileNotFoundError, JSONDecodeError) as e:
                pass
            editor_metadata_content[editor_metadata.get('txt_file_name')] = {"processed": True}
            save_json_file_content(editor_metadata_content, editor_metadata_file)

        except ValueError as e:
            raise ValueError(e.args[0]) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(e.args[0]) from e
        except FileExistsError as e:
            error_dict = e.args[0]
            error_dict["txt_file_name"] = editor_metadata.get('txt_file_name')
            raise FileExistsError(error_dict) from e

    def editor_validate_txt_file(self, editor_raw_folder, editor_metadata):
        txt_file_name = f"{editor_raw_folder}{editor_metadata.get('txt_file_name')}.txt"
        try:
            return mp4_splitter.get_sub_clips_from_txt_file(txt_file_name)
        except ValueError as e:
            raise ValueError(e.args[0]) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(e.args[0]) from e

    def editor_get_process_metadata(self):
        return self.editor_processor.get_metadata()

    def get_free_disk_space(self, editor_folder):
        df = subprocess.Popen(["df", f"{editor_folder}"], stdout=subprocess.PIPE)
        output = df.communicate()[0]
        print(output)
        device, size, used, available, percent, mountpoint = output.decode("utf-8").split("\n")[1].split()
        return available
