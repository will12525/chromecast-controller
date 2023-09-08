import git

import media_folder_metadata_handler
from chromecast_handler import ChromecastHandler


class BackEndHandler:
    SERVER_URL = "http://192.168.1.200:8000/"
    SERVER_URL_TV_SHOWS = SERVER_URL + "tv_shows/"
    MEDIA_FOLDER_PATH = "/media/hdd1/plex_media/tv_shows/"
    MEDIA_METADATA_FILE = "tv_show_metadata.json"

    startup_sha = None
    chromecast_handler = None
    media_folder_metadata_handler = None

    def __init__(self):
        repo = git.Repo(search_parent_directories=True)
        self.startup_sha = repo.head.object.hexsha
        print(self.startup_sha)
        self.chromecast_handler = ChromecastHandler()
        self.media_folder_metadata_handler = media_folder_metadata_handler.MediaFolderMetadataHandler(
            self.MEDIA_METADATA_FILE, self.MEDIA_FOLDER_PATH)

    def get_startup_sha(self):
        return self.startup_sha

    def start(self):
        self.chromecast_handler.start()

    def get_chromecast_scan_list(self):
        return self.chromecast_handler.get_scan_list()

    def get_chromecast_device_id(self):
        return self.chromecast_handler.get_chromecast_id()

    def get_media_current_time(self):
        return self.chromecast_handler.get_media_current_time()

    def get_media_current_duration(self):
        return self.chromecast_handler.get_media_current_duration()

    def seek_media_time(self, media_time):
        self.chromecast_handler.seek_media_time(media_time)

    def send_chromecast_cmd(self, cmd):
        self.chromecast_handler.send_command(cmd)

    def connect_chromecast(self, device_id_str):
        self.chromecast_handler.connect_chromecast(device_id_str)

    def disconnect_chromecast(self):
        self.chromecast_handler.disconnect_chromecast()

    def set_media_id(self, media_id):
        return self.media_folder_metadata_handler.set_media_id(media_id)

    def get_media_id(self):
        return self.media_folder_metadata_handler.get_media_id()

    def get_episode_url(self):
        return self.media_folder_metadata_handler.get_url(self.SERVER_URL_TV_SHOWS)

    def get_current_playing_episode_info(self):
        return self.chromecast_handler.get_current_playing_episode_info()

    def play_episode(self):
        self.chromecast_handler.play_from_media_drive(self.media_folder_metadata_handler, self.SERVER_URL_TV_SHOWS)

    def get_tv_show_name_list(self):
        return self.media_folder_metadata_handler.get_tv_show_name_list()

    def get_tv_show_season_name_list(self):
        return self.media_folder_metadata_handler.get_tv_show_season_name_list()

    def get_tv_show_season_episode_name_list(self):
        return self.media_folder_metadata_handler.get_tv_show_season_episode_name_list()

    def update_media_id_selection(self, new_media_id):
        return self.media_folder_metadata_handler.update_media_id_selection(new_media_id)
