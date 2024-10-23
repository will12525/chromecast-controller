import json
import time
import copy

from unittest import TestCase
import config_file_handler
import database_handler.media_metadata_collector as md_collector
from database_handler import common_objects
from . import pytest_mocks


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


class TestDBCreator(TestMediaMetadataCollectorSetup):

    def test_print_day(self):
        print(int(time.strftime('%j')))

    def test_collect_tv_shows(self):
        content_directory_info = copy.deepcopy(self.media_paths[0])
        content_directory_info["content_src"] = content_directory_info["content_src"] + "media_folder_sample/"

        print(content_directory_info)
        result = list(md_collector.collect_mp4_files(content_directory_info))
        # print(json.dumps(result, indent=4))
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
                {
                    "tag_title": "tv"
                },
                {
                    "tag_title": "tv show"
                }
            ]

            assert "container_content" in item
            assert isinstance(item.get("container_content"), list)
            assert len(item.get("container_content")) == 1

            container_content = item.get("container_content")[0]
            print(json.dumps(container_content, indent=4))

            assert "container_path" in item
            assert isinstance(item.get("container_path"), str)

            # assert isinstance(item.get("content_index"), str)

            # assert isinstance(item.get(common_objects.PLAYLIST_TITLE), str)
            # assert isinstance(item.get(common_objects.PATH_COLUMN), str)
            # assert isinstance(item.get(common_objects.SEASON_INDEX_COLUMN), int)
            # assert isinstance(item.get("episode_index"), int)
            # assert isinstance(item.get(common_objects.PLAYLIST_TITLE), str)

            # assert item.get(common_objects.PLAYLIST_TITLE)
            # assert item.get(common_objects.PATH_COLUMN)
            # assert item.get(common_objects.SEASON_INDEX_COLUMN)
            # assert item.get("episode_index")

            # assert " - " in item.get(common_objects.PATH_COLUMN)
            # assert ".mp4" in item.get(common_objects.PATH_COLUMN)
            # assert item.get(common_objects.PLAYLIST_TITLE) in item.get(common_objects.PATH_COLUMN)
            # assert item.get(common_objects.PATH_COLUMN).count(item.get(common_objects.PLAYLIST_TITLE)) == 2
            # assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get(common_objects.PATH_COLUMN)
            # assert str(item.get("episode_index")) in item.get(common_objects.PATH_COLUMN)
            # assert item.get(common_objects.PATH_COLUMN).count(str(item.get("episode_index"))) >= 1
    #
    # def test_collect_movies(self):
    #     result = list(md_collector.collect_movies(self.media_paths[0]))
    #     print(json.dumps(result, indent=4))
    #     assert result
    #     assert len(result) == 5
    #     for item in result:
    #         assert len(item) == 11
    #         assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
    #         assert common_objects.PATH_COLUMN in item
    #         assert item.get(common_objects.MEDIA_TITLE_COLUMN) is not None
    #         assert item.get(common_objects.PATH_COLUMN) is not None
    #         assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
    #         assert isinstance(item.get(common_objects.PATH_COLUMN), str)
    #         assert item.get(common_objects.MEDIA_TITLE_COLUMN)
    #         assert item.get(common_objects.PATH_COLUMN)
    #         assert ".mp4" in item.get(common_objects.PATH_COLUMN)
    #
    # def test_collect_movies_w_extra(self):
    #     result = list(md_collector.collect_movies(self.media_paths[0]))
    #     print(json.dumps(result, indent=4))
    #     assert result
    #     assert len(result) == 5
    #     for item in result:
    #         assert len(item) == 11
    #         assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
    #         assert common_objects.PATH_COLUMN in item
    #         assert item.get(common_objects.MEDIA_TITLE_COLUMN) is not None
    #         assert item.get(common_objects.PATH_COLUMN) is not None
    #         assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
    #         assert isinstance(item.get(common_objects.PATH_COLUMN), str)
    #         assert item.get(common_objects.MEDIA_TITLE_COLUMN)
    #         assert item.get(common_objects.PATH_COLUMN)
    #         assert ".mp4" in item.get(common_objects.PATH_COLUMN)
