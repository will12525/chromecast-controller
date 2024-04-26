import subprocess
import threading
import requests  # request img from web
import shutil  # save img locally
import git
import pathlib

import config_file_handler
import database_handler.common_objects as common_objects
from chromecast_handler import ChromecastHandler
from database_handler.create_database import DBCreator
from database_handler.database_handler import DatabaseHandler
import mp4_splitter
from database_handler.media_metadata_collector import extract_tv_show_file_name_content


def setup_db():
    with DBCreator() as db_connection:
        db_connection.create_db()
        for media_folder_info in config_file_handler.load_js_file().get("media_folders"):
            media_directory_info = common_objects.default_media_directory_info.copy()
            media_directory_info.update(media_folder_info)
            db_connection.setup_media_directory(media_directory_info)


def editor_save_txt_file(output_path, editor_metadata):
    mp4_splitter.editor_save_txt_file(output_path, editor_metadata)


def editor_validate_txt_file(editor_raw_folder, editor_metadata):
    try:
        return mp4_splitter.editor_validate_txt_file(editor_raw_folder, editor_metadata)
    except ValueError as e:
        raise ValueError(e.args[0]) from e
    except FileNotFoundError as e:
        raise FileNotFoundError(e.args[0]) from e


def get_free_disk_space(editor_folder):
    df = subprocess.Popen(["df", f"{editor_folder}"], stdout=subprocess.PIPE)
    output = df.communicate()[0]
    print(output)
    device, size, used, available, percent, mount_point = output.decode("utf-8").split("\n")[1].split()
    return available


def download_image(json_request):
    if (not json_request.get('image_url')
            or len(json_request.get('image_url')) < 5
            or not json_request.get('content_type')
            or not json_request.get('id')
            or json_request.get('image_url')[-4:] not in ['.jpg', '.png']):
        raise ValueError({{"message": "Image url must be .jpg or .png"}})

    file_name = f"{json_request.get('content_type')}_{json_request.get('id')}{json_request.get('image_url')[-4:]}"

    with DatabaseHandler() as db_connection:
        media_folder_path = db_connection.get_media_folder_path(1)
        if len(common_objects.ContentType) > json_request.get('content_type'):
            content_type = common_objects.ContentType(json_request.get('content_type'))
            media_metadata = db_connection.get_media_content(content_type, params_dict=json_request)
        else:
            raise ValueError(
                {"message": 'Unknown content type provided', 'value': json_request.get('content_type')})

    if json_request.get('image_url') == media_metadata.get("image_url"):
        json_request['image_url'] = file_name
        return

    if not media_folder_path:
        raise ValueError({"message": "Error media directory table missing paths"})

    output_path = f"{pathlib.Path(media_folder_path.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN)).resolve().parent.absolute()}/images/{file_name}"

    if pathlib.Path(output_path).resolve().exists():
        json_request['image_url'] = file_name
        raise ValueError({"message": "Image url already exists, assigning existing image",
                          "file_name": json_request.get('image_url'), "string": f"{file_name}"})

    res = requests.get(json_request.get('image_url'), stream=True)

    if res.status_code == 200:
        with open(output_path, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
        print('Image successfully Downloaded: ', output_path)
        json_request['image_url'] = file_name
    else:
        raise ValueError(
            {"message": "requests error encountered while saving image", "file_name": json_request.get('image_url'),
             "string": f"{res.status_code}"})


def build_tv_show_output_path(file_name_str):
    media_metadata = {}
    file_name = pathlib.Path(file_name_str)
    with DatabaseHandler() as db_connection:
        media_folder_path = db_connection.get_media_folder_path(1)
    if not media_folder_path:
        raise ValueError({"message": "Error media directory table missing paths"})

    extract_tv_show_file_name_content(media_metadata, file_name.stem)
    output_path = pathlib.Path(
        f"{media_folder_path.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN)}/{media_metadata[common_objects.PLAYLIST_TITLE]}/{file_name}").resolve()
    if output_path.exists():
        raise FileExistsError({"message": "File already exists", "file_name": str(file_name_str)})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


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

    def get_editor_metadata(self, editor_raw_folder, selected_txt_file=None):
        return mp4_splitter.get_editor_metadata(editor_raw_folder, self.editor_processor, selected_txt_file)

    def editor_process_txt_file(self, editor_raw_folder, editor_metadata, media_output_parent_path):
        try:
            return mp4_splitter.editor_process_txt_file(editor_raw_folder, editor_metadata, media_output_parent_path,
                                                        self.editor_processor)
        except ValueError as e:
            raise ValueError(e.args[0]) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(e.args[0]) from e
        except FileExistsError as e:
            raise FileExistsError(e.args[0]) from e

    def editor_get_process_metadata(self):
        return self.editor_processor.get_metadata()
