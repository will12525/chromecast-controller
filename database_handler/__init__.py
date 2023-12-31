import sys
import traceback
from contextlib import closing
import sqlite3

from database_handler import common_objects
from database_handler.common_objects import DBType


class DBConnection:
    VERSION = 1
    MEDIA_METADATA_DB_NAME = 'media_metadata.db'

    __sql_create_version_info_table = f'''CREATE TABLE IF NOT EXISTS version_info (
                                         {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                         version integer NOT NULL
                                      );'''
    __version_table_creation_script = ''.join(['BEGIN;', __sql_create_version_info_table, 'COMMIT;'])
    __sql_insert_version_info_table = 'INSERT INTO version_info(version) VALUES(?)'
    __version_info_query = 'SELECT * FROM version_info;'

    connection = None
    db_type = None

    def __init__(self, db_type=DBType.PHYSICAL):
        self.db_type = db_type

    def __enter__(self):
        try:
            if self.db_type == DBType.PHYSICAL:
                self.connection = sqlite3.connect(self.MEDIA_METADATA_DB_NAME)
            elif self.db_type == DBType.MEMORY:
                self.connection = sqlite3.connect(':memory:')
            else:
                print(f"Unknown DBType provided: {self.db_type}")

            if self.connection:
                self.connection.row_factory = sqlite3.Row
            # print(f"SqlLite version: {sqlite3.version}")
        except sqlite3.Error as e:
            print(f"Connection error: {e}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        if self.connection:
            self.connection.close()

    def print_db_traceback(self, error, message):
        return
        print('-------SQLite error: %s-------' % (' '.join(error.args)))
        print("Exception class is: ", error.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(message)

    def get_last_row_id(self, cursor) -> int:
        if cursor.rowcount > 0:
            return cursor.lastrowid

    def get_data_list(self, cursor) -> list[dict]:
        return [dict(row) for row in cursor.fetchall()]

    def execute_db_query(self, query, return_func, params=()):
        if sqlite3.complete_statement(query):
            with closing(self.connection.cursor()) as cursor:
                try:
                    cursor.execute(query, params)
                    self.connection.commit()
                    return return_func(cursor)
                except sqlite3.Error as error:
                    self.print_db_traceback(error, f"Error: Query: {query} Params: {params}")
                    return []

    def create_tables(self, db_table_creation_script):
        if sqlite3.complete_statement(db_table_creation_script):
            with closing(self.connection.cursor()) as cursor:
                try:
                    cursor.executescript(db_table_creation_script)
                    self.connection.commit()
                    return self.get_last_row_id(cursor)
                except sqlite3.Error as error:
                    self.print_db_traceback(error, f"Error creating tables:\n{db_table_creation_script}")

    def add_data_to_db(self, query, params):
        return self.execute_db_query(query, self.get_last_row_id, params)

    def get_data_from_db(self, query, params=()):
        return self.execute_db_query(query, self.get_data_list, params)

    def get_data_from_db_first_result(self, query, params=()) -> dict:
        if query_result := self.get_data_from_db(query, params):
            return query_result[0]
        return {}

    def get_row_item(self, query: str, params, item: str):
        return self.get_data_from_db_first_result(query, params).get(item)

    def get_row_id(self, query: str, params: tuple):
        return self.get_row_item(query, params, common_objects.ID_COLUMN)

    def check_db_version(self):
        if not (version := self.get_row_item(self.__version_info_query, (), 'version')):
            self.create_tables(self.__version_table_creation_script)
            self.execute_db_query(self.__sql_insert_version_info_table, self.get_last_row_id, (self.VERSION,))
            version = self.VERSION
        return version
