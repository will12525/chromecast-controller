import json
from unittest import TestCase
import os
from database_handler.database_handler import DatabaseHandler
from database_handler.create_database import MediaType


class TestDatabaseHandler(TestCase):
    SERVER_URL_TV_SHOWS = "http://192.168.1.200:8000/tv_shows/"
    MEDIA_FOLDER_PATH = "../media_folder_sample/"
    DB_PATH = "media_metadata.db"

    def setUp(self) -> None:
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)
        media_paths = [{"type": MediaType.TV_SHOW, "path": self.MEDIA_FOLDER_PATH, "url": self.SERVER_URL_TV_SHOWS}]
        self.db_handler = DatabaseHandler(media_paths)


class TestDatabaseHandlerFunctions(TestDatabaseHandler):

    def test_get_next_url(self):
        print("Next URL")

        url = self.db_handler.get_next_media_metadata(1, 1)
        print(url)
        assert url
        assert url.get("id") == 2
        assert url.get("season_id") == 1
        assert url.get("tv_show_id") == 1
        assert url.get("playlist_id") == 1
        assert url.get("name") == "Episode 2"
        assert ".mp4" in url.get("path")
        print(json.dumps(url, indent=4))

    def test_get_media_metadata(self):
        print("Current URL")

        url = self.db_handler.get_media_metadata(1)
        print(url)
        assert url
        assert url.get("id") == 1
        assert url.get("season_id") == 1
        assert url.get("tv_show_id") == 1
        assert url.get("playlist_id") == 1
        assert url.get("name") == "Episode 1"
        assert ".mp4" in url.get("path")
        print(json.dumps(url, indent=4))

    def test_close(self):
        pass

    def test_get_tv_show_name(self):
        result = self.db_handler.get_tv_show_name(1)
        assert isinstance(result, str)

    def test_get_movie_name_list(self):
        result = self.db_handler.get_movie_name_list()
        print(result)

    def test_get_tv_show_name_list(self):
        result = self.db_handler.get_tv_show_name_list()
        print(result)
        assert result
        assert 3 == len(result)
        assert isinstance(result[0], dict)
        assert result[0].get("id")
        assert result[0].get("name")

    def test_get_tv_show_season_name_list(self):
        result = self.db_handler.get_tv_show_season_name_list(1)
        print(result)
        assert result
        assert 2 == len(result)
        assert isinstance(result[0], dict)
        assert result[0].get("id")
        assert result[0].get("name")

    def test_get_tv_show_season_episode_name_list(self):
        result = self.db_handler.get_tv_show_season_episode_name_list(1)
        print(result)
        assert result
        assert 2 == len(result)
        assert isinstance(result[0], dict)
        assert result[0].get("id")
        assert result[0].get("name")

    def test_get_tv_show_metadata(self):
        result = self.db_handler.get_tv_show_metadata(1)
        assert result
        assert isinstance(result, dict)
        assert result.get("id")
        assert result.get("name")
        assert result.get("season_count")
        assert result.get("episode_count")

    def test_get_tv_show_season_metadata(self):
        result = self.db_handler.get_tv_show_season_metadata(1)
        print(result)
        assert result
        assert isinstance(result, dict)
        assert result.get("name")
        assert result.get("id")
        assert result.get("name")
        assert result.get("episode_count")
