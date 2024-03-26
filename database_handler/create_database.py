from . import DBConnection
from .common_objects import ContentType
from .media_metadata_collector import collect_tv_shows, collect_movies, get_extra_metadata
from . import common_objects

# playlist_info and media_info are the sources

INSERT_IGNORE = 'INSERT OR IGNORE INTO'

sql_create_playlist_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.PLAYLIST_INFO_TABLE} (
                                    {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                    {common_objects.PLAYLIST_TITLE} text NOT NULL UNIQUE
                                );'''

SET_PLAYLIST_METADATA = f'{INSERT_IGNORE} {common_objects.PLAYLIST_INFO_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.PLAYLIST_TITLE});'

sql_create_playlist_media_list_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.PLAYLIST_MEDIA_LIST_TABLE} (
                                          {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                          {common_objects.PLAYLIST_ID_COLUMN} integer NOT NULL,
                                          {common_objects.MEDIA_ID_COLUMN} integer NOT NULL,
                                          {common_objects.LIST_INDEX_COLUMN} integer NOT NULL,
                                          FOREIGN KEY ({common_objects.MEDIA_ID_COLUMN}) REFERENCES {common_objects.MEDIA_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                          FOREIGN KEY ({common_objects.PLAYLIST_ID_COLUMN}) REFERENCES {common_objects.PLAYLIST_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                          UNIQUE ({common_objects.PLAYLIST_ID_COLUMN}, {common_objects.MEDIA_ID_COLUMN}, {common_objects.LIST_INDEX_COLUMN})
                                       );'''

sql_insert_playlist_media_list_table = f'{INSERT_IGNORE} {common_objects.PLAYLIST_MEDIA_LIST_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.PLAYLIST_ID_COLUMN}, :{common_objects.MEDIA_ID_COLUMN}, :{common_objects.LIST_INDEX_COLUMN});'

sql_create_tv_show_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.TV_SHOW_INFO_TABLE} (
                                   {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                   {common_objects.PLAYLIST_ID_COLUMN} integer NOT NULL UNIQUE,
                                   FOREIGN KEY ({common_objects.PLAYLIST_ID_COLUMN}) REFERENCES {common_objects.PLAYLIST_INFO_TABLE} ({common_objects.ID_COLUMN})
                                );'''

SET_TV_SHOW_METADATA = f'{INSERT_IGNORE} {common_objects.TV_SHOW_INFO_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.PLAYLIST_ID_COLUMN});'

sql_create_season_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.SEASON_INFO_TABLE} (
                                  {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                  {common_objects.TV_SHOW_ID_COLUMN} integer NOT NULL,
                                  {common_objects.SEASON_INDEX_COLUMN} integer NOT NULL,
                                  FOREIGN KEY ({common_objects.TV_SHOW_ID_COLUMN}) REFERENCES {common_objects.TV_SHOW_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                  UNIQUE({common_objects.TV_SHOW_ID_COLUMN}, {common_objects.SEASON_INDEX_COLUMN})
                               );'''

sql_insert_season_info_table = f'{INSERT_IGNORE} {common_objects.SEASON_INFO_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.TV_SHOW_ID_COLUMN}, :{common_objects.SEASON_INDEX_COLUMN});'

sql_create_media_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.MEDIA_INFO_TABLE} (
                                 {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                 {common_objects.TV_SHOW_ID_COLUMN} integer,
                                 {common_objects.SEASON_ID_COLUMN} integer,
                                 {common_objects.MEDIA_DIRECTORY_ID_COLUMN} NOT NULL,
                                 {common_objects.MEDIA_TITLE_COLUMN} text NOT NULL,
                                 {common_objects.PATH_COLUMN} text NOT NULL UNIQUE,
                                 {common_objects.MD5SUM_COLUMN} text UNIQUE,
                                 {common_objects.DURATION_COLUMN} integer,
                                 {common_objects.PLAY_COUNT} integer DEFAULT 0,
                                 FOREIGN KEY ({common_objects.TV_SHOW_ID_COLUMN}) REFERENCES {common_objects.TV_SHOW_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                 FOREIGN KEY ({common_objects.SEASON_ID_COLUMN}) REFERENCES {common_objects.SEASON_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                 FOREIGN KEY ({common_objects.MEDIA_DIRECTORY_ID_COLUMN}) REFERENCES {common_objects.MEDIA_DIRECTORY_ID_COLUMN} ({common_objects.ID_COLUMN}),
                                 UNIQUE({common_objects.MEDIA_DIRECTORY_ID_COLUMN}, {common_objects.MEDIA_TITLE_COLUMN}, {common_objects.PATH_COLUMN})
                              );'''

sql_insert_media_info_table = f'{INSERT_IGNORE} {common_objects.MEDIA_INFO_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.TV_SHOW_ID_COLUMN}, :{common_objects.SEASON_ID_COLUMN}, :{common_objects.MEDIA_DIRECTORY_ID_COLUMN}, :{common_objects.MEDIA_TITLE_COLUMN}, :{common_objects.PATH_COLUMN}, :{common_objects.MD5SUM_COLUMN}, :{common_objects.DURATION_COLUMN}, 0);'

sql_create_media_folder_path_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.MEDIA_DIRECTORY_TABLE} (
                                        {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                        {common_objects.MEDIA_TYPE_COLUMN} integer NOT NULL,
                                        {common_objects.MEDIA_DIRECTORY_PATH_COLUMN} text NOT NULL UNIQUE,
                                        {common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN} text,
                                        {common_objects.MEDIA_DIRECTORY_URL_COLUMN} text NOT NULL UNIQUE
                                     );'''

sql_insert_media_folder_path_table = f'{INSERT_IGNORE} {common_objects.MEDIA_DIRECTORY_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.MEDIA_TYPE_COLUMN}, :{common_objects.MEDIA_DIRECTORY_PATH_COLUMN}, :{common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN}, :{common_objects.MEDIA_DIRECTORY_URL_COLUMN});'

# Get row ID's from various contents
GET_ID = f'SELECT {common_objects.ID_COLUMN} FROM '
GET_PLAYLIST_ID_FROM_TITLE = f'{GET_ID} {common_objects.PLAYLIST_INFO_TABLE} WHERE {common_objects.PLAYLIST_TITLE}=:{common_objects.PLAYLIST_TITLE};'
GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO = f'{GET_ID} {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN}=:{common_objects.PLAYLIST_ID_COLUMN} AND {common_objects.MEDIA_ID_COLUMN}=:{common_objects.MEDIA_ID_COLUMN} AND {common_objects.LIST_INDEX_COLUMN}=:{common_objects.LIST_INDEX_COLUMN};'
GET_TV_SHOW_ID_FROM_PLAYLIST_ID = f'{GET_ID} {common_objects.TV_SHOW_INFO_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN}=:{common_objects.PLAYLIST_ID_COLUMN};'
GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX = f'{GET_ID} {common_objects.SEASON_INFO_TABLE} WHERE {common_objects.TV_SHOW_ID_COLUMN}=:{common_objects.TV_SHOW_ID_COLUMN} AND {common_objects.SEASON_INDEX_COLUMN}=:{common_objects.SEASON_INDEX_COLUMN};'
GET_MEDIA_ID_FROM_TITLE_PATH = f'{GET_ID} {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.MEDIA_TITLE_COLUMN}=:{common_objects.MEDIA_TITLE_COLUMN} AND {common_objects.PATH_COLUMN}=:{common_objects.PATH_COLUMN};'
GET_MEDIA_ID_FROM_PATH = f'{GET_ID} {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.PATH_COLUMN}=:{common_objects.PATH_COLUMN};'

GET_MEDIA_DIRECTORY_INFO = f'SELECT * FROM {common_objects.MEDIA_DIRECTORY_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_ALL_MEDIA_DIRECTORIES = f'SELECT * FROM {common_objects.MEDIA_DIRECTORY_TABLE};'
GET_PLAYLIST_METADATA = f'SELECT * FROM {common_objects.PLAYLIST_INFO_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_PLAYLIST_LIST_METADATA = f'SELECT * FROM {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_TV_SHOW_METADATA = f'SELECT * FROM {common_objects.TV_SHOW_INFO_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_SEASON_METADATA = f'SELECT * FROM {common_objects.SEASON_INFO_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_MEDIA_METADATA = f'SELECT * FROM {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_MEDIA_METADATA_FROM_MEDIA_FOLDER_PATH_ID = f'SELECT * FROM {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.MEDIA_DIRECTORY_ID_COLUMN}=:{common_objects.MEDIA_DIRECTORY_ID_COLUMN};'


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

    def scan_media_directory(self, media_directory_info):
        if media_directory_info.get(common_objects.MEDIA_TYPE_COLUMN) == ContentType.TV.value:
            self.add_tv_show_data(media_directory_info)
        elif media_directory_info.get(common_objects.MEDIA_TYPE_COLUMN) == ContentType.MOVIE.value:
            self.add_movie_data(media_directory_info)
        else:
            print(f'ERROR: Unknown ContentType provided: {media_directory_info.get(common_objects.MEDIA_TYPE_COLUMN)}')
            print(f'INFO: Supported values {ContentType.list()}')

    def setup_media_directory(self, media_directory_info):
        if media_directory_id := self.set_media_directory_info(media_directory_info):
            media_directory_info[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_directory_id
            self.scan_media_directory(media_directory_info)
        return media_directory_id

    def scan_all_media_directories(self):
        for media_directory_info in self.get_all_media_directory_info():
            media_directory_info[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_directory_info.get(
                common_objects.ID_COLUMN)
            self.scan_media_directory(media_directory_info)

    def add_tv_show_data(self, media_directory_info):
        for tv_show in collect_tv_shows(media_directory_info):
            if tv_show.get(common_objects.PLAYLIST_TITLE):
                if self.get_row_id(GET_MEDIA_ID_FROM_PATH, (tv_show.get(common_objects.PATH_COLUMN),)):
                    continue

                tv_show[common_objects.PLAYLIST_ID_COLUMN] = self.set_playlist_metadata(tv_show)
                if not tv_show.get(common_objects.PLAYLIST_ID_COLUMN):
                    tv_show[common_objects.PLAYLIST_ID_COLUMN] = self.get_playlist_id_from_title(tv_show)

                tv_show[common_objects.TV_SHOW_ID_COLUMN] = self.set_tv_show_metadata(tv_show)
                if not tv_show.get(common_objects.TV_SHOW_ID_COLUMN):
                    tv_show[common_objects.TV_SHOW_ID_COLUMN] = self.get_tv_show_id_from_playlist_id(tv_show)

                tv_show[common_objects.SEASON_ID_COLUMN] = self.set_season_metadata(tv_show)
                if not tv_show.get(common_objects.SEASON_ID_COLUMN):
                    tv_show[common_objects.SEASON_ID_COLUMN] = self.get_season_id_from_tv_show_id_season_index(tv_show)

                if tv_show.get("full_file_path"):
                    get_extra_metadata(tv_show, title=True)

                tv_show[common_objects.MEDIA_ID_COLUMN] = self.set_media_metadata(tv_show)
                if tv_show.get(common_objects.MEDIA_ID_COLUMN):
                    self.add_media_to_playlist(tv_show)

    def add_movie_data(self, media_directory_info):
        for movie in collect_movies(media_directory_info):
            movie[common_objects.TV_SHOW_ID_COLUMN] = None
            movie[common_objects.SEASON_ID_COLUMN] = None
            if movie.get("full_file_path"):
                get_extra_metadata(movie, title=True)
            self.set_media_metadata(movie)

    def set_media_directory_info(self, media_directory_info) -> int:
        return self.add_data_to_db(sql_insert_media_folder_path_table, media_directory_info)

    def get_media_directory_info(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_DIRECTORY_INFO, {common_objects.ID_COLUMN: item_id})

    def get_all_media_directory_info(self):
        return self.get_data_from_db(GET_ALL_MEDIA_DIRECTORIES)

    def set_playlist_metadata(self, playlist_metadata) -> int:
        return self.add_data_to_db(SET_PLAYLIST_METADATA, playlist_metadata)

    def get_playlist_metadata(self, item_id: int) -> dict:
        return self.get_data_from_db_first_result(GET_PLAYLIST_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_playlist_id_from_title(self, playlist_metadata) -> int:
        return self.get_row_id(GET_PLAYLIST_ID_FROM_TITLE, playlist_metadata)

    def set_tv_show_metadata(self, tv_show_metadata) -> int:
        return self.add_data_to_db(SET_TV_SHOW_METADATA, tv_show_metadata)

    def get_tv_show_metadata(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_TV_SHOW_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_tv_show_id_from_playlist_id(self, tv_show_metadata) -> int:
        return self.get_row_id(GET_TV_SHOW_ID_FROM_PLAYLIST_ID, tv_show_metadata)

    def set_season_metadata(self, season_metadata) -> int:
        return self.add_data_to_db(sql_insert_season_info_table, season_metadata)

    def get_season_metadata(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_SEASON_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_season_id_from_tv_show_id_season_index(self, season_metadata) -> int:
        return self.get_row_id(GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX, season_metadata)

    def set_media_metadata(self, media_metadata) -> int:
        return self.add_data_to_db(sql_insert_media_info_table, media_metadata)

    def get_media_metadata(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_media_id_from_media_title_path(self, media_metadata) -> int:
        return self.get_row_id(GET_MEDIA_ID_FROM_TITLE_PATH, media_metadata)

    def get_media_metadata_from_media_folder_path_id(self, media_metadata) -> list[dict]:
        return self.get_data_from_db(GET_MEDIA_METADATA_FROM_MEDIA_FOLDER_PATH_ID, media_metadata)

    def add_media_to_playlist(self, media_metadata) -> int:
        return self.add_data_to_db(sql_insert_playlist_media_list_table, media_metadata)

    def get_playlist_entry(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_PLAYLIST_LIST_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_playlist_id_from_playlist_media_metadata(self, media_metadata) -> int:
        return self.get_row_id(GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO, media_metadata)
