from . import DBConnection, MediaType
from .database_handler import GET_ALL_MEDIA_DIRECTORIES
from .media_metadata_collector import collect_tv_shows, collect_movies, collect_new_tv_shows

# playlist_info and media_info are the sources


sql_create_playlist_info_table = """CREATE TABLE IF NOT EXISTS playlist_info (
                                id integer PRIMARY KEY,
                                playlist_title text NOT NULL UNIQUE
                                );"""

sql_insert_playlist_info_table = '''INSERT OR IGNORE INTO playlist_info (playlist_title) VALUES(?)'''

sql_create_playlist_media_list_table = """CREATE TABLE IF NOT EXISTS playlist_media_list (
                                          id integer PRIMARY KEY,
                                          playlist_id integer NOT NULL,
                                          media_id integer NOT NULL,
                                          list_index integer NOT NULL,
                                          FOREIGN KEY (media_id) REFERENCES media_info (id),
                                          FOREIGN KEY (playlist_id) REFERENCES playlist_info (id),
                                          UNIQUE (playlist_id, media_id, list_index)
                                        );"""

sql_insert_playlist_media_list_table = '''INSERT INTO playlist_media_list (playlist_id, media_id, list_index) VALUES (?, ?, ?)'''

sql_create_tv_show_info_table = """CREATE TABLE IF NOT EXISTS tv_show_info (
                                id integer PRIMARY KEY,
                                playlist_id integer NOT NULL UNIQUE,
                                FOREIGN KEY (playlist_id) REFERENCES playlist_info (id)
                            );"""

sql_insert_tv_show_info_table = '''INSERT INTO tv_show_info (playlist_id) VALUES (?)'''

sql_create_season_info_table = """CREATE TABLE IF NOT EXISTS season_info (
                                id integer PRIMARY KEY,
                                tv_show_id integer NOT NULL,
                                tv_show_season_index integer NOT NULL,
                                FOREIGN KEY (tv_show_id) REFERENCES tv_show_info (id),
                                UNIQUE(tv_show_id, tv_show_season_index)
                            );"""

sql_insert_season_info_table = '''INSERT INTO season_info (tv_show_id, tv_show_season_index) VALUES (?, ?)'''

sql_create_media_info_table = """CREATE TABLE IF NOT EXISTS media_info (
                                id integer PRIMARY KEY,
                                tv_show_id integer,
                                season_id integer,
                                media_folder_path_id NOT NULL,
                                media_title text NOT NULL,
                                path text NOT NULL UNIQUE,
                                FOREIGN KEY (tv_show_id) REFERENCES season_info (id),
                                FOREIGN KEY (season_id) REFERENCES season_info (id),
                                FOREIGN KEY (media_folder_path_id) REFERENCES media_folder_path_id (id),
                                UNIQUE(media_folder_path_id, media_title, path)
                            );"""

sql_insert_media_info_table = '''INSERT INTO media_info (tv_show_id, season_id, media_folder_path_id, media_title, path) VALUES (?, ?, ?, ?, ?)'''

sql_create_media_folder_path_table = """CREATE TABLE IF NOT EXISTS media_folder_path (
                                id integer PRIMARY KEY,
                                media_type integer NOT NULL,
                                media_folder_path text NOT NULL UNIQUE,
                                media_folder_url text NOT NULL UNIQUE,
                                new_media_folder_path text
                            );"""

sql_insert_media_folder_path_table = ''' INSERT INTO media_folder_path(media_type, media_folder_path, new_media_folder_path, media_folder_url) VALUES(?, ?, ?, ?) '''

db_table_creation_list = [sql_create_tv_show_info_table, sql_create_season_info_table, sql_create_media_info_table,
                          sql_create_playlist_info_table, sql_create_playlist_media_list_table,
                          sql_create_media_folder_path_table]

# Get row ID's from various contents
GET_ID = "SELECT id FROM "
GET_PLAYLIST_ID_FROM_TITLE = f"{GET_ID} playlist_info WHERE playlist_title=?"
GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO = f"{GET_ID} playlist_media_list WHERE playlist_id=? AND media_id=? AND list_index=?"
GET_TV_SHOW_ID_FROM_PLAYLIST_ID = f"{GET_ID} tv_show_info WHERE playlist_id=?"
GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX = f"{GET_ID} season_info WHERE tv_show_id=? AND tv_show_season_index=?"
GET_MEDIA_ID_FROM_TITLE_PATH = f"{GET_ID} media_info WHERE media_title=? AND path=?"
GET_MEDIA_ID_FROM_PATH = f"{GET_ID} media_info WHERE path=?"


