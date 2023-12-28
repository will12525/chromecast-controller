from enum import Enum, auto
import sqlite3


class MediaType(Enum):
    TV_SHOW = auto()
    MOVIE = auto()


class DBConnection:
    VERSION = 1
    MEDIA_METADATA_DB_NAME = 'media_metadata.db'
    __db_connection = None
    __sql_create_version_info_table = '''CREATE TABLE IF NOT EXISTS version_info (
                                         id integer PRIMARY KEY,
                                         version integer NOT NULL
                                      );'''

    __sql_insert_version_info_table = 'INSERT INTO version_info(version) VALUES(?)'
    __version_info_query = 'SELECT * FROM version_info;'

    def __init__(self, table_list=None):
        self.__validate_db(table_list)

    def __del__(self):
        self.close()

    def close(self):
        if self.__db_connection:
            self.__db_connection.close()

    def __connect_db(self):
        """ create a database connection to a SQLite database """
        if not self.__db_connection:
            try:
                self.__db_connection = sqlite3.connect(self.MEDIA_METADATA_DB_NAME)
                self.__db_connection.row_factory = sqlite3.Row
                # print(f"SqlLite version: {sqlite3.version}")
            except sqlite3.Error as e:
                print(f"Connection error: {e}")
        return self.__db_connection

    def __create_table(self, create_table_sql):
        """ create a table from the create_table_sql statement
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        c = None
        if db_connection := self.__connect_db():
            try:
                c = db_connection.cursor()
                if sqlite3.complete_statement(create_table_sql):
                    c.execute(create_table_sql)
            except sqlite3.Error as e:
                print(f"Error creating table:\n{create_table_sql}")
                print(e)
            finally:
                if c:
                    c.close()

    def __create_tables(self, create_table_sql_list):
        """ create a table from the create_table_sql statement
        :param create_table_sql_list: a CREATE TABLE statement
        :return:
        """
        for table in create_table_sql_list:
            self.__create_table(table)

    def add_data_to_db(self, query, params):
        cur = None
        if db_connection := self.__connect_db():
            try:
                cur = db_connection.cursor()
                cur.execute(query, params)
                db_connection.commit()
                return cur.lastrowid
            except sqlite3.Error as er:
                pass
                # print('SQLite error: %s' % (' '.join(er.args)))
                # print("Exception class is: ", er.__class__)
                # print('SQLite traceback: ')
                # exc_type, exc_value, exc_tb = sys.exc_info()
                # print(traceback.format_exception(exc_type, exc_value, exc_tb))
                # print(f"Error: Query: {query} Params: {params}")
                # print()
            finally:
                if cur:
                    cur.close()

    def get_data_from_db(self, query, params=()):
        c = None
        if db_connection := self.__connect_db():
            try:
                c = db_connection.cursor()
                c.execute(query, params)
                query_result = c.fetchall()
                query_result_dict_list = []
                for result in query_result:
                    query_result_dict_list.append(dict(result))
                return query_result_dict_list
            except sqlite3.Error as e:
                print(f"Error querying db:\n{query}")
                print(e)
                return []
            finally:
                if c:
                    c.close()

    def get_data_from_db_first_result(self, query, params=()) -> dict:
        if query_result := self.get_data_from_db(query, params):
            return query_result[0]
        return {}

    def get_row_item(self, query: str, params: tuple, item: str):
        return self.get_data_from_db_first_result(query, params).get(item)

    def get_row_id(self, query: str, params: tuple):
        return self.get_row_item(query, params, "id")

    def __set_version(self, version):
        return self.add_data_to_db(self.__sql_insert_version_info_table, (version,))

    def __validate_db(self, table_list=None):
        if not self.get_data_from_db(self.__version_info_query):
            self.__create_table(self.__sql_create_version_info_table)
            self.__set_version(self.VERSION)
        if table_list:
            self.__create_tables(table_list)
