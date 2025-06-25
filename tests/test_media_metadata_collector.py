import json
import time
import copy

from unittest import TestCase
import config_file_handler
import database_handler.media_metadata_collector as md_collector
from database_handler import common_objects
from . import pytest_mocks
from . import data_file


class TestMediaMetadataCollectorSetup(TestCase):
    media_paths = None

    def setUp(self) -> None:
        md_collector.MOVE_FILE = False
        self.media_paths = config_file_handler.load_json_file_content().get("media_folders")
        for index, media_path in enumerate(self.media_paths):
            media_path["id"] = index
        pytest_mocks.patch_get_file_hash(self)
        pytest_mocks.patch_get_ffmpeg_metadata(self)
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)


def structure_check(item, tag):
    assert len(item) == 7
    assert "content_directory_id" in item
    assert item.get("content_title") is not None
    assert isinstance(item.get("content_title"), str)
    assert item.get("content_title")
    assert "content_src" in item
    assert item.get("content_src") is not None
    assert isinstance(item.get("content_src"), str)
    assert item.get("content_src")
    assert ".mp4" in item.get("content_src")
    assert item.get("tags") == [{"tag_title": tag}]

class TestCollectMP4Files(TestMediaMetadataCollectorSetup):


    def test_collect_tv_shows_src_0(self):
        self.media_paths[0]["content_src"] += "tv_shows/"

        print(self.media_paths[0])
        result = list(md_collector.collect_mp4_files(self.media_paths[0]))
        print(json.dumps(result, indent=4))
        assert result
        assert type(result) is list
        # print(len(result))
        assert len(result) == 12
        for item in result:
            # print(json.dumps(item, indent=4))
            assert len(item) == 7

            assert "container_title" in item
            assert isinstance(item.get("container_title"), str)
            assert item.get("container_title") in ["Vampire", "Vans", "Werewolf"]

            assert "description" in item
            assert isinstance(item.get("description"), str)
            assert item.get("description") == ""

            assert "img_src" in item
            assert isinstance(item.get("img_src"), str)

            assert "content_index" in item

            assert "tags" in item
            assert isinstance(item.get("tags"), list)
            assert item.get("tags") == [
                {"tag_title": "tv"},
                {"tag_title": "tv show"}
            ]

            assert "container_content" in item
            assert isinstance(item.get("container_content"), list)
            assert len(item.get("container_content")) == 1

            # container_content = item.get("container_content")[0]
            # print(json.dumps(container_content, indent=4))

            assert "container_path" in item
            assert isinstance(item.get("container_path"), str)
        assert result == data_file.tv_show_src_0_struct


    def test_collect_movies_src_0(self):
        self.media_paths[0]["content_src"] += "movies/"
        print(self.media_paths[0])
        result = list(md_collector.collect_mp4_files(self.media_paths[0]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 3
        for item in result:
            structure_check(item, "movie")
        assert result == data_file.movie_src_0_struct

    def test_collect_books_src_0(self):
        self.media_paths[0]["content_src"] += "books/"
        print(self.media_paths[0])
        result = list(md_collector.collect_mp4_files(self.media_paths[0]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 2
        for item in result:
            structure_check(item, "book")
        assert result == data_file.book_src_0_struct



    def test_collect_all_media_src_0(self):
        print(self.media_paths[0])
        result = list(md_collector.collect_mp4_files(self.media_paths[0]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 17
        # for item in result:
        #     print(json.dumps(item, indent=4))
        #     assert len(item) == 7
        #     assert "content_directory_id" in item
        #     assert item.get("content_title") is not None
        #     assert isinstance(item.get("content_title"), str)
        #     assert item.get("content_title")
        #     assert "content_src" in item
        #     assert item.get("content_src") is not None
        #     assert isinstance(item.get("content_src"), str)
        #     assert item.get("content_src")
        #     assert ".mp4" in item.get("content_src")
        #     assert isinstance(item.get("tags"), list)


    def test_collect_tv_shows_src_1(self):
        self.media_paths[1]["content_src"] += "tv_shows/"

        print(self.media_paths[1])
        result = list(md_collector.collect_mp4_files(self.media_paths[1]))
        print(json.dumps(result, indent=4))
        assert result
        assert type(result) is list
        # print(len(result))
        assert len(result) == 12
        for item in result:
            # print(json.dumps(item, indent=4))
            assert len(item) == 7

            assert "container_title" in item
            assert isinstance(item.get("container_title"), str)
            assert item.get("container_title") in ["Gremlins", "Vans", "Dinosaurs"]

            assert "description" in item
            assert isinstance(item.get("description"), str)
            assert item.get("description") == ""

            assert "img_src" in item
            assert isinstance(item.get("img_src"), str)

            assert "content_index" in item

            assert "tags" in item
            assert isinstance(item.get("tags"), list)
            assert item.get("tags") == [
                {"tag_title": "tv"},
                {"tag_title": "tv show"}
            ]

            assert "container_content" in item
            assert isinstance(item.get("container_content"), list)
            assert len(item.get("container_content")) == 1

            # container_content = item.get("container_content")[0]
            # print(json.dumps(container_content, indent=4))

            assert "container_path" in item
            assert isinstance(item.get("container_path"), str)
        assert result == data_file.tv_show_src_1_struct

    def test_collect_movies_src_1(self):
        self.media_paths[1]["content_src"] += "movies/"
        print(self.media_paths[1])
        result = list(md_collector.collect_mp4_files(self.media_paths[1]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 3
        for item in result:
            structure_check(item, "movie")
        assert result == data_file.movie_src_1_struct


    def test_collect_books_src_1(self):
        self.media_paths[1]["content_src"] += "books/"
        print(self.media_paths[1])
        result = list(md_collector.collect_mp4_files(self.media_paths[1]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 2
        for item in result:
            structure_check(item, "book")
        assert result == data_file.book_src_1_struct


    def test_collect_all_media_src_1(self):
        print(self.media_paths[1])
        result = list(md_collector.collect_mp4_files(self.media_paths[1]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 17
        # assert False