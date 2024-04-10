import json
import subprocess
import threading
from json import JSONDecodeError
import requests  # request img from web
import shutil  # save img locally
import git
import pathlib

import config_file_handler
from chromecast_handler import ChromecastHandler
from database_handler.common_objects import MEDIA_DIRECTORY_PATH_COLUMN
from database_handler.create_database import DBCreator
from database_handler.database_handler import DatabaseHandler
from database_handler.media_metadata_collector import mp4_file_ext, txt_file_ext
import mp4_splitter


def setup_db():
    with DBCreator() as db_connection:
        db_connection.create_db()
        for media_folder_info in config_file_handler.load_js_file():
            db_connection.setup_media_directory(media_folder_info)


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

    def editor_save_txt_file(self, output_path, editor_metadata):
        mp4_splitter.editor_save_txt_file(output_path, editor_metadata)

    def get_editor_metadata(self, editor_metadata_file, editor_raw_folder, selected_txt_file=None):
        return mp4_splitter.get_editor_metadata(editor_metadata_file, editor_raw_folder, self.editor_processor,
                                                selected_txt_file)

    def editor_validate_txt_file(self, editor_raw_folder, editor_metadata):
        try:
            return mp4_splitter.editor_validate_txt_file(editor_raw_folder, editor_metadata)
        except ValueError as e:
            raise ValueError(e.args[0]) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(e.args[0]) from e

    def editor_process_txt_file(self, editor_metadata_file, editor_raw_folder, editor_metadata,
                                media_output_parent_path):
        try:
            return mp4_splitter.editor_process_txt_file(editor_metadata_file, editor_raw_folder, editor_metadata,
                                                        media_output_parent_path, self.editor_processor)
        except ValueError as e:
            raise ValueError(e.args[0]) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(e.args[0]) from e
        except FileExistsError as e:
            raise FileExistsError(e.args[0]) from e

    def editor_get_process_metadata(self):
        return self.editor_processor.get_metadata()

    def get_free_disk_space(self, editor_folder):
        df = subprocess.Popen(["df", f"{editor_folder}"], stdout=subprocess.PIPE)
        output = df.communicate()[0]
        print(output)
        device, size, used, available, percent, mountpoint = output.decode("utf-8").split("\n")[1].split()
        return available

    def download_image(self, json_request):
        if (not json_request.get('image_url')
                or len(json_request.get('image_url')) < 5
                or not json_request.get('content_type')
                or not json_request.get('id')
                or json_request.get('image_url')[-4:] not in ['.jpg', '.png']):
            raise ValueError

        with DatabaseHandler() as db_connection:
            db_connection.update_media_metadata(json_request)
            media_metadata = db_connection.get_media_folder_path(1)

        if not media_metadata:
            raise ValueError

        file_name = f"{json_request.get('content_type')}_{json_request.get('id')}{json_request.get('image_url')[-4:]}"
        output_path = f"{pathlib.Path(media_metadata.get(MEDIA_DIRECTORY_PATH_COLUMN)).resolve().parent.absolute()}/{file_name}"

        res = requests.get(json_request.get('image_url'), stream=True)

        if res.status_code == 200:
            with open(output_path, 'wb') as f:
                shutil.copyfileobj(res.raw, f)
            print('Image successfully Downloaded: ', output_path)

        print(pathlib.Path(file_name).resolve())
        print(output_path, file_name)
