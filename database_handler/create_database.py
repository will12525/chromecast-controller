import os
import traceback
import sys
import sqlite3
from sqlite3 import Error
from enum import Enum, auto
from .media_metadata_collector import collect_tv_shows, collect_movies

# playlist_info and media_info are the sources

VERSION = 1
MEDIA_METADATA_DB_NAME = r"media_metadata.db"

sql_create_tv_show_info_table = """CREATE TABLE IF NOT EXISTS tv_show_info (
                                id integer PRIMARY KEY,
                                playlist_id integer NOT NULL UNIQUE,
                                FOREIGN KEY (playlist_id) REFERENCES playlist_info (id)
                            );"""

sql_insert_tv_show_info_table = ''' INSERT INTO tv_show_info(playlist_id) VALUES(?) '''

sql_create_season_info_table = """CREATE TABLE IF NOT EXISTS season_info (
                                id integer PRIMARY KEY,
                                tv_show_id integer NOT NULL,
                                start_list_index integer,
                                end_list_index integer,
                                name text NOT NULL,
                                list_index integer NOT NULL,
                                FOREIGN KEY (tv_show_id) REFERENCES tv_show_info (id),
                                FOREIGN KEY (start_list_index) REFERENCES playlist_media_list (list_index),
                                FOREIGN KEY (end_list_index) REFERENCES playlist_media_list (list_index)
                            );"""

sql_insert_season_info_table = ''' INSERT INTO season_info(tv_show_id, start_list_index, end_list_index, name, list_index) VALUES(?, ?, ?, ?, ?) '''

sql_create_media_info_table = """CREATE TABLE IF NOT EXISTS media_info (
                                id integer PRIMARY KEY,
                                season_id integer,
                                tv_show_id integer,
                                name text NOT NULL,
                                media_folder_path_id, 
                                path text NOT NULL,
                                FOREIGN KEY (season_id) REFERENCES season_info (id),
                                FOREIGN KEY (tv_show_id) REFERENCES tv_show_info (id)
                                FOREIGN KEY (media_folder_path_id) REFERENCES media_folder_path_id (id)
                            );"""

sql_insert_media_info_table = ''' INSERT INTO media_info(season_id, tv_show_id, name, media_folder_path_id, path) VALUES(?, ?, ?, ?, ?) '''

sql_create_playlist_info_table = """CREATE TABLE IF NOT EXISTS playlist_info (
                                id integer PRIMARY KEY,
                                name text NOT NULL UNIQUE
                                );"""

sql_insert_playlist_info_table = ''' INSERT INTO playlist_info(name) VALUES(?) '''

sql_create_playlist_media_list_table = """CREATE TABLE IF NOT EXISTS playlist_media_list (
                                id integer PRIMARY KEY,
                                playlist_id integer NOT NULL,
                                media_id integer NOT NULL,
                                list_index integer NOT NULL,
                                FOREIGN KEY (media_id) REFERENCES media_info (id),
                                FOREIGN KEY (playlist_id) REFERENCES playlist_info (id)
                            );"""

sql_insert_playlist_media_list_table = ''' INSERT INTO playlist_media_list(playlist_id, media_id, list_index) VALUES(?, ?, ?) '''

sql_create_media_folder_path_table = """CREATE TABLE IF NOT EXISTS media_folder_path (
                                id integer PRIMARY KEY,
                                media_type integer NOT NULL,
                                media_folder_path text NOT NULL,
                                media_folder_url text NOT NULL
                            );"""

sql_insert_media_folder_path_table = ''' INSERT INTO media_folder_path(media_type, media_folder_path, media_folder_url) VALUES(?, ?, ?) '''

db_table_creation_list = [sql_create_tv_show_info_table, sql_create_season_info_table, sql_create_media_info_table,
                          sql_create_playlist_info_table, sql_create_playlist_media_list_table,
                          sql_create_media_folder_path_table]


class MediaType(Enum):
    TV_SHOW = auto()
    MOVIE = auto()


