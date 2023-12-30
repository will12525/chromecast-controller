from . import DBConnection, MediaType
from .database_handler import GET_ALL_MEDIA_DIRECTORIES
from .media_metadata_collector import collect_tv_shows, collect_movies
from . import common_objects

# playlist_info and media_info are the sources


sql_create_playlist_info_table = f'''CREATE TABLE IF NOT EXISTS playlist_info (
                                    id integer PRIMARY KEY,
                                    {common_objects.PLAYLIST_TITLE} text NOT NULL UNIQUE
                                );'''

SET_PLAYLIST_METADATA = f'INSERT OR IGNORE INTO playlist_info VALUES(:id, :{common_objects.PLAYLIST_TITLE});'

sql_create_playlist_media_list_table = '''CREATE TABLE IF NOT EXISTS playlist_media_list (
                                          id integer PRIMARY KEY,
                                          playlist_id integer NOT NULL,
                                          media_id integer NOT NULL,
                                          list_index integer NOT NULL,
                                          FOREIGN KEY (media_id) REFERENCES media_info (id),
                                          FOREIGN KEY (playlist_id) REFERENCES playlist_info (id),
                                          UNIQUE (playlist_id, media_id, list_index)
                                       );'''

sql_insert_playlist_media_list_table = 'INSERT INTO playlist_media_list VALUES(:id, :playlist_id, :media_id, :list_index);'

sql_create_tv_show_info_table = '''CREATE TABLE IF NOT EXISTS tv_show_info (
                                   id integer PRIMARY KEY,
                                   playlist_id integer NOT NULL UNIQUE,
                                   FOREIGN KEY (playlist_id) REFERENCES playlist_info (id)
                                );'''

SET_TV_SHOW_METADATA = 'INSERT INTO tv_show_info VALUES(:id, :playlist_id);'

sql_create_season_info_table = '''CREATE TABLE IF NOT EXISTS season_info (
                                  id integer PRIMARY KEY,
                                  tv_show_id integer NOT NULL,
                                  season_index integer NOT NULL,
                                  FOREIGN KEY (tv_show_id) REFERENCES tv_show_info (id),
                                  UNIQUE(tv_show_id, season_index)
                               );'''

sql_insert_season_info_table = 'INSERT INTO season_info VALUES(:id, :tv_show_id, :season_index);'

sql_create_media_info_table = '''CREATE TABLE IF NOT EXISTS media_info (
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
                              );'''

sql_insert_media_info_table = 'INSERT INTO media_info VALUES(:id, :tv_show_id, :season_id, :media_folder_path_id, :media_title, :path);'

sql_create_media_folder_path_table = '''CREATE TABLE IF NOT EXISTS media_folder_path (
                                        id integer PRIMARY KEY,
                                        media_type integer NOT NULL,
                                        media_folder_path text NOT NULL UNIQUE,
                                        new_media_folder_path text,
                                        media_folder_url text NOT NULL UNIQUE
                                     );'''

sql_insert_media_folder_path_table = 'INSERT INTO media_folder_path VALUES(:id, :media_type, :media_folder_path, :new_media_folder_path, :media_folder_url);'

# Get row ID's from various contents
GET_ID = 'SELECT id FROM '
GET_PLAYLIST_ID_FROM_TITLE = f'{GET_ID} playlist_info WHERE {common_objects.PLAYLIST_TITLE}=:{common_objects.PLAYLIST_TITLE};'
GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO = f'{GET_ID} playlist_media_list WHERE playlist_id=:playlist_id AND media_id=:media_id AND list_index=:list_index;'
GET_TV_SHOW_ID_FROM_PLAYLIST_ID = f'{GET_ID} tv_show_info WHERE playlist_id=:playlist_id;'
GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX = f'{GET_ID} season_info WHERE tv_show_id=:tv_show_id AND season_index=:season_index;'
GET_MEDIA_ID_FROM_TITLE_PATH = f'{GET_ID} media_info WHERE media_title=:media_title AND path=:path;'
GET_MEDIA_ID_FROM_PATH = f'{GET_ID} media_info WHERE path=:path;'

GET_MEDIA_DIRECTORY_INFO = f'SELECT * FROM media_folder_path WHERE id=:id;'
GET_PLAYLIST_METADATA = f'SELECT * FROM playlist_info WHERE id=:id;'
GET_PLAYLIST_LIST_METADATA = f'SELECT * FROM playlist_media_list WHERE id=:id;'
GET_TV_SHOW_METADATA = f'SELECT * FROM tv_show_info WHERE id=:id;'
GET_SEASON_METADATA = f'SELECT * FROM season_info WHERE id=:id;'
GET_MEDIA_METADATA = f'SELECT * FROM media_info WHERE id=:id;'
GET_MEDIA_METADATA_FROM_MEDIA_FOLDER_PATH_ID = f'SELECT * FROM media_info WHERE media_folder_path_id=:media_folder_path_id;'


