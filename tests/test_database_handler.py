import json
from unittest import TestCase
import os
from database_handler.database_handler import DatabaseHandler
from database_handler.create_database import MediaType, DBCreator


class TestDatabaseHandler(TestCase):
    SERVER_URL_TV_SHOWS = "http://192.168.1.200:8000/tv_shows/"
    MEDIA_FOLDER_PATH = "../media_folder_sample/"
    DB_PATH = "media_metadata.db"

    def setUp(self) -> None:
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)
        media_paths = [{"media_type": MediaType.TV_SHOW.value, "media_folder_path": self.MEDIA_FOLDER_PATH,
                        "media_folder_url": self.SERVER_URL_TV_SHOWS}]
        db_creator = DBCreator()
        db_creator.setup_media_directory(media_paths[0])

        self.db_handler = DatabaseHandler()


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
        assert url.get("title") == "Episode 2"
        assert ".mp4" in url.get("path")
        print(json.dumps(url, indent=4))

    def test_get_previous_url(self):
        print("Next URL")

        url = self.db_handler.get_previous_media_metadata(1, 1)
        print(url)
        assert url
        assert url.get("id") == 5
        assert url.get("season_id") == 2
        assert url.get("tv_show_id") == 1
        assert url.get("playlist_id") == 1
        assert url.get("title") == "Episode 3"
        assert ".mp4" in url.get("path")
        print(json.dumps(url, indent=4))

        url = self.db_handler.get_previous_media_metadata(3, 1)
        print(url)
        assert url
        assert url.get("id") == 2
        assert url.get("season_id") == 1
        assert url.get("tv_show_id") == 1
        assert url.get("playlist_id") == 1
        assert url.get("title") == "Episode 2"
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
        assert url.get("title") == "Episode 1"
        assert ".mp4" in url.get("path")
        print(json.dumps(url, indent=4))

    def test_close(self):
        pass

    def test_get_tv_show_title(self):
        result = self.db_handler.get_tv_show_title(1)
        assert isinstance(result, str)

    def test_get_movie_title_list(self):
        result = self.db_handler.get_movie_title_list()
        print(result)

    def test_get_tv_show_title_list(self):
        result = self.db_handler.get_tv_show_title_list()
        print(result)
        assert result
        assert 3 == len(result)
        assert isinstance(result[0], dict)
        assert result[0].get("id")
        assert result[0].get("title")

    def test_get_tv_show_season_title_list(self):
        result = self.db_handler.get_tv_show_season_title_list(1)
        print(result)
        assert result
        assert 2 == len(result)
        assert isinstance(result[0], dict)
        assert result[0].get("id")
        assert isinstance(result[0].get("id"), int)
        assert result[0].get("title")
        assert isinstance(result[0].get("title"), str)

    def test_get_tv_show_season_episode_title_list(self):
        result = self.db_handler.get_tv_show_season_episode_title_list(1)
        print(result)
        assert result
        assert 2 == len(result)
        assert isinstance(result[0], dict)
        assert result[0].get("id")
        assert result[0].get("title")

    def test_get_tv_show_metadata(self):
        result = self.db_handler.get_tv_show_metadata(1)
        assert result
        assert isinstance(result, dict)
        assert result.get("id")
        assert result.get("title")
        assert result.get("season_count")
        assert result.get("episode_count")

    def test_get_tv_show_season_metadata(self):
        result = self.db_handler.get_tv_show_season_metadata(1)
        print(result)
        assert result
        assert isinstance(result, dict)
        assert result.get("id")
        assert result.get("tv_show_id")
        assert result.get("tv_show_season_index")
        assert result.get("playlist_id")
        assert result.get("title")
        assert result.get("sub_title")
        assert result.get("episode_count")

    def test_get_season_list_index(self):
        result = self.db_handler.get_season_list_index(1)
        assert result
        assert isinstance(result, int)
        assert result == 1
