import git

from database_handler.database_handler import DatabaseHandler
from chromecast_handler import ChromecastHandler


class BackEndHandler:
    SERVER_URL = "http://192.168.1.200:8000/"
    SERVER_URL_TV_SHOWS = SERVER_URL + "tv_shows/"
    MEDIA_FOLDER_PATH = "/media/hdd1/plex_media/tv_shows/"
    MEDIA_METADATA_FILE = "tv_show_metadata.json"

    startup_sha = None
    chromecast_handler = None

    def __init__(self):
        repo = git.Repo(search_parent_directories=True)
        self.startup_sha = repo.head.object.hexsha
        print(self.startup_sha)
        self.chromecast_handler = ChromecastHandler()
        # Build database if it doesn't exist
        DatabaseHandler(self.MEDIA_FOLDER_PATH)

    def get_startup_sha(self):
        return self.startup_sha

    def start(self):
        self.chromecast_handler.start()

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

    def play_episode(self, media_id):
        self.chromecast_handler.play_from_sql(media_id, self.SERVER_URL_TV_SHOWS, self.MEDIA_FOLDER_PATH)

    def get_tv_show_name_list(self):
        db_handler = DatabaseHandler(self.MEDIA_FOLDER_PATH)
        if db_handler:
            return db_handler.get_tv_show_name_list()

    def get_tv_show_season_name_list(self, tv_show_id):
        db_handler = DatabaseHandler(self.MEDIA_FOLDER_PATH)
        if db_handler:
            return db_handler.get_tv_show_season_name_list(tv_show_id)

    def get_tv_show_season_episode_name_list(self, season_id):
        db_handler = DatabaseHandler(self.MEDIA_FOLDER_PATH)
        if db_handler:
            return db_handler.get_tv_show_season_episode_name_list(season_id=season_id)

    def get_tv_show_metadata(self, media_id):
        db_handler = DatabaseHandler(self.MEDIA_FOLDER_PATH)
        if db_handler:
            return db_handler.get_tv_show_metadata(media_id)

    def get_tv_show_season_metadata(self, media_id):
        db_handler = DatabaseHandler(self.MEDIA_FOLDER_PATH)
        if db_handler:
            return db_handler.get_tv_show_season_metadata(media_id)