class DBCreator(DBConnection):

    def __init__(self):
        super().__init__(db_table_creation_list)

    def check_new_content(self, new_tv_folder):
        return collect_new_tv_shows(new_tv_folder)

    def add_tv_show_data(self, media_directory_info, tv_show_list):
        tv_show_ids = {}
        for tv_show in tv_show_list:
            if tv_show_tile := tv_show.get("mp4_show_title"):
                if self.get_row_id(GET_MEDIA_ID_FROM_PATH, (tv_show.get("mp4_file_url"),)):
                    continue
                if playlist_tv_show_id := tv_show_ids.get(tv_show_tile):
                    (playlist_id, tv_show_id) = playlist_tv_show_id
                else:
                    (playlist_id, tv_show_id) = self.add_tv_show(tv_show_tile)

                season_id = self.add_season(tv_show_id, tv_show.get("season_index"))
                media_id = self.add_media(media_directory_info.get("id"), tv_show.get("media_title",
                                                                                      f"Episode {(tv_show.get('episode_index'))}"),
                                          tv_show.get("mp4_file_url"), season_id, tv_show_id)
                list_index = (1000 * tv_show.get("season_index")) + tv_show.get("episode_index")
                self.add_media_to_playlist(playlist_id, media_id, list_index)

    def scan_tv_folder(self, media_directory_info):
        self.add_tv_show_data(media_directory_info, collect_tv_shows(media_directory_info))

    def scan_movie_folder(self, media_directory_info):
        for movie in collect_movies(media_directory_info):
            self.add_media(media_directory_info.get("id"), movie.get("mp4_show_title"), movie.get("mp4_file_url"))

    def scan_media_directory(self, media_directory_info):
        if media_directory_info.get("media_type") == MediaType.TV_SHOW.value:
            self.scan_tv_folder(media_directory_info)
        elif media_directory_info.get("media_type") == MediaType.MOVIE.value:
            self.scan_movie_folder(media_directory_info)
        else:
            print(f"ERROR: Unknown MediaType provided: {media_directory_info.get('media_type')}")

    def scan_all_media_directories(self):
        for media_directory_info in self.get_data_from_db(GET_ALL_MEDIA_DIRECTORIES):
            self.scan_media_directory(media_directory_info)

    def add_media_directory(self, media_directory_info):
        return self.add_data_to_db(sql_insert_media_folder_path_table, (
            media_directory_info.get("media_type"), media_directory_info.get("media_folder_path"),
            media_directory_info.get("new_media_folder_path"), media_directory_info.get("media_folder_url"),))

    def setup_media_directory(self, media_directory_info):
        if media_directory_id := self.add_media_directory(media_directory_info):
            media_directory_info["id"] = media_directory_id
            self.scan_media_directory(media_directory_info)
        return media_directory_id

    def add_playlist(self, playlist_title):
        playlist_id = self.get_row_id(GET_PLAYLIST_ID_FROM_TITLE, (playlist_title,))
        if not playlist_id:
            playlist_id = self.add_data_to_db(sql_insert_playlist_info_table, (playlist_title,))
        return playlist_id

    def add_media_to_playlist(self, playlist_id, media_id, list_index):
        playlist_media_id = self.add_data_to_db(sql_insert_playlist_media_list_table,
                                                (playlist_id, media_id, list_index))
        if not playlist_media_id:
            playlist_media_id = self.get_row_id(GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO,
                                                (playlist_id, media_id, list_index))
        return playlist_media_id

    def add_media(self, media_folder_path_id, media_title, media_path, season_id=None, tv_show_id=None):
        media_id = self.add_data_to_db(sql_insert_media_info_table,
                                       (tv_show_id, season_id, media_folder_path_id, media_title, media_path))
        if not media_id:
            media_id = self.get_row_id(GET_MEDIA_ID_FROM_TITLE_PATH, (media_title, media_path))
        return media_id

    def add_season(self, tv_show_id, tv_show_season_index):
        season_id = self.add_data_to_db(sql_insert_season_info_table, (tv_show_id, tv_show_season_index))
        if not season_id:
            season_id = self.get_row_id(GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX, (tv_show_id, tv_show_season_index))
        return season_id

    def add_tv_show(self, tv_show_title):
        playlist_id = self.add_playlist(tv_show_title)
        tv_show_id = self.add_data_to_db(sql_insert_tv_show_info_table, (playlist_id,))
        if not tv_show_id:
            tv_show_id = self.get_row_id(GET_TV_SHOW_ID_FROM_PLAYLIST_ID, (playlist_id,))
        return playlist_id, tv_show_id
