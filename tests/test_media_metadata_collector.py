import json
import pathlib
from unittest import TestCase
import config_file_handler
import database_handler.media_metadata_collector as md_collector
from database_handler import common_objects
import __init__


class TestMediaMetadataCollectorSetup(TestCase):
    media_paths = None

    def setUp(self) -> None:
        md_collector.MOVE_FILE = False
        self.media_paths = config_file_handler.load_js_file().get("media_folders")

        __init__.patch_get_file_hash(self)
        __init__.patch_get_ffmpeg_metadata(self)
        __init__.patch_move_media_file(self)
        __init__.patch_extract_subclip(self)


class TestDBCreator(TestMediaMetadataCollectorSetup):

    def test_collect_tv_shows(self):
        result = list(md_collector.collect_tv_shows(self.media_paths[0]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 12
        for item in result:
            assert len(item) == 11
            assert common_objects.PLAYLIST_TITLE in item
            assert common_objects.PATH_COLUMN in item
            assert common_objects.SEASON_INDEX_COLUMN in item
            assert "episode_index" in item
            assert item.get(common_objects.PLAYLIST_TITLE) is not None
            assert item.get(common_objects.PATH_COLUMN) is not None
            assert item.get(common_objects.SEASON_INDEX_COLUMN) is not None
            assert item.get("episode_index") is not None

            assert isinstance(item.get(common_objects.PLAYLIST_TITLE), str)
            assert isinstance(item.get(common_objects.PATH_COLUMN), str)
            assert isinstance(item.get(common_objects.SEASON_INDEX_COLUMN), int)
            assert isinstance(item.get("episode_index"), int)
            assert isinstance(item.get(common_objects.PLAYLIST_TITLE), str)

            assert item.get(common_objects.PLAYLIST_TITLE)
            assert item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.SEASON_INDEX_COLUMN)
            assert item.get("episode_index")

            assert " - " in item.get(common_objects.PATH_COLUMN)
            assert ".mp4" in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PLAYLIST_TITLE) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(item.get(common_objects.PLAYLIST_TITLE)) == 2
            assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get(common_objects.PATH_COLUMN)
            assert str(item.get("episode_index")) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(str(item.get("episode_index"))) >= 1

    def test_collect_movies(self):
        result = list(md_collector.collect_movies(self.media_paths[1]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 5
        for item in result:
            assert len(item) == 11
            assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
            assert common_objects.PATH_COLUMN in item
            assert item.get(common_objects.MEDIA_TITLE_COLUMN) is not None
            assert item.get(common_objects.PATH_COLUMN) is not None
            assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
            assert isinstance(item.get(common_objects.PATH_COLUMN), str)
            assert item.get(common_objects.MEDIA_TITLE_COLUMN)
            assert item.get(common_objects.PATH_COLUMN)
            assert ".mp4" in item.get(common_objects.PATH_COLUMN)

    def test_collect_movies_w_extra(self):
        result = list(md_collector.collect_movies(self.media_paths[1]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 5
        for item in result:
            assert len(item) == 11
            assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
            assert common_objects.PATH_COLUMN in item
            assert item.get(common_objects.MEDIA_TITLE_COLUMN) is not None
            assert item.get(common_objects.PATH_COLUMN) is not None
            assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
            assert isinstance(item.get(common_objects.PATH_COLUMN), str)
            assert item.get(common_objects.MEDIA_TITLE_COLUMN)
            assert item.get(common_objects.PATH_COLUMN)
            assert ".mp4" in item.get(common_objects.PATH_COLUMN)
