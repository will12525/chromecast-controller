import json
import subprocess
import threading
import traceback

import requests  # request img from web
import shutil  # save img locally
import git
import pathlib
import re

import config_file_handler
import database_handler.common_objects as common_objects
from chromecast_handler import ChromecastHandler
from database_handler.db_setter import DBCreatorV2
from database_handler.db_getter import DatabaseHandlerV2
import mp4_splitter
from database_handler.media_metadata_collector import get_content_type

EDITOR_PROCESSED_LOG = "editor_metadata.json"
DISK_SPACE_USE_LIMIT = 20


def setup_db():
    with DBCreatorV2() as db_connection:
        db_connection.create_db()
        for media_folder_info in config_file_handler.load_json_file_content().get("media_folders", []):
            db_connection.setup_content_directory(media_folder_info)


def get_free_disk_space(size=None, ret=3, dir_path=None):
    path = dir_path
    if dir_path and dir_path.is_file():
        path = dir_path.parent

    if path and path.exists():
        print(f"Check free space of directory: {path}")
        cmd = ["df", f"{path}"]
        if size:
            cmd = ["df", "-B", size, f"{path}"]
        df = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output = df.communicate()[0]
        decoded_output_list = output.decode("utf-8").split("\n")
        # device, size, used, available, percent, mount_point
        print(f"Disk space check: {decoded_output_list}")
        cmd_output_list = output.decode("utf-8").split("\n")[1].split()
        return cmd_output_list[ret]
    else:
        print(f"Missing Path: {path}")
    return ""


def get_free_disk_space_percent(editor_folder):
    return get_free_disk_space(ret=4, dir_path=editor_folder)


def get_system_data():
    disk_space = {
        "disk_space": []
    }
    if raw_folder := config_file_handler.load_json_file_content().get('editor_raw_folder'):
        disk_space["raw_folder"] = {
            "free_disk_space": get_free_disk_space(size="G", dir_path=raw_folder),
            "free_disk_percent": get_free_disk_space_percent(raw_folder),
            "directory_path": raw_folder
        }

    with DBCreatorV2() as db_connection:
        media_directory_info = db_connection.get_all_content_directory_info()

    for media_directory in media_directory_info:
        media_directory_path_str = media_directory.get("content_src")
        disk_space["disk_space"].append(
            {
                "free_disk_space": get_free_disk_space(size="G", dir_path=media_directory_path_str),
                "free_disk_percent": get_free_disk_space_percent(media_directory_path_str),
                "directory_path": media_directory_path_str
            })

    return disk_space


def path_has_space(dir_path):
    free_disk_space_str = get_free_disk_space(size="G", dir_path=dir_path)
    if free_disk_space_str:
        try:
            return int(free_disk_space_str[:-1]) > DISK_SPACE_USE_LIMIT
        except ValueError as e:
            print(e)
    return False


def get_free_media_drive():
    with DBCreatorV2() as db_connection:
        media_directory_info = db_connection.get_all_content_directory_info()

    for media_directory in media_directory_info:
        media_directory_path_str = media_directory.get("content_src")
        if path_has_space(media_directory_path_str):
            return media_directory


def build_editor_output_path(media_type, error_log):
    mp4_output_parent_path = None
    with DBCreatorV2() as db_connection:
        media_folder_path = db_connection.get_all_content_directory_info()[0]
    if media_type == common_objects.ContentType.RAW.name:
        pass
        if raw_folder := config_file_handler.load_json_file_content().get('editor_raw_folder'):
            if not path_has_space(raw_folder):
                error_log.append({"message": "Splitter folder out of space", "file_name": f"{raw_folder}",
                                  "value": get_free_disk_space(size="G", dir_path=raw_folder)})
        else:
            error_log.append({"message": "Splitter folder missing from config file"})
    elif media_type == common_objects.ContentType.MOVIE.name:
        mp4_output_parent_path = pathlib.Path(f"{media_folder_path.get('content_src')}/movies").resolve()
    elif media_type == common_objects.ContentType.TV.name:
        mp4_output_parent_path = pathlib.Path(f"{media_folder_path.get('content_src')}/tv_shows").resolve()
    elif media_type == common_objects.ContentType.BOOK.name:
        mp4_output_parent_path = pathlib.Path(f"{media_folder_path.get('content_src')}/books").resolve()
    else:
        print(f"Unknown media type: {media_type}")

    if mp4_output_parent_path:
        if not path_has_space(mp4_output_parent_path):
            error_log.append({"message": "Splitter folder out of space", "file_name": f"{mp4_output_parent_path}",
                              "value": get_free_disk_space(size="G", dir_path=mp4_output_parent_path)})
    return mp4_output_parent_path


