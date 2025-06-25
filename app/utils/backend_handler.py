import threading
import traceback

import requests  # request img from web
import git
import pathlib
import shutil

from app.utils import config_file_handler, mp4_splitter
from app.utils.chromecast_handler import ChromecastHandler
from app.database.db_getter import DBHandler
from app.utils.common import get_system_data, build_editor_output_path

EDITOR_PROCESSED_LOG = "editor_metadata.json"


def setup_db():
    db_connection = DBHandler()
    db_connection.open()
    db_connection.create_db()
    for media_folder_info in config_file_handler.load_json_file_content().get("media_folders", []):
        content_path = pathlib.Path(media_folder_info.get("content_src", "")).resolve()
        if content_path.exists():
            pathlib.Path(content_path / "tv_shows").mkdir(exist_ok=True)
            pathlib.Path(content_path / "movies").mkdir(exist_ok=True)
            pathlib.Path(content_path / "books").mkdir(exist_ok=True)
            db_connection.setup_content_directory(media_folder_info)
        else:
            print(f"Config file path missing: {content_path}")
    db_connection.close()


def delete_splitter_file(file_name):
    if raw_folder := config_file_handler.load_json_file_content().get('editor_raw_folder'):
        mp4_file_name = file_name.replace(".json", ".mp4")
        json_file_path = pathlib.Path(f"{raw_folder}/{file_name}")
        mp4_file_path = pathlib.Path(f"{raw_folder}/{mp4_file_name}")
        if mp4_file_path.exists():
            print(f"Deleting: {mp4_file_path}")
            mp4_file_path.unlink()
            if json_file_path.exists():
                json_file_path.unlink()


def editor_validate_txt_file(file_name, media_type):
    error_log = []
    if destination_dir_path := build_editor_output_path(media_type, error_log):
        error_log.extend(mp4_splitter.editor_validate_txt_file(file_name, destination_dir_path))
    return error_log


def editor_save_file(file_name, file_content):
    raw_folder = config_file_handler.load_json_file_content().get('editor_raw_folder')
    file_path = pathlib.Path(f"{raw_folder}{file_name}").resolve()
    config_file_handler.save_json_file_content(file_path, file_content)


def download_image(json_request):
    if (not json_request.get("img_src")
            or len(json_request.get("img_src")) < 5
            or not (json_request.get("container_id") or json_request.get("content_id"))
            or json_request.get("img_src")[-4:] not in ['.jpg', '.png', '.webp']):
        raise ValueError({{"message": "Image url must be .jpg or .png"}})

    db_connection = DBHandler()
    db_connection.open()
    if container_id := json_request.get("container_id"):
        media_metadata = db_connection.get_container_info(container_id)
        parent_file = media_metadata.get('container_path')
        file_path = f"{parent_file}/{media_metadata.get('container_title')}{pathlib.Path(json_request['img_src']).suffix}"
    elif content_id := json_request.get("content_id"):
        media_metadata = db_connection.get_content_info(content_id)
        parent_file = media_metadata.get('content_src')
        file_path = f"{parent_file}{pathlib.Path(json_request['img_src']).suffix}"

    if json_request.get("img_src") == media_metadata.get("img_src"):
        return

    res = requests.get(json_request.get('img_src'), stream=True)
    media_directory = None

    for media_directory in db_connection.get_all_content_directory_info():
        print(f'{media_directory.get("content_src")}{parent_file}')
        if pathlib.Path(f'{media_directory.get("content_src")}{parent_file}').exists():
            break
    db_connection.close()

    if res.status_code == 200 and media_directory:
        json_request["img_url"] = f"{media_directory.get('content_url')}/{file_path}"
        output_path = pathlib.Path(f"{media_directory.get('content_src')}/{file_path}").resolve().absolute()
        print(f'Downloading {json_request.get("img_src")} to {output_path}')
        with open(output_path, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
        print('Image successfully Downloaded: ', output_path)
        json_request["img_src"] = str(file_path)
    else:
        print({"message": "requests error encountered while saving image",
               "file_name": json_request.get("img_src"),
               "string": f"{res.status_code}"})
        raise ValueError(
            {"message": "requests error encountered while saving image",
             "file_name": json_request.get("img_src"),
             "string": f"{res.status_code}"})


class BackEndHandler:
    startup_sha = None
    chromecast_handler = None
    editor_thread = mp4_splitter.SubclipThreadHandler()
    media_scan_in_progress = False
    transfer_in_progress = False

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

    def play_media_on_chromecast(self, content_data):
        return self.chromecast_handler.play_from_sql(content_data)

    def play_random_container_content(self, json_request):
        return self.chromecast_handler.play_random_container_content(json_request)

    def scan_media_directories(self):
        try:
            if not self.media_scan_in_progress:
                self.media_scan_in_progress = True
                db_connection = DBHandler()
                db_connection.open()
                db_connection.scan_content_directories()
                db_connection.close()
                self.media_scan_in_progress = False
            else:
                print("Scan in progress")
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
            self.media_scan_in_progress = False

    def get_editor_metadata(self, selected_txt_file=None):
        config_file = config_file_handler.load_json_file_content()
        raw_folder = config_file.get('editor_raw_folder')
        raw_folder_url = config_file.get('editor_raw_url')

        editor_metadata = mp4_splitter.get_editor_metadata(raw_folder, self.editor_thread,
                                                           selected_editor_file=selected_txt_file,
                                                           raw_url=raw_folder_url,
                                                           process_file=EDITOR_PROCESSED_LOG)
        editor_metadata["storage"] = get_system_data()
        return editor_metadata

    def editor_process_txt_file(self, media_type, file_name):
        error_log = []
        destination_dir_path = build_editor_output_path(media_type, error_log)
        if not error_log and destination_dir_path:
            error_log.extend(
                mp4_splitter.editor_process_media_file(file_name, destination_dir_path, self.editor_thread))
        if not error_log:
            mp4_splitter.update_processed_file(file_name, EDITOR_PROCESSED_LOG)
        return error_log

    def editor_get_process_metadata(self):
        return self.editor_thread.get_metadata()