class SqliteDatabaseHandler:
    db_connection = None

    def __init__(self, media_paths=None):
        if not os.path.exists(MEDIA_METADATA_DB_NAME):
            self.create_connection(MEDIA_METADATA_DB_NAME)
            self.create_tables(db_table_creation_list)
            if media_paths:
                for media_path in media_paths:
                    self.populate_db(media_path)
        else:
            self.create_connection(MEDIA_METADATA_DB_NAME)

    def __del__(self):
        self.close()

    def close(self):
        if self.db_connection:
            self.db_connection.close()

    def create_connection(self, db_file):
        """ create a database connection to a SQLite database """
        if not self.db_connection:
            try:
                self.db_connection = sqlite3.connect(db_file)
                self.db_connection.row_factory = sqlite3.Row
                print(f"SqlLite version: {sqlite3.version}")
            except Error as e:
                print(f"Connection error: {e}")

    def create_table(self, create_table_sql):
        """ create a table from the create_table_sql statement
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        c = None
        if self.db_connection:
            try:
                c = self.db_connection.cursor()
                c.execute(create_table_sql)
            except Error as e:
                print(f"Error creating table:\n{create_table_sql}")
                print(e)
            finally:
                if c:
                    c.close()

    def create_tables(self, create_table_sql_list):
        """ create a table from the create_table_sql statement
        :param create_table_sql_list: a CREATE TABLE statement
        :return:
        """
        for table in create_table_sql_list:
            self.create_table(table)

    def add_data_to_db(self, query, params):
        cur = None
        if self.db_connection:
            try:
                cur = self.db_connection.cursor()
                cur.execute(query, params)
                self.db_connection.commit()
                return cur.lastrowid
            except sqlite3.Error as er:
                print('SQLite error: %s' % (' '.join(er.args)))
                print("Exception class is: ", er.__class__)
                print('SQLite traceback: ')
                exc_type, exc_value, exc_tb = sys.exc_info()
                print(traceback.format_exception(exc_type, exc_value, exc_tb))
                print(f"Query: {query}\nParams: {params}")
            finally:
                if cur:
                    cur.close()

    def get_data_from_db(self, query, params=()):
        c = None
        if self.db_connection:
            try:
                c = self.db_connection.cursor()
                c.execute(query, params)
                query_result = c.fetchall()
                query_result_dict_list = []
                for result in query_result:
                    query_result_dict_list.append(dict(result))
                return query_result_dict_list
            except Error as e:
                print(f"Error querying db:\n{query}")
                print(e)
            finally:
                if c:
                    c.close()

    def populate_db(self, media_path):
        media_folder_path_id = self.add_media_folder_path(media_path)
        if media_path.get("type") == MediaType.TV_SHOW:
            collect_tv_shows(self, media_folder_path_id, media_path.get("path"))
        elif media_path.get("type") == MediaType.MOVIE:
            movie_list = collect_movies(media_path.get("path"))
            for movie in movie_list:
                self.add_media(movie.get("title"), media_folder_path_id, movie.get("path"))
        else:
            print(f"Unknown media type: {media_path.get('type')}")

    def add_playlist(self, name):
        return self.add_data_to_db(sql_insert_playlist_info_table, (name,))

    def add_media_folder_path(self, media_folder_path_info):
        return self.add_data_to_db(sql_insert_media_folder_path_table, (
            media_folder_path_info.get("type").value, media_folder_path_info.get("path"),
            media_folder_path_info.get("url"),))

    def update_playlist_end_season_index(self, season_info_id, list_index):
        sql = ''' UPDATE season_info SET end_list_index = ? WHERE id = ?'''
        self.add_data_to_db(sql, (list_index, season_info_id))

    def add_media_to_playlist(self, playlist_id, season_info_id, media_id):
        list_index = self.get_playlist_end_index(playlist_id) + 1
        self.update_playlist_end_season_index(season_info_id, list_index)
        return self.add_data_to_db(sql_insert_playlist_media_list_table, (playlist_id, media_id, list_index))

    def add_media(self, media_name, media_folder_path_id, media_path, season_id=None, tv_show_id=None):
        return self.add_data_to_db(sql_insert_media_info_table,
                                   (season_id, tv_show_id, media_name, media_folder_path_id, media_path))

    def add_season(self, playlist_id, tv_show_id, season_name, end_list_index=None, list_index=None):
        start_list_index = self.get_playlist_end_index(playlist_id) + 1
        return self.add_data_to_db(sql_insert_season_info_table,
                                   (tv_show_id, start_list_index, end_list_index, season_name, list_index))

    def add_tv_show(self, tv_show_dir_name):
        playlist_id = self.add_playlist(tv_show_dir_name)
        return playlist_id, self.add_data_to_db(sql_insert_tv_show_info_table, (playlist_id,))

    def get_playlist_end_index(self, playlist_id):
        query = "SELECT list_index FROM playlist_media_list WHERE playlist_id=? ORDER BY list_index DESC LIMIT 1"
        playlist_rows = self.get_data_from_db(query, (playlist_id,))
        if playlist_rows:
            if playlist_row := playlist_rows[0]:
                return playlist_row.get("list_index")
        return 0
