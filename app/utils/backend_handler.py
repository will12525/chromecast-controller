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
    try:
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
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
    finally:
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
    _chromecast_handler = None
    startup_sha = None
    editor_thread = mp4_splitter.SubclipThreadHandler()
    media_scan_in_progress = False
    transfer_in_progress = False
    # Last finished scan result for /scan_status polling (message after async job ends)
    last_scan_result = None  # type: dict | None
    _scan_lock = threading.Lock()

    def __init__(self):
        repo = git.Repo(search_parent_directories=True)
        self.startup_sha = repo.head.object.hexsha
        print(self.startup_sha)
        self.chromecast = self.get_chromecast()

    @classmethod
    def get_chromecast(cls):
        if cls._chromecast_handler is None:
            cls._chromecast_handler = ChromecastHandler()
            cls._chromecast_handler.start()
        return cls._chromecast_handler

    def get_startup_sha(self):
        return self.startup_sha

    def start(self):
        setup_db_thread = threading.Thread(target=setup_db, args=(), daemon=True)
        setup_db_thread.start()
        return setup_db_thread

    def get_chromecast_scan_list(self):
        return self.chromecast.get_scan_list()

    def get_chromecast_device_id(self):
        return self.chromecast.get_chromecast_id()

    def get_chromecast_device_name(self):
        return self.chromecast.get_chromecast_name()

    def seek_media_time(self, media_time):
        self.chromecast.seek_media_time(media_time)

    def send_chromecast_cmd(self, cmd):
        self.chromecast.send_command(cmd)

    def connect_chromecast(self, device_id_str):
        return self.chromecast.connect_chromecast(device_id_str)

    def disconnect_chromecast(self):
        self.chromecast.disconnect_chromecast()

    def get_chromecast_media_controller_metadata(self):
        return self.chromecast.get_media_controller_metadata()

    def play_media_on_chromecast(self, content_data):
        return self.chromecast.play_from_sql(content_data)

    def play_random_container_content(self, json_request):
        return self.chromecast.play_random_container_content(json_request)

    def scan_media_directories(self):
        """
        Scan content directories once (synchronous).

        Returns:
            dict: {"status": "ok"|"busy"|"error", "message": str}
        """
        if self.media_scan_in_progress:
            print("Scan in progress")
            return {"status": "busy", "message": "Scan already in progress"}
        try:
            self.media_scan_in_progress = True
            db_connection = DBHandler()
            db_connection.open()
            db_connection.scan_content_directories()
            db_connection.close()
            result = {"status": "ok", "message": "Scan complete"}
            self.last_scan_result = result
            return result
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
            result = {"status": "error", "message": str(e)}
            self.last_scan_result = result
            return result
        finally:
            self.media_scan_in_progress = False

    def get_scan_status(self):
        """Payload for GET /scan_status."""
        busy = bool(self.media_scan_in_progress or self.transfer_in_progress)
        payload = {
            "scanning": bool(self.media_scan_in_progress),
            "transfer_in_progress": bool(self.transfer_in_progress),
            "status": "busy" if busy else "idle",
        }
        if self.last_scan_result:
            payload["last_result"] = dict(self.last_scan_result)
        return payload

    def start_scan_media_directories(self, run_client_sync=False):
        """
        Start a background media scan (and optional CLIENT content pull).

        Returns immediately with status "started" or "busy".
        Clients should poll get_scan_status() until status is idle, then read last_result.
        """
        with self._scan_lock:
            if self.media_scan_in_progress or self.transfer_in_progress:
                return {"status": "busy", "message": "Scan already in progress"}
            self.media_scan_in_progress = True
            self.last_scan_result = None

        def _job():
            final = {"status": "ok", "message": "Scan complete"}
            try:
                db_connection = DBHandler()
                db_connection.open()
                try:
                    db_connection.scan_content_directories()
                finally:
                    db_connection.close()

                if run_client_sync and not self.transfer_in_progress:
                    print("Starting server content pull")
                    self.transfer_in_progress = True
                    try:
                        from app.utils import content_transfer

                        content_transfer.query_server()
                    finally:
                        self.transfer_in_progress = False
                    # Rescan after transfer so newly pulled files appear
                    db_connection = DBHandler()
                    db_connection.open()
                    try:
                        db_connection.scan_content_directories()
                    finally:
                        db_connection.close()
                    final = {
                        "status": "ok",
                        "message": "Scan complete (synced from server)",
                    }
            except Exception as e:
                print("Exception class: ", e.__class__)
                print(f"ERROR: {e}")
                print(traceback.print_exc())
                final = {"status": "error", "message": str(e)}
            finally:
                self.last_scan_result = final
                self.media_scan_in_progress = False
                self.transfer_in_progress = False

        threading.Thread(target=_job, daemon=True, name="media-scan").start()
        return {"status": "started", "message": "Scan started"}

    def get_editor_metadata(self, selected_txt_file=None):
        config_file = config_file_handler.load_json_file_content()
        raw_folder = config_file.get('editor_raw_folder')
        raw_folder_url = config_file.get('editor_raw_url')

        editor_metadata = mp4_splitter.get_editor_metadata(raw_folder, self.editor_thread,
                                                           selected_editor_file=selected_txt_file,
                                                           raw_url=raw_folder_url,
                                                           process_file=EDITOR_PROCESSED_LOG)
        storage = get_system_data()
        editor_metadata["storage"] = storage
        # Flag low storage so the editor UI can warn / block process starts.
        # percent_used is 0-100; treat >= 90% used as low free space.
        low = [
            item for item in (storage or [])
            if (item.get("percent_used") or 0) >= 90 or (item.get("free_space") or 0) <= 5
        ]
        editor_metadata["storage_low"] = bool(low)
        editor_metadata["storage_warnings"] = low
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
