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
        self.media_paths = config_file_handler.load_js_file()

        __init__.patch_get_file_hash(self)
        __init__.patch_get_ffmpeg_metadata(self)
        __init__.patch_move_media_file(self)


class TestDBCreator(TestMediaMetadataCollectorSetup):

    def test_get_new_title_txt_files(self):
        media_folder_path = md_collector.get_new_media_folder_path(self.media_paths[2])
        # print(media_folder_path)
        media_folder_titles = md_collector.get_title_txt_files(media_folder_path)
        assert len(media_folder_titles) == 4
        for key, value in media_folder_titles.items():
            # print(key, value)
            assert isinstance(key, str)
            assert isinstance(value, list)
            assert str(media_folder_path) in key
            assert "S" in key
            assert value
            for item in value:
                assert item
                assert isinstance(item, str)

    def test_get_tv_show_title_txt_files(self):
        media_directory_info = self.media_paths[0]
        media_folder_path = pathlib.Path(media_directory_info.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN))
        media_folder_titles = md_collector.get_title_txt_files(media_folder_path)
        # print(media_folder_titles)
        assert len(media_folder_titles) == 5
        for key, value in media_folder_titles.items():
            # print(key, value)
            assert isinstance(key, str)
            assert isinstance(value, list)
            assert str(media_folder_path) in key
            assert "Season " in key
            assert value
            for item in value:
                assert item
                assert isinstance(item, str)

    def test_collect_tv_shows(self):
        result = list(md_collector.collect_tv_shows(self.media_paths[0]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 12
        for item in result:
            assert len(item) == 10
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
            assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)

            assert item.get(common_objects.PLAYLIST_TITLE)
            assert item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.SEASON_INDEX_COLUMN)
            assert item.get("episode_index")

            assert "Season " in item.get(common_objects.PATH_COLUMN)
            assert " - " in item.get(common_objects.PATH_COLUMN)
            assert ".mp4" in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PLAYLIST_TITLE) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(item.get(common_objects.PLAYLIST_TITLE)) == 2
            assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(
                str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 2
            assert str(item.get("episode_index")) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(str(item.get("episode_index"))) >= 1

    def test_collect_tv_shows_new(self):
        result = list(md_collector.collect_tv_shows(self.media_paths[2]))
        counts_of_length_8 = 0
        counts_of_length_10 = 0
        # print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 20
        for item in result:
            # print(json.dumps(item, indent=4))
            if len(item) == 10:
                counts_of_length_8 += 1
            if len(item) == 12:
                counts_of_length_10 += 1
                assert "media_folder_mp4" in item
                assert "mp4_output_file_name" in item
                assert item.get("media_folder_mp4") is not None
                assert item.get("mp4_output_file_name") is not None
                assert isinstance(item.get("media_folder_mp4"), str)
                assert isinstance(item.get("mp4_output_file_name"), str)
                assert item.get("media_folder_mp4")
                assert item.get("mp4_output_file_name")

                assert "input" in item.get("media_folder_mp4")
                assert "S" in item.get("media_folder_mp4")
                assert "E" in item.get("media_folder_mp4")
                assert ".mp4" in item.get("media_folder_mp4")
                assert "output" in item.get("mp4_output_file_name")
                assert "Season " in item.get("mp4_output_file_name")
                assert " - " in item.get("mp4_output_file_name")
                assert ".mp4" in item.get("mp4_output_file_name")

                assert item.get(common_objects.PLAYLIST_TITLE) in item.get("media_folder_mp4")
                assert item.get("media_folder_mp4").count(item.get(common_objects.PLAYLIST_TITLE)) == 1
                assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get("media_folder_mp4")
                assert item.get("media_folder_mp4").count(str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 1
                assert str(item.get("episode_index")) in item.get("media_folder_mp4")
                assert item.get("media_folder_mp4").count(str(item.get("episode_index"))) >= 1
                assert item.get(common_objects.PLAYLIST_TITLE) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(item.get(common_objects.PLAYLIST_TITLE)) == 2
                assert item.get(common_objects.PATH_COLUMN) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(item.get(common_objects.PATH_COLUMN)) == 1
                assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 2
                assert str(item.get("episode_index")) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(str(item.get("episode_index"))) >= 1

            assert len(item) in [12, 10]
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
            assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)

            assert item.get(common_objects.PLAYLIST_TITLE)
            assert item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.SEASON_INDEX_COLUMN)
            assert item.get("episode_index")

            assert "Season " in item.get(common_objects.PATH_COLUMN)
            assert " - " in item.get(common_objects.PATH_COLUMN)
            assert ".mp4" in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PLAYLIST_TITLE) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(item.get(common_objects.PLAYLIST_TITLE)) == 2
            assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(
                str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 2
            assert str(item.get("episode_index")) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(str(item.get("episode_index"))) >= 1
            # print(counts_of_length_8, counts_of_length_10)
        assert counts_of_length_8 == counts_of_length_10 == 10

    def test_collect_tv_shows_new_w_extra(self):
        result = list(md_collector.collect_tv_shows(self.media_paths[2]))
        counts_of_length_8 = 0
        counts_of_length_10 = 0
        # print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 20
        for item in result:
            # print(json.dumps(item, indent=4))
            if len(item) == 10:
                counts_of_length_8 += 1
            if len(item) == 12:
                counts_of_length_10 += 1
                assert "media_folder_mp4" in item
                assert "mp4_output_file_name" in item
                assert item.get("media_folder_mp4") is not None
                assert item.get("mp4_output_file_name") is not None
                assert isinstance(item.get("media_folder_mp4"), str)
                assert isinstance(item.get("mp4_output_file_name"), str)
                assert item.get("media_folder_mp4")
                assert item.get("mp4_output_file_name")

                assert "input" in item.get("media_folder_mp4")
                assert "S" in item.get("media_folder_mp4")
                assert "E" in item.get("media_folder_mp4")
                assert ".mp4" in item.get("media_folder_mp4")
                assert "output" in item.get("mp4_output_file_name")
                assert "Season " in item.get("mp4_output_file_name")
                assert " - " in item.get("mp4_output_file_name")
                assert ".mp4" in item.get("mp4_output_file_name")

                assert item.get(common_objects.PLAYLIST_TITLE) in item.get("media_folder_mp4")
                assert item.get("media_folder_mp4").count(item.get(common_objects.PLAYLIST_TITLE)) == 1
                assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get("media_folder_mp4")
                assert item.get("media_folder_mp4").count(str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 1
                assert str(item.get("episode_index")) in item.get("media_folder_mp4")
                assert item.get("media_folder_mp4").count(str(item.get("episode_index"))) >= 1
                assert item.get(common_objects.PLAYLIST_TITLE) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(item.get(common_objects.PLAYLIST_TITLE)) == 2
                assert item.get(common_objects.PATH_COLUMN) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(item.get(common_objects.PATH_COLUMN)) == 1
                assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 2
                assert str(item.get("episode_index")) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(str(item.get("episode_index"))) >= 1

            assert len(item) in [12, 10]
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
            assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)

            assert item.get(common_objects.PLAYLIST_TITLE)
            assert item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.SEASON_INDEX_COLUMN)
            assert item.get("episode_index")

            assert "Season " in item.get(common_objects.PATH_COLUMN)
            assert " - " in item.get(common_objects.PATH_COLUMN)
            assert ".mp4" in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PLAYLIST_TITLE) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(item.get(common_objects.PLAYLIST_TITLE)) == 2
            assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(
                str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 2
            assert str(item.get("episode_index")) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(str(item.get("episode_index"))) >= 1
            # print(counts_of_length_8, counts_of_length_10)
        assert counts_of_length_8 == counts_of_length_10 == 10

    def test_collect_movies(self):
        result = list(md_collector.collect_movies(self.media_paths[1]))
        # print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 5
        for item in result:
            assert len(item) == 10
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
        # print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 5
        for item in result:
            assert len(item) == 10
            assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
            assert common_objects.PATH_COLUMN in item
            assert item.get(common_objects.MEDIA_TITLE_COLUMN) is not None
            assert item.get(common_objects.PATH_COLUMN) is not None
            assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
            assert isinstance(item.get(common_objects.PATH_COLUMN), str)
            assert item.get(common_objects.MEDIA_TITLE_COLUMN)
            assert item.get(common_objects.PATH_COLUMN)
            assert ".mp4" in item.get(common_objects.PATH_COLUMN)

    def test_collect_new_tv_shows_new(self):
        result = list(md_collector.collect_new_tv_shows(self.media_paths[2]))
        # print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 10
        for item in result:
            assert len(item) == 12
            assert "media_folder_mp4" in item
            assert "mp4_output_file_name" in item
            assert common_objects.PLAYLIST_TITLE in item
            assert common_objects.PATH_COLUMN in item
            assert common_objects.SEASON_INDEX_COLUMN in item
            assert "episode_index" in item
            assert common_objects.MEDIA_TITLE_COLUMN in item
            assert item.get("media_folder_mp4") is not None
            assert item.get("mp4_output_file_name") is not None
            assert item.get(common_objects.PLAYLIST_TITLE) is not None
            assert item.get(common_objects.PATH_COLUMN) is not None
            assert item.get(common_objects.SEASON_INDEX_COLUMN) is not None
            assert item.get("episode_index") is not None
            assert item.get(common_objects.MEDIA_TITLE_COLUMN) is not None
            assert isinstance(item.get("media_folder_mp4"), str)
            assert isinstance(item.get("mp4_output_file_name"), str)
            assert isinstance(item.get(common_objects.PLAYLIST_TITLE), str)
            assert isinstance(item.get(common_objects.PATH_COLUMN), str)
            assert isinstance(item.get(common_objects.SEASON_INDEX_COLUMN), int)
            assert isinstance(item.get("episode_index"), int)
            assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)

            assert item.get("media_folder_mp4")
            assert item.get("mp4_output_file_name")
            assert item.get(common_objects.PLAYLIST_TITLE)
            assert item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.SEASON_INDEX_COLUMN)
            assert item.get("episode_index")
            assert item.get(common_objects.MEDIA_TITLE_COLUMN)

            assert "input" in item.get("media_folder_mp4")
            assert "S" in item.get("media_folder_mp4")
            assert "E" in item.get("media_folder_mp4")
            assert ".mp4" in item.get("media_folder_mp4")
            assert "output" in item.get("mp4_output_file_name")
            assert "Season " in item.get("mp4_output_file_name")
            assert " - " in item.get("mp4_output_file_name")
            assert ".mp4" in item.get("mp4_output_file_name")

            assert item.get(common_objects.PLAYLIST_TITLE) in item.get("media_folder_mp4")
            assert item.get("media_folder_mp4").count(item.get(common_objects.PLAYLIST_TITLE)) == 1
            assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get("media_folder_mp4")
            assert item.get("media_folder_mp4").count(str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 1
            assert str(item.get("episode_index")) in item.get("media_folder_mp4")
            assert item.get("media_folder_mp4").count(str(item.get("episode_index"))) >= 1
            assert item.get(common_objects.PLAYLIST_TITLE) in item.get("mp4_output_file_name")
            assert item.get("mp4_output_file_name").count(item.get(common_objects.PLAYLIST_TITLE)) == 2
            assert item.get(common_objects.PATH_COLUMN) in item.get("mp4_output_file_name")
            assert item.get("mp4_output_file_name").count(item.get(common_objects.PATH_COLUMN)) == 1
            assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get("mp4_output_file_name")
            assert item.get("mp4_output_file_name").count(str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 2
            assert str(item.get("episode_index")) in item.get("mp4_output_file_name")
            assert item.get("mp4_output_file_name").count(str(item.get("episode_index"))) >= 1

            assert "Season " in item.get(common_objects.PATH_COLUMN)
            assert " - " in item.get(common_objects.PATH_COLUMN)
            assert ".mp4" in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PLAYLIST_TITLE) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(item.get(common_objects.PLAYLIST_TITLE)) == 2
            assert str(item.get(common_objects.SEASON_INDEX_COLUMN)) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(
                str(item.get(common_objects.SEASON_INDEX_COLUMN))) >= 2
            assert str(item.get("episode_index")) in item.get(common_objects.PATH_COLUMN)
            assert item.get(common_objects.PATH_COLUMN).count(str(item.get("episode_index"))) >= 1
