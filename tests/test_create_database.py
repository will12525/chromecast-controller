import json
import os
from pathlib import Path
# from unittest import TestCase
# from pyfakefs import fake_filesystem_unittest
from pyfakefs.fake_filesystem_unittest import TestCase

import config_file_handler
from database_handler import common_objects
from database_handler.common_objects import DBType
from database_handler.db_setter import DBCreatorV2
from database_handler.media_metadata_collector import get_playlist_list_index
from . import pytest_mocks

book_1 = "books/Dinosaur Rawr - another author.mp4"
book_1_image = "books/Dinosaur Rawr - another author.mp4.jpg"
book_2 = "books/This is a book title - I'm an author.mp4"
book_paths = [book_1, book_1_image, book_2]

movie_1 = "movies/Vampire (2020).mp4"
movie_1_image = "movies/Vampire (2020).mp4.jpg"
movie_2 = "movies/Vampire 2(2022).mp4"
movie_3 = "movies/The Cat Returns (2002).mp4"
movie_paths = [movie_1, movie_1_image, movie_1, movie_2, movie_3]

tv_1_image = "tv_show/Vampire/Vampire.jpg"
tv_1_s1_image = "tv_show/Vampire/Vampire - s01e001.mp4.jpg"
tv_1_s1_e1 = "tv_show/Vampire/Vampire - s01e001.mp4"
tv_1_s1_e1_image = "tv_show/Vampire/Vampire - s01e001.mp4.jpg"
tv_1_s1_e2 = "tv_show/Vampire/Vampire - s01e002.mp4"
tv_1_s2_e1 = "tv_show/Vampire/Vampire - s02e1.mp4"
tv_1_s2_e2 = "tv_show/Vampire/Vampire - s02e2.mp4"
tv_1_s2_e3 = "tv_show/Vampire/Vampire - s02e3.mp4"

tv_2_s1_e1 = "tv_show/Werewolf/Werewolf - s01e001.mp4"
tv_2_s1_e2 = "tv_show/Werewolf/Werewolf - s01e2.mp4"
tv_2_s1_e3 = "tv_show/Werewolf/Werewolf - s01e3.mp4"
tv_2_s2_e2 = "tv_show/Werewolf/Werewolf - s02e002.mp4"
tv_2_s3_e1 = "tv_show/Werewolf/Werewolf - s03e1.mp4"

tv_3_image = "tv_show/Vans/Vans.png"
tv_3_s2_e1 = "tv_show/Vans/Vans - s02e001.mp4"
tv_3_s2_e2 = "tv_show/Vans/Vans - s02e2.mp4"
tv_show_paths = [tv_1_image, tv_1_s1_image, tv_1_s1_e1, tv_1_s1_e1_image, tv_1_s1_e2, tv_1_s2_e1, tv_1_s2_e2,
                 tv_1_s2_e3, tv_2_s1_e1, tv_2_s1_e2, tv_2_s1_e3, tv_2_s2_e2, tv_2_s3_e1, tv_3_image, tv_3_s2_e1,
                 tv_3_s2_e2]


class TestDBCreatorInit(TestCase):
    DB_PATH = Path("media_metadata.db")

    def setUp(self) -> None:
        # self.setUpPyfakefs(allow_root_user=False)
        pytest_mocks.patch_get_file_hash(self)
        pytest_mocks.patch_get_ffmpeg_metadata(self)
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)
        pytest_mocks.patch_load_json_file_content(self)

    def erase_db(self):
        if self.DB_PATH.exists():
            self.DB_PATH.unlink()
        assert not self.DB_PATH.exists()


class TestDBCreator(TestDBCreatorInit):

    def test_create_file(self):
        """Test example.create_file() which uses `open()`
        and `file.write()`.
        """
        self.assertFalse(os.path.isdir("/test"))
        os.mkdir("/test")
        self.assertTrue(os.path.isdir("/test"))

        self.assertFalse(os.path.exists("/test/file.txt"))
        Path("/test/file.txt").touch()
        self.assertTrue(os.path.exists("/test/file.txt"))

    def test_create_db_memory(self):
        self.erase_db()
        with DBCreatorV2(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            assert db_setter_connection.VERSION == db_setter_connection.check_db_version()
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('version_info');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('content_directory');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('container');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('content');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('container_content');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('container_container');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('user_tags');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('user_tags_content');")
        assert not self.DB_PATH.exists()

    def test_create_db_physical(self):
        self.erase_db()
        with DBCreatorV2(DBType.PHYSICAL) as db_setter_connection:
            db_setter_connection.create_db()
            assert db_setter_connection.VERSION == db_setter_connection.check_db_version()
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('version_info');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('content_directory');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('container');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('content');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('container_content');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('container_container');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('user_tags');")
            assert db_setter_connection.get_data_from_db("PRAGMA table_info('user_tags_content');")
        assert self.DB_PATH.exists()

    def test_add_content_directory_info(self):
        config_file_data = config_file_handler.load_json_file_content()
        with DBCreatorV2(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            for media_folder in config_file_data.get("media_folders"):
                assert db_setter_connection.add_media_folder(media_folder)
                db_media_folder = db_setter_connection.get_media_folder_info_by_id(media_folder.get("id"))
                assert media_folder == db_media_folder

    def test_scan_media_metadata_v2(self):
        self.erase_db()
        with DBCreatorV2(DBType.PHYSICAL) as db_setter_connection:
            db_setter_connection.create_db()

            if self.media_folders:
                for media_path in self.media_folders:
                    # print(media_path)
                    db_setter_connection.setup_content_directory(media_path)

            db_setter_connection.scan_content_directories()