class DBCreator(DBConnection):

    def create_db(self):
        if self.VERSION != self.check_db_version():
            # Run db update procedure
            pass
        db_table_creation_script = ''.join(['BEGIN;', sql_create_tv_show_info_table, sql_create_season_info_table,
                                            sql_create_media_info_table, sql_create_playlist_info_table,
                                            sql_create_playlist_media_list_table, sql_create_media_folder_path_table,
                                            'COMMIT;'])
        self.create_tables(db_table_creation_script)

    def scan_all_media_directories(self):
        for media_directory_info in self.get_all_media_directory_info():
            self.scan_media_directory(media_directory_info)

    def setup_media_directory(self, media_directory_info):
        if media_directory_id := self.set_media_directory_info(media_directory_info):
            media_directory_info['media_folder_path_id'] = media_directory_id
            self.scan_media_directory(media_directory_info)
        return media_directory_id

    def scan_media_directory(self, media_directory_info):
        if media_directory_info.get('media_type') == MediaType.TV_SHOW.value:
            self.add_tv_show_data(media_directory_info)
        elif media_directory_info.get('media_type') == MediaType.MOVIE.value:
            self.add_movie_data(media_directory_info)
        else:
            print(f"ERROR: Unknown MediaType provided: {media_directory_info.get('media_type')}")

    def add_tv_show_data(self, media_directory_info):
        for tv_show in collect_tv_shows(media_directory_info):
            if tv_show.get(common_objects.PLAYLIST_TITLE):
                if self.get_row_id(GET_MEDIA_ID_FROM_PATH, (tv_show.get('path'),)):
                    continue

                tv_show['playlist_id'] = self.set_playlist_metadata(tv_show)
                if not tv_show.get('playlist_id'):
                    tv_show['playlist_id'] = self.get_playlist_id_from_title(tv_show)

                tv_show['tv_show_id'] = self.set_tv_show_metadata(tv_show)
                if not tv_show.get('tv_show_id'):
                    tv_show['tv_show_id'] = self.get_tv_show_id_from_playlist_id(tv_show)

                tv_show['season_id'] = self.set_season_metadata(tv_show)
                if not tv_show.get('season_id'):
                    tv_show['season_id'] = self.get_season_id_from_tv_show_id_season_index(tv_show)

                tv_show['media_id'] = self.set_media_metadata(tv_show)
                if tv_show.get('media_id'):
                    self.add_media_to_playlist(tv_show)

    def add_movie_data(self, media_directory_info):
        for movie in collect_movies(media_directory_info):
            movie['tv_show_id'] = None
            movie['season_id'] = None
            movie['id'] = None
            movie[common_objects.PLAYLIST_TITLE] = None
            movie['season_index'] = None
            movie['episode_index'] = None
            self.set_media_metadata(movie)

    def set_media_directory_info(self, media_directory_info) -> int:
        return self.add_data_to_db(sql_insert_media_folder_path_table, media_directory_info)

    def get_media_directory_info(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_DIRECTORY_INFO, {'id': item_id})

    def get_all_media_directory_info(self):
        return self.get_data_from_db(GET_ALL_MEDIA_DIRECTORIES)

    def set_playlist_metadata(self, playlist_metadata) -> int:
        return self.add_data_to_db(SET_PLAYLIST_METADATA, playlist_metadata)

    def get_playlist_metadata(self, item_id: int) -> dict:
        return self.get_data_from_db_first_result(GET_PLAYLIST_METADATA, {'id': item_id})

    def get_playlist_id_from_title(self, playlist_metadata) -> int:
        return self.get_row_id(GET_PLAYLIST_ID_FROM_TITLE, playlist_metadata)

    def set_tv_show_metadata(self, tv_show_metadata) -> int:
        return self.add_data_to_db(SET_TV_SHOW_METADATA, tv_show_metadata)

    def get_tv_show_metadata(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_TV_SHOW_METADATA, {'id': item_id})

    def get_tv_show_id_from_playlist_id(self, tv_show_metadata) -> int:
        return self.get_row_id(GET_TV_SHOW_ID_FROM_PLAYLIST_ID, tv_show_metadata)

    def set_season_metadata(self, season_metadata) -> int:
        return self.add_data_to_db(sql_insert_season_info_table, season_metadata)

    def get_season_metadata(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_SEASON_METADATA, {'id': item_id})

    def get_season_id_from_tv_show_id_season_index(self, season_metadata) -> int:
        return self.get_row_id(GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX, season_metadata)

    def set_media_metadata(self, media_metadata) -> int:
        return self.add_data_to_db(sql_insert_media_info_table, media_metadata)

    def get_media_metadata(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_METADATA, {'id': item_id})

    def get_media_id_from_media_title_path(self, media_metadata) -> int:
        return self.get_row_id(GET_MEDIA_ID_FROM_TITLE_PATH, media_metadata)

    def get_media_metadata_from_media_folder_path_id(self, media_metadata) -> list[dict]:
        return self.get_data_from_db(GET_MEDIA_METADATA_FROM_MEDIA_FOLDER_PATH_ID, media_metadata)

    def add_media_to_playlist(self, media_metadata) -> int:
        return self.add_data_to_db(sql_insert_playlist_media_list_table, media_metadata)

    def get_playlist_entry(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_PLAYLIST_LIST_METADATA, {'id': item_id})

    def get_playlist_id_from_playlist_media_metadata(self, media_metadata) -> int:
        return self.get_row_id(GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO, media_metadata)
