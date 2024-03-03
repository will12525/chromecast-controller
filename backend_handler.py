import threading
import git
import pathlib

import config_file_handler
from chromecast_handler import ChromecastHandler
from database_handler.create_database import DBCreator

EDITOR_FOLDER = "/media/hdd1/plex_media/splitter/"
EDITOR_RAW_FOLDER = f"{EDITOR_FOLDER}raw_files/"


def setup_db():
    with DBCreator() as db_connection:
        db_connection.create_db()
        for media_folder_info in config_file_handler.load_js_file():
            db_connection.setup_media_directory(media_folder_info)


class BackEndHandler:
    startup_sha = None
    chromecast_handler = None

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
    
    def get_editor_txt_files(self):
        editor_txt_file_list = ["Hello", "World!", EDITOR_FOLDER, EDITOR_RAW_FOLDER]
        RAW_PATH = pathlib.Path(EDITOR_RAW_FOLDER).resolve()
        print(RAW_PATH)
        print(RAW_PATH.is_dir())
        print(list(RAW_PATH.rglob("*.mp4")))
        for raw_folder_mp4 in list(RAW_PATH.rglob("*.mp4")):
            print(raw_folder_mp4)
            raw_txt_file = str(raw_folder_mp4).replace('.mp4', '.txt')
            editor_txt_file_list.append(raw_txt_file)

        
        return editor_txt_file_list

