import time
from unittest import TestCase
import os
from database_handler.create_database import MediaType, SqliteDatabaseHandler


class TestDatabaseHandler(TestCase):
    SERVER_URL_TV_SHOWS = "http://192.168.1.200:8000/tv_shows/"
    MEDIA_FOLDER_PATH = "../media_folder_sample/"
    DB_PATH = "media_metadata.db"

    def setUp(self) -> None:
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)
        time.sleep(5)
        media_paths = [{"type": MediaType.TV_SHOW, "path": self.MEDIA_FOLDER_PATH, "address": self.MEDIA_FOLDER_PATH}]
        SqliteDatabaseHandler(media_paths)


class TestDatabaseHandlerFunctions(TestDatabaseHandler):

    def test_get_url(self):
        db_handler = SqliteDatabaseHandler()
        pass
