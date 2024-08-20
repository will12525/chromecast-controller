import json
import os
from unittest import TestCase

import config_file_handler
from database_handler import common_objects
from database_handler.db_setter import DBCreatorV2
from database_handler.db_getter import DatabaseHandler, DatabaseHandlerV2
from database_handler.common_objects import ContentType, DBType
import __init__


class TestDatabaseHandlerV2(TestCase):
    DB_PATH = "media_metadata.db"
    media_directory_info = None

    def setUp(self) -> None:
        self.media_directory_info = config_file_handler.load_json_file_content().get("media_folders")

        __init__.patch_get_file_hash(self)
        __init__.patch_get_ffmpeg_metadata(self)
        __init__.patch_extract_subclip(self)
        __init__.patch_update_processed_file(self)

        self.erase_db()
        self.create_db()

    def create_db(self):
        if self.media_directory_info:
            with DBCreatorV2(DBType.PHYSICAL) as db_setter_connection:
                db_setter_connection.create_db()
                for media_path in self.media_directory_info:
                    db_setter_connection.setup_content_directory(media_path)

    def erase_db(self):
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)


class TestDatabaseHandlerFunctionsV2(TestDatabaseHandlerV2):

    def test_query_db_all_tv_shows(self):
        """
        episode -> content that is part of a tv show
        season -> container that is part of a tv show
        tv -> container that represents a tv show
        tv show -> container that represents a tv show
        movie -> content that is a movie
        :return:
        """

        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content(["tv show"], {})
        print(f"Found containers: {len(metadata.get('containers'))}")
        assert len(metadata.get('containers')) == 6
        for container in metadata.get("containers"):
            print(container)
        print(f"Found content: {len(metadata.get('content'))}")
        assert len(metadata.get('content')) == 0
        for content in metadata.get("content"):
            print(content)

    def test_query_db_all_tv_show_seasons(self):
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content(["season"], {})
        print(f"Found containers: {len(metadata.get('containers'))}")
        assert len(metadata.get('containers')) == 11
        for container in metadata.get("containers"):
            print(container)
        print(f"Found content: {len(metadata.get('content'))}")
        assert len(metadata.get('content')) == 0
        for content in metadata.get("content"):
            print(content)

    def test_query_db_all_season_content(self):
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content(["episode"], {})
        print(f"Found containers: {len(metadata.get('containers'))}")
        assert len(metadata.get('containers')) == 0
        for container in metadata.get("containers"):
            print(container)
        print(f"Found content: {len(metadata.get('content'))}")
        assert len(metadata.get('content')) == 23
        for content in metadata.get("content"):
            print(content)

    def test_query_db_all_movies(self):
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content(["movie"], {})
        print(f"Found containers: {len(metadata.get('containers'))}")
        assert len(metadata.get('containers')) == 0
        for container in metadata.get("containers"):
            print(container)
        print(f"Found content: {len(metadata.get('content'))}")
        assert len(metadata.get('content')) == 5
        for content in metadata.get("content"):
            print(content)

    def test_query_db_all_content(self):
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content(["episode", "movie"], {})
        print(f"Found containers: {len(metadata.get('containers'))}")
        assert len(metadata.get('containers')) == 0
        for container in metadata.get("containers"):
            print(container)
        print(f"Found content: {len(metadata.get('content'))}")
        assert len(metadata.get('content')) == 28
        for content in metadata.get("content"):
            print(content)

    def test_query_db_identical_tags(self):
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content(["tv", "tv show"], {})
        print(f"Found containers: {len(metadata.get('containers'))}")
        assert len(metadata.get('containers')) == 6
        for container in metadata.get("containers"):
            print(container)
        print(f"Found content: {len(metadata.get('content'))}")
        assert len(metadata.get('content')) == 0
        for content in metadata.get("content"):
            print(content)

    def test_query_db_all_containers(self):
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content(["tv", "season"], {})
        print(f"Found containers: {len(metadata.get('containers'))}")
        assert len(metadata.get('containers')) == 17
        for container in metadata.get("containers"):
            print(container)
        print(f"Found content: {len(metadata.get('content'))}")
        assert len(metadata.get('content')) == 0
        for content in metadata.get("content"):
            print(content)

    #
    def test_query_db_specific_tv_show_seasons(self):
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content([], {"container_id": 15})
        print(f"Found containers: {len(metadata.get('containers'))}")
        assert len(metadata.get('containers')) == 3
        for container in metadata.get("containers"):
            print(container)
        print(f"Found content: {len(metadata.get('content'))}")
        assert len(metadata.get('content')) == 0
        for content in metadata.get("content"):
            print(content)

    def test_query_db_specific_season_content(self):
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content([], {"container_id": 11})
        print(json.dumps(metadata, indent=4))
        print(f"Found containers: {len(metadata.get('containers'))}")
        assert len(metadata.get('containers')) == 0
        for container in metadata.get("containers"):
            print(container)
        print(f"Found content: {len(metadata.get('content'))}")
        assert len(metadata.get('content')) == 3
        for content in metadata.get("content"):
            print(content)

    def test_query_db_empty(self):
        self.erase_db()
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content(["episode"], {"container_id": 11})
        print(f"Result: {metadata}")
        assert not metadata.get("containers")
        assert not metadata.get("content")
        assert not metadata.get("parent_container")

    def test_query_db_media_container(self):
        json_request = {'tag_list': [], 'container_dict': {'container_id': '4'}}
        media_metadata = {}
        print(json_request)
        with DatabaseHandlerV2() as db_getter_connection:
            media_metadata.update(
                db_getter_connection.query_content(
                    json_request.get("tag_list"),
                    json_request.get("container_dict", {}),
                )
            )
        print(json.dumps(media_metadata, indent=4))
        # with DatabaseHandlerV2() as db_connection:
        #     metadata = db_connection.query_content([], {"container_id": 9})
        #     metadata = db_connection.query_content([], {"container_id": 9})
        # content = metadata.get("content")[0]
        # print(json.dumps(content, indent=4))
        # json_request = {"content_id": content["content_id"], "parent_container_id": content["parent_container_id"]}
        # print(json.dumps(json_request, indent=4))

    def test_query_db_media_content(self):
        with DatabaseHandlerV2() as db_connection:
            metadata = db_connection.query_content([], {"content_id": 15})
        print(json.dumps(metadata, indent=4))
        assert len(metadata.get("content")) == 1
        # content = metadata.get("content")[0]
        # json_request = {"content_id": content["content_id"], "parent_container_id": content["parent_container_id"]}
        # print(json.dumps(json_request, indent=4))

    def test_query_db_next_media(self):
        with DatabaseHandlerV2() as db_connection:
            # metadata = db_connection.query_content([], {"container_id": 9})
            # content = metadata.get("content")[0]
            # json_request = {"content_id": content["content_id"], "parent_container_id": content["parent_container_id"]}
            json_request = {'content_id': 23, 'parent_container_id': 9}
            next_content = db_connection.get_next_content_in_container(json_request)
            print(json.dumps(next_content, indent=4))
            assert next_content.get("id") == 19
            json_request = {'content_id': 19, 'parent_container_id': 9}
            next_content = db_connection.get_next_content_in_container(json_request)
            print(json.dumps(next_content, indent=4))
            assert next_content.get("id") == 20
            json_request = {'content_id': 22, 'parent_container_id': 9}
            next_content = db_connection.get_next_content_in_container(json_request)
            print(json.dumps(next_content, indent=4))
            assert next_content.get("id") == 23

    def test_query_db_previous_media(self):
        with DatabaseHandlerV2() as db_connection:
            json_request = {'content_id': 19, 'parent_container_id': 9}
            next_content = db_connection.get_previous_content_in_container(json_request)
            print(json.dumps(next_content, indent=4))
            assert next_content.get("id") == 23
            json_request = {'content_id': 23, 'parent_container_id': 9}
            next_content = db_connection.get_previous_content_in_container(json_request)
            print(json.dumps(next_content, indent=4))
            assert next_content.get("id") == 22
            json_request = {'content_id': 20, 'parent_container_id': 9}
            next_content = db_connection.get_previous_content_in_container(json_request)
            print(json.dumps(next_content, indent=4))
            assert next_content.get("id") == 19

    def test_query_db_all_tags(self):
        with DatabaseHandlerV2() as db_connection:
            tag_list = db_connection.get_all_tags()
        print(json.dumps(tag_list, indent=4))

    def test_query_db_add_tag_to_content(self):
        json_request = {'content_id': 18, "tag_title": "season"}
        with DBCreatorV2() as db_connection:
            json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
            db_connection.add_tag_to_content(json_request)
        with DatabaseHandlerV2() as db_connection:
            content_info = db_connection.get_content_info(json_request.get("content_id"))
        print(json.dumps(content_info, indent=4))
        assert json_request.get("tag_title") in content_info.get("user_tags")

    def test_query_db_remove_tag_from_content(self):
        json_request = {'content_id': 18, "tag_title": "movie"}
        with DBCreatorV2() as db_connection:
            json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
            print(json.dumps(json_request, indent=4))
            db_connection.remove_tag_from_content(json_request)
        with DatabaseHandlerV2() as db_connection:
            content_info = db_connection.get_content_info(json_request.get("content_id"))
        print(json.dumps(content_info, indent=4))
        assert not content_info.get("user_tags")

    def test_query_db_remove_tag_from_container(self):
        json_request = {'container_id': 10, "tag_title": "tv show"}
        with DBCreatorV2() as db_connection:
            json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
            print(json.dumps(json_request, indent=4))
            db_connection.remove_tag_from_container(json_request)
        with DatabaseHandlerV2() as db_connection:
            content_info = db_connection.get_container_info(json_request.get("container_id"))
        print(json.dumps(content_info, indent=4))
        assert content_info.get("user_tags") == "tv"

    def test_query_db_add_tag_to_container(self):
        json_request = {'container_id': 10, "tag_title": "season"}
        with DBCreatorV2() as db_connection:
            json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
            db_connection.add_tag_to_container(json_request)
        with DatabaseHandlerV2() as db_connection:
            content_info = db_connection.get_container_info(json_request.get("container_id"))
        print(json.dumps(content_info, indent=4))
        assert json_request.get("tag_title") in content_info.get("user_tags")

    def test_query_db_add_tag(self):
        new_tag = {"tag_title": "Hello world"}
        with DatabaseHandlerV2() as db_connection:
            tag_list = db_connection.get_all_tags()
        for tag in tag_list:
            assert tag.get("tag_title") != new_tag.get("tag_title")
        with DBCreatorV2() as db_connection:
            db_connection.insert_tag(new_tag)
        with DatabaseHandlerV2() as db_connection:
            tag_list = db_connection.get_all_tags()
        new_tag_found = False
        for tag in tag_list:
            if tag.get("tag_title") == new_tag.get("tag_title"):
                new_tag_found = True
        assert new_tag_found
        print(json.dumps(tag_list, indent=4))


