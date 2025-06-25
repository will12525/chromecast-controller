import json
import os
from pathlib import Path
from unittest import TestCase

import config_file_handler
from database_handler.common_objects import DBType
from database_handler.db_getter import DBGetter
from database_handler.db_setter import DBSetter
from . import pytest_mocks


class TestDBCreatorInit(TestCase):
    DB_PATH = Path("media_metadata.db")
    config_file_data = config_file_handler.load_json_file_content()

    def setUp(self) -> None:
        self.media_directory_info = config_file_handler.load_json_file_content().get("media_folders")

        pytest_mocks.patch_get_file_hash(self)
        pytest_mocks.patch_get_ffmpeg_metadata(self)
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)
        # pytest_mocks.patch_load_json_file_content(self)

    def erase_db(self):
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)

    def setup_content_directory(self):
        self.erase_db()
        with DBSetter(DBType.PHYSICAL) as db_setter_connection:
            db_setter_connection.create_db()
            for media_folder in self.config_file_data.get("media_folders"):
                db_setter_connection.setup_content_directory(media_folder)
            assert len(db_setter_connection.get_all_content_directory_info()) == 2


class TestDBCreator(TestDBCreatorInit):

    def test_create_db_memory(self):
        self.erase_db()
        with DBSetter(DBType.MEMORY) as db_setter_connection:
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
        with DBSetter(DBType.PHYSICAL) as db_setter_connection:
            db_setter_connection.create_db()


    def test_add_media_folder(self):
        with DBSetter(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            for media_folder in self.config_file_data.get("media_folders"):
                assert db_setter_connection.add_media_folder(media_folder)
                db_media_folder = db_setter_connection.get_media_folder_info_by_id(media_folder.get("id"))
                assert media_folder == db_media_folder

    def test_add_content_directory_info(self):
        config_file_data = config_file_handler.load_json_file_content()
        with DBSetter(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            for media_folder in config_file_data.get("media_folders"):
                assert db_setter_connection.add_media_folder(media_folder)
                db_media_folder = db_setter_connection.get_media_folder_info_by_id(media_folder.get("id"))
                assert media_folder == db_media_folder

            db_media_folders = db_setter_connection.get_all_content_directory_info()
            assert len(db_media_folders) == 2

    def test_setup_content_directory(self):
        self.setup_content_directory()

    def test_collect_directory_content(self):
        self.setup_content_directory()
        with DBGetter(DBType.PHYSICAL) as db_getter_connection:
            db_content = db_getter_connection.query_db(None, {}, None, None)
            assert len(db_content.get("containers")) >= 0
            assert len(db_content.get("content")) >= 0
            for container in db_content.get("containers"):
                print(json.dumps(container))
                assert "id" in container
                assert type(container.get("id")) is int
                assert "container_title" in container
                assert "container_path" in container
                assert "description" in container
                assert "img_src" in container
                assert "season_index" in container
            for content in db_content.get("content"):
                print(json.dumps(content))
                assert "id" in content
                assert type(content.get("id")) is int
                assert "content_directory_id" in content
                assert type(content.get("content_directory_id")) is int
                assert "content_title" in content
                assert type(content.get("content_title")) is str
                assert "content_src" in content
                assert type(content.get("content_src")) is str
                assert "description" in content
                assert "img_src" in content
                assert "play_count" in content
                assert type(content.get("play_count")) is int
                assert content.get("play_count") == 0
                assert "user_tags_id" in content
                assert "container_id" in content
                assert "content_id" in content
                assert "tag_title" in content
                assert "user_tags" in content

    def test_collect_directory_movies(self):
        tag = "movie"
        self.setup_content_directory()
        with DBGetter(DBType.PHYSICAL) as db_getter_connection:
            db_content = db_getter_connection.query_db([tag], {}, None, None)
            assert len(db_content.get("content")) == 6
            for content in db_content.get("content"):
                print(json.dumps(content))
                assert tag in content.get("user_tags")


            # if self.media_folders:
            #     for media_path in self.media_folders:
            #         # print(media_path)
            #         db_setter_connection.setup_content_directory(media_path)

    def test_collect_directory_episodes(self):
        tag = "episode"
        self.setup_content_directory()
        with DBGetter(DBType.PHYSICAL) as db_getter_connection:
            db_content = db_getter_connection.query_db([tag], {}, None, None)
            assert len(db_content.get("content")) == 24
            for content in db_content.get("content"):
                print(json.dumps(content))
                assert tag in content.get("user_tags")


    def test_collect_directory_books(self):
        tag = "book"
        self.setup_content_directory()
        with DBGetter(DBType.PHYSICAL) as db_getter_connection:
            db_content = db_getter_connection.query_db([tag], {}, None, None)
            assert len(db_content.get("content")) == 4
            for content in db_content.get("content"):
                print(json.dumps(content))
                assert tag in content.get("user_tags")

    # def test_collect_directory_seasons(self):
    #     tag = "season"
    #     self.setup_content_directory()
    #     with DBGetter(DBType.PHYSICAL) as db_getter_connection:
    #         db_content = db_getter_connection.query_db([tag], {}, None, None)
    #         # assert len(db_content.get("content")) == 2
    #         for content in db_content.get("content"):
    #             print(json.dumps(content))
    #             assert tag in content.get("user_tags")
    #
    #     with DBGetter(DBType.PHYSICAL) as db_getter_connection:
    #         print(db_getter_connection.get_all_tags())
    #     assert False
