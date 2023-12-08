import git

from database_handler.create_database import DBCreator, MediaType
from chromecast_handler import ChromecastHandler


class BackEndHandler:
    SERVER_URL = "http://192.168.1.200:8000/"
    SERVER_URL_TV_SHOWS = SERVER_URL + "tv_shows/"
    SERVER_URL_MOVIES = SERVER_URL + "movies/"
    MEDIA_FOLDER_PATH = "/media/hdd1/plex_media/tv_shows"
    MEDIA_FOLDER_PATH_MOVIES = "/media/hdd1/plex_media/movies"

    startup_sha = None
    chromecast_handler = None

    def __init__(self):
        repo = git.Repo(search_parent_directories=True)
        self.startup_sha = repo.head.object.hexsha
        print(self.startup_sha)
        self.chromecast_handler = ChromecastHandler()
        # Build database if it doesn't exist
        media_paths = [{"media_type": MediaType.TV_SHOW.value, "media_folder_path": self.MEDIA_FOLDER_PATH,
                        "media_folder_url": self.SERVER_URL_TV_SHOWS},
                       {"media_type": MediaType.MOVIE.value, "media_folder_path": self.MEDIA_FOLDER_PATH_MOVIES,
                        "media_folder_url": self.SERVER_URL_MOVIES}
                       ]
        db_creator = DBCreator()
        for media_path in media_paths:
            db_creator.setup_media_directory(media_path)

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

    def play_media_on_chromecast(self, media_id, playlist_id=None):
        self.chromecast_handler.play_from_sql(media_id, playlist_id)
