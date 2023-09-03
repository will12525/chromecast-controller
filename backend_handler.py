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
        if self.chromecast_handler:
            self.chromecast_handler.start()

    def get_chromecast_scan_list(self):
        if self.chromecast_handler:
            return self.chromecast_handler.get_scan_list()

    def get_chromecast_connected_device_list(self):
        if self.chromecast_handler:
            return self.chromecast_handler.get_connected_devices_list_str()

    def send_chromecast_cmd(self, cmd):
        if self.chromecast_handler:
            self.chromecast_handler.send_command(cmd)

    def connect_chromecast(self, device_id_str):
        if self.chromecast_handler:
            self.chromecast_handler.connect_to_chromecast(device_id_str)

    def disconnect_chromecast(self, device_id_str):
        if self.chromecast_handler:
            self.chromecast_handler.disconnect_from_chromecast(device_id_str)

    def set_episode(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        if self.media_folder_metadata_handler:
            return self.media_folder_metadata_handler.set_episode_id(tv_show_id,
                                                                     tv_show_season_id,
                                                                     tv_show_season_episode_id)
        return False

    def get_episode_url(self):
        if self.media_folder_metadata_handler:
            return self.media_folder_metadata_handler.get_url(self.SERVER_URL_TV_SHOWS)

    def play_episode(self):
        if self.chromecast_handler and self.media_folder_metadata_handler:
            self.chromecast_handler.play_from_media_drive(self.media_folder_metadata_handler, self.SERVER_URL_TV_SHOWS)

    def get_tv_show_name_list(self):
        if self.media_folder_metadata_handler:
            return media_folder_metadata_handler.get_tv_show_name_list(
                self.media_folder_metadata_handler.get_media_metadata())
        return None

    def get_tv_show_season_name_list(self, tv_show_id):
        if self.media_folder_metadata_handler:
            return media_folder_metadata_handler.get_tv_show_season_name_list(
                self.media_folder_metadata_handler.get_media_metadata(), tv_show_id)
        return None

    def get_tv_show_season_episode_name_list(self, tv_show_id, tv_show_season_id):
        if self.media_folder_metadata_handler:
            return media_folder_metadata_handler.get_tv_show_season_episode_name_list(
                self.media_folder_metadata_handler.get_media_metadata(), tv_show_id, tv_show_season_id)
        return None

    def get_tv_show_metadata(self, tv_show_id):
        if self.media_folder_metadata_handler:
            return media_folder_metadata_handler.get_tv_show_metadata(
                self.media_folder_metadata_handler.get_media_metadata(), tv_show_id)
        return None

    def get_tv_show_season_metadata(self, tv_show_id, tv_show_season_id):
        if self.media_folder_metadata_handler:
            return media_folder_metadata_handler.get_tv_show_season_metadata(
                self.media_folder_metadata_handler.get_media_metadata(), tv_show_id, tv_show_season_id)
        return None

    def get_tv_show_season_episode_metadata(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        if self.media_folder_metadata_handler:
            return media_folder_metadata_handler.get_tv_show_season_episode_metadata(
                self.media_folder_metadata_handler.get_media_metadata(),
                tv_show_id,
                tv_show_season_id,
                tv_show_season_episode_id)
        return None
