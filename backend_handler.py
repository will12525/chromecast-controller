import threading
import git
import pathlib

import config_file_handler
from chromecast_handler import ChromecastHandler
from database_handler.create_database import DBCreator
from database_handler.media_metadata_collector import mp4_file_ext, txt_file_ext
import mp4_splitter

EDITOR_FOLDER = "/media/hdd1/plex_media/splitter/"
EDITOR_RAW_FOLDER = f"{EDITOR_FOLDER}raw_files/"


# EDITOR_RAW_FOLDER = "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/"


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

    def play_media_on_chromecast(self, media_id):
        self.chromecast_handler.play_from_sql(media_id)

    def get_mp4_txt_files(self):
        RAW_PATH = pathlib.Path(EDITOR_RAW_FOLDER).resolve()
        return list(sorted(RAW_PATH.rglob(mp4_file_ext)))

    def get_editor_txt_files(self, editor_mp4_files=None):
        editor_txt_files = []

        if not editor_mp4_files:
            editor_mp4_files = self.get_mp4_txt_files()

        for editor_mp4_file in editor_mp4_files:
            editor_txt_file_path = pathlib.Path(str(editor_mp4_file).replace("mp4", "txt")).resolve()
            editor_txt_file_path.touch()
            editor_txt_files.append(editor_txt_file_path)

        return editor_txt_files

    def get_editor_txt_file_names(self, editor_txt_files=None):
        if not editor_txt_files:
            editor_txt_files = self.get_editor_txt_files()
        return [editor_txt_file.stem for editor_txt_file in editor_txt_files]

    def get_editor_metadata(self, input_txt_file=None):
        editor_txt_files = self.get_editor_txt_files()
        if len(editor_txt_files) >= 1:
            assert ".mp4" not in str(editor_txt_files[0])
            assert ".txt" in str(editor_txt_files[0])

        selected_index = 0
        editor_txt_file_names = self.get_editor_txt_file_names(editor_txt_files)
        selected_txt_file = editor_txt_file_names[selected_index]
        selected_txt_file_content = load_txt_file_content(editor_txt_files[selected_index])

        if input_txt_file and input_txt_file in editor_txt_file_names:
            selected_txt_file = input_txt_file
            selected_txt_file_content = load_txt_file_content(
                editor_txt_files[editor_txt_file_names.index(selected_txt_file)])

        editor_metadata = {
            "txt_file_list": editor_txt_file_names,
            "selected_txt_file_title": selected_txt_file,
            "selected_txt_file_content": selected_txt_file_content
        }
        editor_metadata.update(self.editor_get_process_metadata())
        return editor_metadata

    def editor_save_txt_file(self, editor_metadata):
        sub_clip_file = f"{EDITOR_RAW_FOLDER}{editor_metadata.get('txt_file_name')}.txt"
        save_txt_file_content(sub_clip_file, editor_metadata.get('txt_file_content'))
        print(sub_clip_file)
        print(editor_metadata.get('txt_file_content'))

    # def editor_load_txt_file(self, editor_metadata):
    #     sub_clip_file = f"{EDITOR_RAW_FOLDER}{editor_metadata.get('txt_file_name')}.txt"
    #     editor_metadata['txt_file_content'] = load_txt_file_content(sub_clip_file)
    #     # load_txt_file(sub_clip_file, editor_metadata.get('txt_file_content'))
    #     # return { "load_txt_file":  }

    def editor_process_txt_file(self, editor_metadata, media_output_parent_path):
        sub_clip_file = f"{EDITOR_RAW_FOLDER}{editor_metadata.get('txt_file_name')}.txt"
        try:
            save_txt_file_content(sub_clip_file, editor_metadata.get('txt_file_content'))
        except FileExistsError as e:
            pass

        try:
            sub_clips = self.editor_validate_txt_file(editor_metadata)
            mp4_splitter.get_cmd_list(sub_clips, sub_clip_file, media_output_parent_path)
            self.editor_processor.add_cmds_to_queue(sub_clips)
        except ValueError as e:
            raise ValueError(e.args[0]) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(e.args[0]) from e
        except FileExistsError as e:
            error_dict = e.args[0]
            error_dict["txt_file_name"] = editor_metadata.get('txt_file_name')
            raise FileExistsError(error_dict) from e

    def editor_validate_txt_file(self, editor_metadata):
        txt_file_name = f"{EDITOR_RAW_FOLDER}{editor_metadata.get('txt_file_name')}.txt"
        try:
            return mp4_splitter.get_sub_clips_from_txt_file(txt_file_name)
        except ValueError as e:
            raise ValueError(e.args[0]) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(e.args[0]) from e

    def editor_get_process_metadata(self):
        return self.editor_processor.get_metadata()
