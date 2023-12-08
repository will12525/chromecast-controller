import json
import time
from unittest import TestCase
import os
from database_handler.database_handler import DatabaseHandler, ContentType
from database_handler.create_database import MediaType, DBCreator


class TestDatabaseHandler(TestCase):
    SERVER_URL_TV_SHOWS = "http://192.168.1.200:8000/tv_shows/"
    MEDIA_FOLDER_PATH = "../media_folder_sample"
    SERVER_URL_MOVIES = "http://192.168.1.200:8000/movies/"
    MOVIE_FOLDER_PATH = "../media_folder_movie"
    DB_PATH = "media_metadata.db"

    db_handler = None

    # media_path_data = None

    def setUp(self) -> None:
        # time.sleep(2)
        # if os.path.exists(self.DB_PATH):
        #     os.remove(self.DB_PATH)

        # media_path_data = config_file.load_js_file()
        # print(media_path_data)
        media_paths = [{"media_type": MediaType.TV_SHOW.value, "media_folder_path": self.MEDIA_FOLDER_PATH,
                        "media_folder_url": self.SERVER_URL_TV_SHOWS},
                       {"media_type": MediaType.MOVIE.value,
                        "media_folder_path": self.MOVIE_FOLDER_PATH,
                        "media_folder_url": self.SERVER_URL_MOVIES}]
        db_creator = DBCreator()
        db_creator.setup_media_directory(media_paths[0])
        db_creator.setup_media_directory(media_paths[1])

        self.db_handler = DatabaseHandler()

    def __del__(self):
        if self.db_handler:
            self.db_handler.close()


class TestDatabaseHandlerFunctions(TestDatabaseHandler):

    def test_get_next_url(self):
        print("Next URL")

        url = self.db_handler.get_next_media_metadata(1, 1)
        print(url)
        assert url
        assert url.get("id") == 2
        assert url.get("tv_show_id") == 1
        assert url.get("season_id") == 1
        assert url.get("media_folder_path_id") == 1
        assert url.get("title") == "Episode 2"
        assert ".mp4" in url.get("path")
        assert url.get("media_type") == 1
        assert url.get("media_folder_path") == self.MEDIA_FOLDER_PATH
        assert url.get("media_folder_url") == self.SERVER_URL_TV_SHOWS
        assert url.get("playlist_id") == 1
        assert url.get("tv_show_title") == "Hilda"
        assert url.get("season_title") == "Season 1"
        print(json.dumps(url, indent=4))

    def test_get_previous_url(self):
        print("Next URL")

        url = self.db_handler.get_previous_media_metadata(1, 1)
        print(url)
        assert url
        assert url.get("id") == 5
        assert url.get("tv_show_id") == 1
        assert url.get("season_id") == 2
        assert url.get("media_folder_path_id") == 1
        assert url.get("title") == "Episode 3"
        assert ".mp4" in url.get("path")
        assert url.get("media_type") == 1
        assert url.get("media_folder_path") == self.MEDIA_FOLDER_PATH
        assert url.get("media_folder_url") == self.SERVER_URL_TV_SHOWS
        assert url.get("playlist_id") == 1
        assert url.get("tv_show_title") == "Hilda"
        assert url.get("season_title") == "Season 2"
        print(json.dumps(url, indent=4))

        url = self.db_handler.get_previous_media_metadata(3, 1)
        print(url)
        assert url
        assert url.get("id") == 2
        assert url.get("tv_show_id") == 1
        assert url.get("season_id") == 1
        assert url.get("media_folder_path_id") == 1
        assert url.get("title") == "Episode 2"
        assert ".mp4" in url.get("path")
        assert url.get("media_type") == 1
        assert url.get("media_folder_path") == self.MEDIA_FOLDER_PATH
        assert url.get("media_folder_url") == self.SERVER_URL_TV_SHOWS
        assert url.get("playlist_id") == 1
        assert url.get("tv_show_title") == "Hilda"
        assert url.get("season_title") == "Season 1"
        print(json.dumps(url, indent=4))

    def test_get_media_metadata(self):
        print("Current URL")

        url = self.db_handler.get_media_metadata(1)
        print(url)
        assert url
        assert url.get("id") == 1
        assert url.get("tv_show_id") == 1
        assert url.get("season_id") == 1
        assert url.get("media_folder_path_id") == 1
        assert url.get("title") == "Episode 1"
        assert ".mp4" in url.get("path")
        assert url.get("media_type") == 1
        assert url.get("media_folder_path") == self.MEDIA_FOLDER_PATH
        assert url.get("media_folder_url") == self.SERVER_URL_TV_SHOWS
        assert url.get("playlist_id") == 1
        assert url.get("tv_show_title") == "Hilda"
        assert url.get("season_title") == "Season 1"
        print(json.dumps(url, indent=4))

    def test_close(self):
        pass

    def test_get_tv_show_title(self):
        result = self.db_handler.get_tv_show_title(1)
        print(result)
        assert isinstance(result, str)
        assert result == "Hilda"

    def test_get_movie_title_list(self):
        result = self.db_handler.get_movie_title_list()
        print(result)
        assert isinstance(result, list)

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
        print(result)
        assert result
        assert isinstance(result, dict)
        assert result.get("id") == 1
        assert result.get("title") == "Hilda"
        assert result.get("season_count") == 2
        assert result.get("episode_count") == 5

    def test_get_tv_show_season_metadata(self):
        result = self.db_handler.get_tv_show_season_metadata(1)
        print(result)
        assert result
        assert isinstance(result, dict)
        assert result.get("id") == 1
        assert result.get("tv_show_id") == 1
        assert result.get("tv_show_season_index") == 1
        assert result.get("playlist_id") == 1
        assert result.get("title") == "Hilda"
        assert result.get("sub_title") == "Season 1"
        assert result.get("episode_count") == 2

    def test_get_season_list_index(self):
        result = self.db_handler.get_season_list_index(1)
        assert result
        assert isinstance(result, int)
        assert result == 1

    def test_get_movie_media_content(self):
        content_type = ContentType.MOVIE
        media_id = 14
        metadata = self.db_handler.get_media_content(content_type, media_id)
        print(metadata)
        assert metadata

    def test_get_tv_show_media_content(self):
        content_type = ContentType.TV_SHOW
        media_id = 1
        metadata = self.db_handler.get_media_content(content_type, media_id)
        print(metadata)
        assert metadata

    def test_get_season_media_content(self):
        content_type = ContentType.SEASON
        media_id = 1
        metadata = self.db_handler.get_media_content(content_type, media_id)
        print(metadata)
        assert metadata

    def test_get_media_content(self):
        content_type = ContentType.MEDIA
        media_id = 1
        metadata = self.db_handler.get_media_content(content_type, media_id)
        print(metadata)
        assert metadata
