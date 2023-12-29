import json
import os
import pathlib
from unittest import TestCase
import config_file_handler
import database_handler.media_metadata_collector as md_collector


class TestMediaMetadataCollectorSetup(TestCase):
    DB_PATH = "media_metadata.db"

    media_paths = None
    new_media_path = None

    def setUp(self) -> None:
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)
        self.media_paths = config_file_handler.load_js_file()


class TestDBCreator(TestMediaMetadataCollectorSetup):

    def test_get_new_title_txt_files(self):
        media_folder_path = md_collector.get_new_media_folder_path(self.media_paths[2])
        print(media_folder_path)
        media_folder_titles = md_collector.get_title_txt_files(media_folder_path)
        assert len(media_folder_titles) == 4
        for key, value in media_folder_titles.items():
            print(key, value)
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
        media_folder_path = pathlib.Path(media_directory_info.get("media_folder_path"))
        media_folder_titles = md_collector.get_title_txt_files(media_folder_path)
        print(media_folder_titles)
        assert len(media_folder_titles) == 5
        for key, value in media_folder_titles.items():
            print(key, value)
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
        assert len(result) == 13
        for item in result:
            assert len(item) == 5
            assert "mp4_show_title" in item
            assert "mp4_file_url" in item
            assert "season_index" in item
            assert "episode_index" in item
            assert item.get("mp4_show_title") is not None
            assert item.get("mp4_file_url") is not None
            assert item.get("season_index") is not None
            assert item.get("episode_index") is not None

            assert isinstance(item.get("mp4_show_title"), str)
            assert isinstance(item.get("mp4_file_url"), str)
            assert isinstance(item.get("season_index"), int)
            assert isinstance(item.get("episode_index"), int)
            assert isinstance(item.get("media_title"), str)

            assert item.get("mp4_show_title")
            assert item.get("mp4_file_url")
            assert item.get("season_index")
            assert item.get("episode_index")

            assert "Season " in item.get("mp4_file_url")
            assert " - " in item.get("mp4_file_url")
            assert ".mp4" in item.get("mp4_file_url")
            assert item.get("mp4_show_title") in item.get("mp4_file_url")
            assert item.get("mp4_file_url").count(item.get("mp4_show_title")) == 2
            assert str(item.get("season_index")) in item.get("mp4_file_url")
            assert item.get("mp4_file_url").count(str(item.get("season_index"))) >= 2
            assert str(item.get("episode_index")) in item.get("mp4_file_url")
            assert item.get("mp4_file_url").count(str(item.get("episode_index"))) >= 1

    def test_collect_tv_shows_new(self):
        result = list(md_collector.collect_tv_shows(self.media_paths[2]))
        counts_of_length_7 = 0
        counts_of_length_5 = 0
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 20
        for item in result:
            print(json.dumps(item, indent=4))
            if len(item) == 5:
                counts_of_length_5 += 1
            if len(item) == 7:
                counts_of_length_7 += 1
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

                assert item.get("mp4_show_title") in item.get("media_folder_mp4")
                assert item.get("media_folder_mp4").count(item.get("mp4_show_title")) == 1
                assert str(item.get("season_index")) in item.get("media_folder_mp4")
                assert item.get("media_folder_mp4").count(str(item.get("season_index"))) >= 1
                assert str(item.get("episode_index")) in item.get("media_folder_mp4")
                assert item.get("media_folder_mp4").count(str(item.get("episode_index"))) >= 1
                assert item.get("mp4_show_title") in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(item.get("mp4_show_title")) == 2
                assert item.get("mp4_file_url") in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(item.get("mp4_file_url")) == 1
                assert str(item.get("season_index")) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(str(item.get("season_index"))) >= 2
                assert str(item.get("episode_index")) in item.get("mp4_output_file_name")
                assert item.get("mp4_output_file_name").count(str(item.get("episode_index"))) >= 1

            assert len(item) in [7, 5]
            assert "mp4_show_title" in item
            assert "mp4_file_url" in item
            assert "season_index" in item
            assert "episode_index" in item
            assert item.get("mp4_show_title") is not None
            assert item.get("mp4_file_url") is not None
            assert item.get("season_index") is not None
            assert item.get("episode_index") is not None

            assert isinstance(item.get("mp4_show_title"), str)
            assert isinstance(item.get("mp4_file_url"), str)
            assert isinstance(item.get("season_index"), int)
            assert isinstance(item.get("episode_index"), int)
            assert isinstance(item.get("media_title"), str)

            assert item.get("mp4_show_title")
            assert item.get("mp4_file_url")
            assert item.get("season_index")
            assert item.get("episode_index")

            assert "Season " in item.get("mp4_file_url")
            assert " - " in item.get("mp4_file_url")
            assert ".mp4" in item.get("mp4_file_url")
            assert item.get("mp4_show_title") in item.get("mp4_file_url")
            assert item.get("mp4_file_url").count(item.get("mp4_show_title")) == 2
            assert str(item.get("season_index")) in item.get("mp4_file_url")
            assert item.get("mp4_file_url").count(str(item.get("season_index"))) >= 2
            assert str(item.get("episode_index")) in item.get("mp4_file_url")
            assert item.get("mp4_file_url").count(str(item.get("episode_index"))) >= 1
        assert counts_of_length_5 == counts_of_length_7 == 10

    def test_collect_movies(self):
        result = list(md_collector.collect_movies(self.media_paths[1]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 5
        for item in result:
            assert len(item) == 2
            assert "mp4_show_title" in item
            assert "mp4_file_url" in item
            assert item.get("mp4_show_title") is not None
            assert item.get("mp4_file_url") is not None
            assert isinstance(item.get("mp4_show_title"), str)
            assert isinstance(item.get("mp4_file_url"), str)
            assert item.get("mp4_show_title")
            assert item.get("mp4_file_url")
            assert ".mp4" in item.get("mp4_file_url")

    def test_collect_new_tv_shows_new(self):
        result = list(md_collector.collect_new_tv_shows(self.media_paths[2]))
        print(json.dumps(result, indent=4))
        assert result
        assert len(result) == 10
        for item in result:
            assert len(item) == 7
            assert "media_folder_mp4" in item
            assert "mp4_output_file_name" in item
            assert "mp4_show_title" in item
            assert "mp4_file_url" in item
            assert "season_index" in item
            assert "episode_index" in item
            assert "media_title" in item
            assert item.get("media_folder_mp4") is not None
            assert item.get("mp4_output_file_name") is not None
            assert item.get("mp4_show_title") is not None
            assert item.get("mp4_file_url") is not None
            assert item.get("season_index") is not None
            assert item.get("episode_index") is not None
            assert item.get("media_title") is not None
            assert isinstance(item.get("media_folder_mp4"), str)
            assert isinstance(item.get("mp4_output_file_name"), str)
            assert isinstance(item.get("mp4_show_title"), str)
            assert isinstance(item.get("mp4_file_url"), str)
            assert isinstance(item.get("season_index"), int)
            assert isinstance(item.get("episode_index"), int)
            assert isinstance(item.get("media_title"), str)

            assert item.get("media_folder_mp4")
            assert item.get("mp4_output_file_name")
            assert item.get("mp4_show_title")
            assert item.get("mp4_file_url")
            assert item.get("season_index")
            assert item.get("episode_index")
            assert item.get("media_title")

            assert "input" in item.get("media_folder_mp4")
            assert "S" in item.get("media_folder_mp4")
            assert "E" in item.get("media_folder_mp4")
            assert ".mp4" in item.get("media_folder_mp4")
            assert "output" in item.get("mp4_output_file_name")
            assert "Season " in item.get("mp4_output_file_name")
            assert " - " in item.get("mp4_output_file_name")
            assert ".mp4" in item.get("mp4_output_file_name")

            assert item.get("mp4_show_title") in item.get("media_folder_mp4")
            assert item.get("media_folder_mp4").count(item.get("mp4_show_title")) == 1
            assert str(item.get("season_index")) in item.get("media_folder_mp4")
            assert item.get("media_folder_mp4").count(str(item.get("season_index"))) >= 1
            assert str(item.get("episode_index")) in item.get("media_folder_mp4")
            assert item.get("media_folder_mp4").count(str(item.get("episode_index"))) >= 1
            assert item.get("mp4_show_title") in item.get("mp4_output_file_name")
            assert item.get("mp4_output_file_name").count(item.get("mp4_show_title")) == 2
            assert item.get("mp4_file_url") in item.get("mp4_output_file_name")
            assert item.get("mp4_output_file_name").count(item.get("mp4_file_url")) == 1
            assert str(item.get("season_index")) in item.get("mp4_output_file_name")
            assert item.get("mp4_output_file_name").count(str(item.get("season_index"))) >= 2
            assert str(item.get("episode_index")) in item.get("mp4_output_file_name")
            assert item.get("mp4_output_file_name").count(str(item.get("episode_index"))) >= 1

            assert "Season " in item.get("mp4_file_url")
            assert " - " in item.get("mp4_file_url")
            assert ".mp4" in item.get("mp4_file_url")
            assert item.get("mp4_show_title") in item.get("mp4_file_url")
            assert item.get("mp4_file_url").count(item.get("mp4_show_title")) == 2
            assert str(item.get("season_index")) in item.get("mp4_file_url")
            assert item.get("mp4_file_url").count(str(item.get("season_index"))) >= 2
            assert str(item.get("episode_index")) in item.get("mp4_file_url")
            assert item.get("mp4_file_url").count(str(item.get("episode_index"))) >= 1
