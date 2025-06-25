import sys
import traceback
import sqlite3
from enum import Enum, auto

import app.database.db_queries as queries


class DBType(Enum):
    PHYSICAL = auto()
    MEMORY = auto()


def print_db_traceback(error, message):
    # return
    print("-------SQLite error: %s-------" % (" ".join(error.args)))
    print("Exception class is: ", error.__class__)
    print("SQLite traceback: ")
    exc_type, exc_value, exc_tb = sys.exc_info()
    print(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(message)


class DBConnection:
    VERSION = 1
    DB_FILE_NAME = "media_metadata.db"

    connection = None
    db_type = None

    def __init__(self, db_type=DBType.PHYSICAL, file_name=None):
        self.db_type = db_type
        if file_name:
            self.DB_FILE_NAME = file_name

    def open(self):
        try:
            if self.db_type == DBType.PHYSICAL:
                self.connection = sqlite3.connect(self.DB_FILE_NAME)
            elif self.db_type == DBType.MEMORY:
                self.connection = sqlite3.connect(":memory:")
            else:
                print(f"Unknown DBType provided: {self.db_type}")

            if self.connection:
                self.connection.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Connection error: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        if self.connection:
            self.connection.close()

    def execute_db_query(self, query, cursor, params=()):
        if sqlite3.complete_statement(query):
            try:
                cursor.execute(query, params)
                self.connection.commit()
            except sqlite3.Error as error:
                print_db_traceback(error, f"Error: Query: {query} Params: {params}")

    def execute_db_script(self, db_script_lines: list):
        ret_val = 0
        db_script_lines.insert(0, "BEGIN;")
        db_script_lines.append("COMMIT;")
        db_script = "".join(db_script_lines)
        if sqlite3.complete_statement(db_script):
            cursor = self.connection.cursor()
            try:
                cursor.executescript(db_script)
                self.connection.commit()
                if cursor.rowcount > 0:
                    ret_val = cursor.lastrowid
            except sqlite3.Error as error:
                print_db_traceback(error, f"Error creating tables:\n{db_script}")
            cursor.close()
            return ret_val

    def add_data_to_db(self, query, params):
        ret_val = None
        cursor = self.connection.cursor()
        self.execute_db_query(query, cursor, params)
        if cursor.rowcount > 0:
            ret_val = cursor.lastrowid
        cursor.close()
        return ret_val

    def get_data_from_db(self, query, params=()):
        cursor = self.connection.cursor()
        self.execute_db_query(query, cursor, params)
        ret_val = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return ret_val

    def get_data_from_db_first_result(self, query, params=()) -> dict:
        if query_result := self.get_data_from_db(query, params):
            return query_result[0]
        return {}

    def get_row_item(self, query: str, params, item: str):
        return self.get_data_from_db_first_result(query, params).get(item)

    def get_row_id(self, query: str, params):
        return self.get_row_item(query, params, "id")

    def check_db_version(self):
        if not (
                version := self.get_data_from_db_first_result(queries.version_info_query)
        ):
            self.execute_db_script([queries.sql_create_version_info_table])
            self.add_data_to_db(
                queries.sql_insert_version_info_table, {"version_info": self.VERSION}
            )
            print(
                f"Version: {self.get_data_from_db_first_result(queries.version_info_query)}"
            )
            version = self.VERSION
        return version
