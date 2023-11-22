import os
import traceback
import sys
import sqlite3
from sqlite3 import Error
from .media_metadata_collector import collect_tv_shows

# playlist_info and media_info are the sources

VERSION = 1
MEDIA_METADATA_DB_NAME = r"media_metadata.db"

sql_create_tv_show_info_table = """CREATE TABLE IF NOT EXISTS tv_show_info (
                                id integer PRIMARY KEY,
                                playlist_id integer NOT NULL,
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
                                path text NOT NULL,
                                FOREIGN KEY (season_id) REFERENCES season_info (id),
                                FOREIGN KEY (tv_show_id) REFERENCES tv_show_info (id)
                            );"""

sql_insert_media_info_table = ''' INSERT INTO media_info(season_id, tv_show_id, name, path) VALUES(?, ?, ?, ?) '''

sql_create_playlist_info_table = """CREATE TABLE IF NOT EXISTS playlist_info (
                                id integer PRIMARY KEY,
                                name text NOT NULL
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

sql_create_media_folder_table = """CREATE TABLE IF NOT EXISTS media_folder (
                                id integer PRIMARY KEY,
                                media_folder_path integer NOT NULL
                            );"""

sql_insert_media_folder_table = ''' INSERT INTO media_folder(media_folder_path) VALUES(?) '''

db_table_creation_list = [sql_create_tv_show_info_table, sql_create_season_info_table, sql_create_media_info_table,
                          sql_create_playlist_info_table, sql_create_playlist_media_list_table,
                          sql_create_media_folder_table]


class SqliteDatabaseHandler:
    db_connection = None

    def __init__(self, media_scan_path=None):
        if not os.path.exists(MEDIA_METADATA_DB_NAME):
            self.create_connection(MEDIA_METADATA_DB_NAME)
            self.create_tables(db_table_creation_list)
            if media_scan_path:
                self.populate_db(media_scan_path)
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
                print(f"SqlLite version: {sqlite3.version}")
            except Error as e:
                print(e)

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
            finally:
                if cur:
                    cur.close()

    def get_data_from_db(self, query, params=()):
        c = None
        if self.db_connection:
            try:
                c = self.db_connection.cursor()
                c.execute(query, params)
                return c.fetchall()
            except Error as e:
                print(f"Error querying db:\n{query}")
                print(e)
            finally:
                if c:
                    c.close()

    def populate_db(self, path):
        collect_tv_shows(self, path)

    def add_playlist(self, name):
        return self.add_data_to_db(sql_insert_playlist_info_table, (name,))

    def add_media_folder_path(self, media_folder_path):
        return self.add_data_to_db(sql_insert_media_folder_table, (media_folder_path,))

    def add_media_to_playlist(self, playlist_id, media_id, list_index=None):
        if not list_index:
            list_index = self.get_playlist_end_index(playlist_id) + 1
        return self.add_data_to_db(sql_insert_playlist_media_list_table, (playlist_id, media_id, list_index))

    def add_media(self, media_name, media_path, season_id=None, tv_show_id=None):
        return self.add_data_to_db(sql_insert_media_info_table, (season_id, tv_show_id, media_name, media_path))

    def add_season(self, tv_show_id, season_name, start_list_index=None, end_list_index=None, list_index=None):
        return self.add_data_to_db(sql_insert_season_info_table,
                                   (tv_show_id, start_list_index, end_list_index, season_name, list_index))

    def add_start_end_season_index(self, season_id, start_list_index, end_list_index):
        sql = ''' UPDATE season_info SET start_list_index = ?, end_list_index = ? WHERE id = ?'''
        self.add_data_to_db(sql, (start_list_index, end_list_index, season_id))

    def add_tv_show(self, playlist_id):
        return self.add_data_to_db(sql_insert_tv_show_info_table, (playlist_id,))

    def get_playlist_end_index(self, playlist_id):
        query = "SELECT list_index FROM playlist_media_list WHERE playlist_id=? ORDER BY list_index DESC LIMIT 1"
        playlist_rows = self.get_data_from_db(query, (playlist_id,))
        if playlist_rows:
            if playlist_row := playlist_rows[0]:
                return playlist_row[0]
        return 0