def editor_validate_txt_file(json_request):
    error_log = []
    if mp4_output_parent_path := build_editor_output_path(json_request.get("media_type"), error_log):
        error_log.extend(mp4_splitter.editor_validate_txt_file(json_request.get('file_name'), mp4_output_parent_path))
    return error_log


def editor_save_file(file_name, json_request):
    raw_folder = config_file_handler.load_json_file_content().get('editor_raw_folder')
    file_path = pathlib.Path(f"{raw_folder}{file_name}").resolve()
    mp4_splitter.editor_save_file(file_path, json_request)


def download_image(json_request):
    if (not json_request.get("img_src")
            or len(json_request.get("img_src")) < 5
            or not (json_request.get("container_id") or json_request.get("content_id"))
            or json_request.get("img_src")[-4:] not in ['.jpg', '.png', '.webp']):
        raise ValueError({{"message": "Image url must be .jpg or .png"}})

    with DBCreatorV2() as db_connection:
        media_folder_path = db_connection.get_all_content_directory_info()[0]

    with DatabaseHandlerV2() as db_connection:
        if container_id := json_request.get("container_id"):
            media_metadata = db_connection.get_container_info(container_id)
            file_path = f"{media_metadata.get('container_path')}/{media_metadata.get('container_title')}{pathlib.Path(json_request['img_src']).suffix}"
        elif content_id := json_request.get("content_id"):
            media_metadata = db_connection.get_content_info(content_id)
            file_path = f"{media_metadata.get('content_src')}{pathlib.Path(json_request['img_src']).suffix}"

    if json_request.get("img_src") == media_metadata.get("img_src"):
        return

    res = requests.get(json_request.get('img_src'), stream=True)

    if res.status_code == 200:
        output_path = pathlib.Path(f"{media_folder_path.get('content_src')}/{file_path}").resolve().absolute()
        with open(output_path, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
        print('Image successfully Downloaded: ', output_path)
        json_request["img_src"] = str(file_path)
    else:
        print({"message": "requests error encountered while saving image",
               "file_name": json_request.get(common_objects.IMAGE_URL),
               "string": f"{res.status_code}"})
        raise ValueError(
            {"message": "requests error encountered while saving image",
             "file_name": json_request.get(common_objects.IMAGE_URL),
             "string": f"{res.status_code}"})


def build_tv_show_output_path(file_name_str):
    error_log = []
    output_path = None
    mp4_output_parent_path = None

    content_type = get_content_type(f"/{file_name_str}")
    if content_type:
        mp4_output_parent_path = build_editor_output_path(content_type.name, error_log)
    # media_directory = get_free_media_drive()
    # content_src = media_directory.get("content_src")
    if not error_log and mp4_output_parent_path:
        if content_type == common_objects.ContentType.TV:
            if match := re.search(r"^([\w\W]+) - s(\d+)e(\d+)\.mp4$", file_name_str):
                output_path = mp4_output_parent_path / match[1] / file_name_str
        else:
            output_path = mp4_output_parent_path / file_name_str
        if output_path.exists():
            raise FileExistsError({"message": "File already exists", "file_name": file_name_str})
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path.as_posix()
    else:
        print(error_log)


class BackEndHandler:
    startup_sha = None
    chromecast_handler = None
    editor_processor = mp4_splitter.SubclipProcessHandler()
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

    def scan_media_directories(self):
        try:
            if not self.media_scan_in_progress:
                self.media_scan_in_progress = True
                with DBCreatorV2() as db_connection:
                    db_connection.scan_content_directories()
                self.media_scan_in_progress = False
            else:
                print("Scan in progress")
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
        finally:
            self.media_scan_in_progress = False

    def get_editor_metadata(self, selected_txt_file=None):
        config_file = config_file_handler.load_json_file_content()
        raw_folder = config_file.get('editor_raw_folder')
        raw_folder_url = config_file.get('editor_raw_url')
        return mp4_splitter.get_editor_metadata(raw_folder, self.editor_processor,
                                                selected_editor_file=selected_txt_file, raw_url=raw_folder_url,
                                                process_file=EDITOR_PROCESSED_LOG)

    def editor_process_txt_file(self, json_request):
        error_log = []
        mp4_output_parent_path = build_editor_output_path(json_request.get("media_type"), error_log)
        if not error_log and mp4_output_parent_path:
            error_log.extend(
                mp4_splitter.editor_process_txt_file(json_request, mp4_output_parent_path, self.editor_processor))
        if not error_log:
            mp4_splitter.update_processed_file(json_request.get('file_name'), EDITOR_PROCESSED_LOG)
        return error_log

    def editor_get_process_metadata(self):
        return self.editor_processor.get_metadata()
