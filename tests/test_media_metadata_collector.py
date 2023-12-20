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
        self.new_media_path = self.media_paths[2]


class TestDBCreator(TestMediaMetadataCollectorSetup):

    def test_collect_new_tv_shows(self):
        expected_output = [{'media_folder_mp4': '..\\media_folder_modify\\input\\Animal Party\\S1\\E1.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Animal Party\\Season 1\\Animal Party - s1e1.mp4',
                            'media_title': 'sparkle'},
                           {'media_folder_mp4': '..\\media_folder_modify\\input\\Animal Party\\S1\\E2.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Animal Party\\Season 1\\Animal Party - s1e2.mp4',
                            'media_title': 'mysterious'},
                           {'media_folder_mp4': '..\\media_folder_modify\\input\\Animal Party\\S12\\E1.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Animal Party\\Season 12\\Animal Party - s12e1.mp4',
                            'media_title': 'sparkle'},
                           {'media_folder_mp4': '..\\media_folder_modify\\input\\Animal Party\\S12\\E2.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Animal Party\\Season 12\\Animal Party - s12e2.mp4',
                            'media_title': 'mysterious'},
                           {'media_folder_mp4': '..\\media_folder_modify\\input\\Animal Party\\S12\\E3.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Animal Party\\Season 12\\Animal Party - s12e3.mp4',
                            'media_title': 'dark'},
                           {'media_folder_mp4': '..\\media_folder_modify\\input\\Sparkles\\S1\\E1.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Sparkles\\Season 1\\Sparkles - s1e1.mp4',
                            'media_title': 'sparkle'},
                           {'media_folder_mp4': '..\\media_folder_modify\\input\\Sparkles\\S1\\E2.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Sparkles\\Season 1\\Sparkles - s1e2.mp4',
                            'media_title': 'mysterious'},
                           {'media_folder_mp4': '..\\media_folder_modify\\input\\Sparkles\\S2\\E1.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Sparkles\\Season 2\\Sparkles - s2e1.mp4',
                            'media_title': 'sparkle'},
                           {'media_folder_mp4': '..\\media_folder_modify\\input\\Sparkles\\S2\\E2.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Sparkles\\Season 2\\Sparkles - s2e2.mp4',
                            'media_title': 'mysterious'},
                           {'media_folder_mp4': '..\\media_folder_modify\\input\\Sparkles\\S2\\E3.mp4',
                            'mp4_output_file_name': '..\\media_folder_modify\\output\\Sparkles\\Season 2\\Sparkles - s2e3.mp4',
                            'media_title': 'dark'}]

        generated_result = md_collector.collect_new_tv_shows(self.new_media_path)
        print(generated_result)
        assert len(generated_result) == 10
        for item in generated_result:
            assert "media_folder_mp4" in item
            assert "mp4_output_file_name" in item
            assert "media_title" in item
            assert item.get("media_folder_mp4") is not None
            assert item.get("mp4_output_file_name") is not None
            assert item.get("media_title") is not None
        assert generated_result == expected_output

    def test_get_new_title_txt_files(self):
        media_path_info = self.media_paths[2]
        media_folder_path = md_collector.get_new_media_folder_path(media_path_info)
        print(media_folder_path)
        media_folder_titles = md_collector.get_title_txt_files(media_folder_path)
        assert len(media_folder_titles) == 4
        for key, value in media_folder_titles.items():
            print(value)
            assert isinstance(key, str)
            assert isinstance(value, list)

    def test_get_tv_show_title_txt_files(self):
        media_path_info = self.media_paths[0]
        media_folder_path = pathlib.Path(media_path_info.get("media_folder_path"))
        media_folder_titles = md_collector.get_title_txt_files(media_folder_path)
        print(media_folder_titles)
        assert len(media_folder_titles) == 5
        for key, value in media_folder_titles.items():
            print(value)
            assert isinstance(key, str)
            assert isinstance(value, list)

    def test_collect_tv_shows_new(self):
        result = md_collector.collect_tv_shows(self.media_paths[0])
        print(result)
        assert result

    def test_collect_tv_shows(self):
        result = md_collector.collect_tv_shows(self.media_paths[0])
        print(result)
        assert result
        assert len(result) == 13
        for item in result:
            assert "mp4_show_title" in item
            assert "mp4_file_url" in item
            assert "season_index" in item
            assert "episode_index" in item
            assert item.get("mp4_show_title") is not None
            assert item.get("mp4_file_url") is not None
            assert item.get("season_index") is not None
            assert item.get("episode_index") is not None

    def test_collect_movies(self):
        result = md_collector.collect_movies(self.media_paths[1])
        print(result)
        assert result
        assert len(result) == 5
        for item in result:
            assert "mp4_show_title" in item
            assert "mp4_file_url" in item