class TestDatabaseHandler(TestCase):
    DB_PATH = "media_metadata.db"

    db_handler = None

    media_paths = None

    def setUp(self) -> None:
        __init__.patch_get_file_hash(self)
        __init__.patch_get_ffmpeg_metadata(self)
        __init__.patch_extract_subclip(self)
        __init__.patch_update_processed_file(self)

        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)

        self.media_paths = config_file_handler.load_json_file_content().get("media_folders")
        assert self.media_paths
        assert isinstance(self.media_paths, list)
        assert len(self.media_paths) == 3
        # with DBCreator() as db_connection:
        #     db_connection.create_db()
        #     for media_path in self.media_paths:
        #         db_connection.setup_media_directory(media_path)


class TestDatabaseHandlerFunctions(TestDatabaseHandler):

    def test_next_content_type(self):
        content_type = ContentType.TV
        content_type = content_type.get_next()
        assert content_type == ContentType.TV_SHOW
        content_type = content_type.get_next()
        assert content_type == ContentType.SEASON
        content_type = content_type.get_next()
        assert content_type == ContentType.MEDIA

    def test_get_next_url(self):
        data = {common_objects.MEDIA_ID_COLUMN: 1, common_objects.PLAYLIST_ID_COLUMN: 1}
        data2 = {common_objects.MEDIA_ID_COLUMN: 5, common_objects.PLAYLIST_ID_COLUMN: 1}
        data3 = {common_objects.MEDIA_ID_COLUMN: 4, common_objects.PLAYLIST_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_next_in_playlist_media_metadata(data)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 2
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "mysterious"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Vampire - s01e002.mp4" == metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("season_title") == "Season 1"
            assert metadata.get("tv_show_title") == "Vampire"

            metadata = db_connection.get_next_in_playlist_media_metadata(data2)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "sparkle"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Vampire - s01e001.mp4" == metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("season_title") == "Season 1"
            assert metadata.get("tv_show_title") == "Vampire"

            metadata = db_connection.get_next_in_playlist_media_metadata(data3)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 5
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 2
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "dark"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Vampire - s02e003.mp4" == metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("season_title") == "Season 2"
            assert metadata.get("tv_show_title") == "Vampire"

    def test_get_previous_url(self):
        data = {common_objects.MEDIA_ID_COLUMN: 1, common_objects.PLAYLIST_ID_COLUMN: 1}
        data2 = {common_objects.MEDIA_ID_COLUMN: 3, common_objects.PLAYLIST_ID_COLUMN: 1}

        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_previous_in_playlist_media_metadata(data)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 5
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 2
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "dark"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Vampire - s02e003.mp4" == metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("season_title") == "Season 2"
            assert metadata.get("tv_show_title") == "Vampire"

            metadata = db_connection.get_previous_in_playlist_media_metadata(data2)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 2
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "mysterious"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Vampire - s01e002.mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("tv_show_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"

    def test_get_media_metadata(self):
        data = {common_objects.MEDIA_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=ContentType.MEDIA, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "sparkle"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("tv_show_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"

    def test_close(self):
        pass

    def test_get_tv_show_title(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_tv_show_title({common_objects.TV_SHOW_ID_COLUMN: 1})
            print(json.dumps(metadata, indent=4))
            assert isinstance(metadata, str)
            assert metadata == "Vampire"

    def test_get_movie_title_list(self):
        compare = [{common_objects.ID_COLUMN: 13, common_objects.MEDIA_TITLE_COLUMN: 'Vampire - s01e001',
                    common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''},
                   {common_objects.ID_COLUMN: 14, common_objects.MEDIA_TITLE_COLUMN: 'Vampire - s01e002',
                    common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''},
                   {common_objects.ID_COLUMN: 15, common_objects.MEDIA_TITLE_COLUMN: 'Vampire - s02e001',
                    common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''},
                   {common_objects.ID_COLUMN: 16, common_objects.MEDIA_TITLE_COLUMN: 'Vampire - s02e002',
                    common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''},
                   {common_objects.ID_COLUMN: 17, common_objects.MEDIA_TITLE_COLUMN: 'Vampire - s02e003',
                    common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''}]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_list(ContentType.MOVIE)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert common_objects.MEDIA_TITLE_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                assert movie in compare

    def test_get_playlist_title_list(self):
        compare = [{common_objects.ID_COLUMN: 6, common_objects.PLAYLIST_TITLE: 'Dinosaurs',
                    common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''},
                   {common_objects.ID_COLUMN: 14, common_objects.MEDIA_TITLE_COLUMN: '', common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''},
                   {common_objects.ID_COLUMN: 15, common_objects.MEDIA_TITLE_COLUMN: '', common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''},
                   {common_objects.ID_COLUMN: 16, common_objects.MEDIA_TITLE_COLUMN: '', common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''},
                   {common_objects.ID_COLUMN: 17, common_objects.MEDIA_TITLE_COLUMN: '', common_objects.DESCRIPTION: '',
                    common_objects.IMAGE_URL: ''}]
        # with DBCreator() as db_connection:
        #     row_id = db_connection.set_playlist_metadata(
        #         {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Dinosaurs"})
        #     print(row_id)

        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_list(ContentType.PLAYLISTS)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.PLAYLIST.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 1
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert common_objects.PLAYLIST_TITLE in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.PLAYLIST_TITLE], str)
                assert movie in compare

    def test_get_tv_show_title_list(self):
        movie_titles = [{'id': 4, 'playlist_title': 'Animal Party', "description": "", "image_url": ""},
                        {'id': 5, 'playlist_title': 'Sparkles', "description": "", "image_url": ""},
                        {'id': 1, 'playlist_title': 'Vampire', "description": "", "image_url": ""},
                        {'id': 2, 'playlist_title': 'Vans', "description": "", "image_url": ""},
                        {'id': 3, 'playlist_title': 'Werewolf', "description": "", "image_url": ""}]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_list(ContentType.TV)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.TV_SHOW.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "playlist_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["playlist_title"], str)
                assert movie in movie_titles

    def test_get_tv_show_season_title_list(self):
        compare = [{'id': 1, 'season_title': 'Season 1', 'season_index': 1, "description": "", "image_url": ""},
                   {'id': 2, 'season_title': 'Season 2', 'season_index': 2, "description": "", "image_url": ""}]
        data = {common_objects.TV_SHOW_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_list(ContentType.TV_SHOW, data)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.SEASON.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "season_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["season_title"], str)
                assert movie in compare

    def test_get_tv_show_season_episode_title_list(self):
        compare = [
            {
                "id": 1,
                "media_title": "",
                "season_index": 1,
                "list_index": 1001,
                "play_count": 0, "description": "", "image_url": ""
            },
            {
                "id": 2,
                "media_title": "",
                "season_index": 1,
                "list_index": 1002,
                "play_count": 0, "description": "", "image_url": ""
            }
        ]
        data = {common_objects.SEASON_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_list(ContentType.SEASON, data)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert common_objects.MEDIA_TITLE_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                assert movie in compare

    def test_get_tv_show_metadata(self):
        compare = [{'id': 1, 'season_title': 'Season 1', 'season_index': 1, "description": "", "image_url": ""},
                   {'id': 2, 'season_title': 'Season 2', 'season_index': 2, "description": "", "image_url": ""}]
        data = {common_objects.TV_SHOW_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=ContentType.TV_SHOW, params_dict=data)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("container_content_type") == ContentType.TV.value
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("season_count") == 2
            assert metadata.get("episode_count") == 5
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "season_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["season_title"], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.SEASON.value

    def test_get_movie_metadata(self):
        compare = [{
            "id": 13,
            "media_title": "Vampire - s01e001",
            "description": "",
            "image_url": ""
        },
            {
                "id": 14,
                "media_title": "Vampire - s01e002",
                "description": "",
                "image_url": ""
            },
            {
                "id": 15,
                "media_title": "Vampire - s02e001",
                "description": "",
                "image_url": ""
            },
            {
                "id": 16,
                "media_title": "Vampire - s02e002",
                "description": "",
                "image_url": ""
            },
            {
                "id": 17,
                "media_title": "Vampire - s02e003",
                "description": "",
                "image_url": ""
            }]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=ContentType.MOVIE)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_tv_show_season_metadata(self):
        compare = [
            {
                "id": 1,
                "media_title": "",
                "season_index": 1,
                "list_index": 1,
                "play_count": 0, "description": "", "image_url": ""
            },
            {
                "id": 2,
                "media_title": "",
                "season_index": 1,
                "list_index": 2,
                "play_count": 0, "description": "", "image_url": ""
            }]
        data = {common_objects.SEASON_ID_COLUMN: 1}

        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=ContentType.SEASON, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("container_content_type") == ContentType.TV_SHOW.value
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_INDEX_COLUMN) == 1
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"
            assert metadata.get("episode_count") == 2
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                # print(json.dumps(movie, indent=4))

                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert common_objects.MEDIA_TITLE_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_season_list_index(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_season_list_index({common_objects.SEASON_ID_COLUMN: 1})
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, int)
            assert metadata == 1

    def test_get_movie_media_content(self):
        content_type = ContentType.MOVIE
        compare = [
            {
                "id": 13,
                "media_title": "Vampire - s01e001",
                "description": "",
                "image_url": ""
            },
            {
                "id": 14,
                "media_title": "Vampire - s01e002",
                "description": "",
                "image_url": ""
            },
            {
                "id": 15,
                "media_title": "Vampire - s02e001",
                "description": "",
                "image_url": ""
            },
            {
                "id": 16,
                "media_title": "Vampire - s02e002",
                "description": "",
                "image_url": ""
            },
            {
                "id": 17,
                "media_title": "Vampire - s02e003",
                "description": "",
                "image_url": ""
            }]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert common_objects.MEDIA_TITLE_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                # print(movie)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_tv_show_media_content(self):
        content_type = ContentType.TV
        compare = [{'id': 4, 'playlist_title': 'Animal Party', "description": "", "image_url": ""},
                   {'id': 5, 'playlist_title': 'Sparkles', "description": "", "image_url": ""},
                   {'id': 1, 'playlist_title': 'Vampire', "description": "", "image_url": ""},
                   {'id': 2, 'playlist_title': 'Vans', "description": "", "image_url": ""},
                   {'id': 3, 'playlist_title': 'Werewolf', "description": "", "image_url": ""}]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "playlist_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["playlist_title"], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.TV_SHOW.value

    def test_get_tv_show_none_content(self):
        content_type = ContentType.TV_SHOW
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type)
            assert not metadata
            assert isinstance(metadata, dict)
            assert metadata == {}

    def test_get_season_media_content(self):
        content_type = ContentType.TV_SHOW
        media_id = 1
        compare = [{'id': 1, 'season_title': 'Season 1', 'season_index': 1, "description": "", "image_url": ""},
                   {'id': 2, 'season_title': 'Season 2', 'season_index': 2, "description": "", "image_url": ""}]
        params = {common_objects.TV_SHOW_ID_COLUMN: media_id}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=params)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("season_count") == 2
            assert metadata.get("episode_count") == 5
            assert metadata.get("container_content_type") == ContentType.TV.value
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "season_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["season_title"], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.SEASON.value

    def test_get_playlist_media_content(self):
        content_type = ContentType.PLAYLIST
        media_id = 1
        compare = [{
            "id": 1,
            "media_title": "",
            "list_index": 1,
            "play_count": 0,
            "description": "",
            "image_url": ""
        },
            {
                "id": 2,
                "media_title": "",
                "list_index": 2,
                "play_count": 0,
                "description": "",
                "image_url": ""
            },
            {
                "id": 3,
                "media_title": "",
                "list_index": 1,
                "play_count": 0,
                "description": "",
                "image_url": ""
            },
            {
                "id": 4,
                "media_title": "",
                "list_index": 2,
                "play_count": 0,
                "description": "",
                "image_url": ""
            },
            {
                "id": 5,
                "media_title": "",
                "list_index": 3,
                "play_count": 0,
                "description": "",
                "image_url": ""
            }]
        params = {common_objects.PLAYLIST_ID_COLUMN: media_id}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=params)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("episode_count") == 5
            assert metadata.get("container_content_type") == ContentType.PLAYLISTS.value
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "media_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["media_title"], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_media_content(self):
        content_type = ContentType.SEASON
        media_id = 1
        compare = [
            {
                "id": 1,
                "media_title": "",
                "season_index": 1,
                "list_index": 1,
                "play_count": 0,
                "description": "",
                "image_url": ""
            },
            {
                "id": 2,
                "media_title": "",
                "season_index": 1,
                "list_index": 2,
                "play_count": 0,
                "description": "",
                "image_url": ""
            }
        ]
        params = {common_objects.SEASON_ID_COLUMN: media_id}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=params)
        print(json.dumps(metadata, indent=4))
        assert metadata
        assert isinstance(metadata, dict)
        assert metadata.get(common_objects.ID_COLUMN) == 1
        assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
        assert metadata.get(common_objects.SEASON_INDEX_COLUMN) == 1
        assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
        assert metadata.get("playlist_title") == "Vampire"
        assert metadata.get("season_title") == "Season 1"
        assert metadata.get("episode_count") == 2
        assert metadata.get("container_content_type") == ContentType.TV_SHOW.value
        assert metadata.get("media_list")
        assert isinstance(metadata.get("media_list"), list)
        assert len(metadata.get("media_list")) == 2
        for movie in metadata.get("media_list"):
            assert isinstance(movie, dict)
            assert common_objects.ID_COLUMN in movie
            assert common_objects.MEDIA_TITLE_COLUMN in movie
            assert isinstance(movie[common_objects.ID_COLUMN], int)
            assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
            assert movie in compare
        assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_media_content_metadata(self):
        content_type = ContentType.MEDIA
        data = {common_objects.MEDIA_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
        print(json.dumps(metadata, indent=4))
        assert metadata
        assert metadata.get(common_objects.ID_COLUMN) == 1
        assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
        assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
        assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
        # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "sparkle"
        assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
        assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
        assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
            common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
        assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
            common_objects.MEDIA_DIRECTORY_URL_COLUMN)
        assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
        assert metadata.get("tv_show_title") == "Vampire"
        assert metadata.get("season_title") == "Season 1"

    def test_get_media_content_none(self):
        content_type = ContentType.PLAYLIST
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type)
        # print(metadata)
        assert isinstance(metadata, dict)
        assert metadata == {}

    def test_update_media_metadata_media(self):
        content_type = ContentType.MEDIA
        description_metadata = {'content_type': content_type.value, 'id': 1, 'image_url': 'Hello',
                                'description': 'World'}
        data = {common_objects.MEDIA_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
            # print(json.dumps(metadata, indent=4))
            assert metadata.get(common_objects.DESCRIPTION) == ""
            assert metadata.get(common_objects.IMAGE_URL) == ""
            db_connection.update_media_metadata(description_metadata)
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
            assert metadata.get(common_objects.DESCRIPTION) == description_metadata.get(common_objects.DESCRIPTION)
            assert metadata.get(common_objects.IMAGE_URL) == description_metadata.get(common_objects.IMAGE_URL)

    def test_update_media_metadata_season(self):
        content_type = ContentType.SEASON
        description_metadata = {'content_type': content_type.value, 'id': 1, 'image_url': 'Hello',
                                'description': 'World'}
        data = {common_objects.SEASON_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata.get(common_objects.DESCRIPTION) == ""
            assert metadata.get(common_objects.IMAGE_URL) == ""
            db_connection.update_media_metadata(description_metadata)
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata.get(common_objects.DESCRIPTION) == description_metadata.get(common_objects.DESCRIPTION)
            assert metadata.get(common_objects.IMAGE_URL) == description_metadata.get(common_objects.IMAGE_URL)

    def test_update_media_metadata_tv_show(self):
        content_type = ContentType.TV_SHOW
        description_metadata = {'content_type': content_type.value, 'id': 1, 'image_url': 'Hello',
                                'description': 'World'}
        data = {common_objects.TV_SHOW_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata.get(common_objects.DESCRIPTION) == ""
            assert metadata.get(common_objects.IMAGE_URL) == ""
            db_connection.update_media_metadata(description_metadata)
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata.get(common_objects.DESCRIPTION) == description_metadata.get(common_objects.DESCRIPTION)
            assert metadata.get(common_objects.IMAGE_URL) == description_metadata.get(common_objects.IMAGE_URL)

    def test_update_media_metadata_playlist(self):
        content_type = ContentType.PLAYLIST
        description_metadata = {'content_type': content_type.value, 'id': 1, 'image_url': 'Hello',
                                'description': 'World'}
        data = {common_objects.PLAYLIST_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata.get(common_objects.DESCRIPTION) == ""
            assert metadata.get(common_objects.IMAGE_URL) == ""
            db_connection.update_media_metadata(description_metadata)
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata.get(common_objects.DESCRIPTION) == description_metadata.get(common_objects.DESCRIPTION)
            assert metadata.get(common_objects.IMAGE_URL) == description_metadata.get(common_objects.IMAGE_URL)

    def test_update_play_count(self):
        data = {common_objects.MEDIA_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=ContentType.MEDIA, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata.get(common_objects.PLAY_COUNT) == 0
            assert metadata.get(common_objects.MEDIA_ID_COLUMN) == data[common_objects.MEDIA_ID_COLUMN]
            db_connection.update_play_count(params=data)
            metadata = db_connection.get_media_content(content_type=ContentType.MEDIA, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata.get(common_objects.PLAY_COUNT) == 1
            assert metadata.get(common_objects.MEDIA_ID_COLUMN) == data[common_objects.MEDIA_ID_COLUMN]
