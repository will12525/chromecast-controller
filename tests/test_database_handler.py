import json
from unittest import TestCase

import config_file_handler
import database_handler.database_handler as database_handler
from database_handler.create_database import DBCreator


class TestDatabaseHandler(TestCase):
    DB_PATH = "media_metadata.db"

    db_handler = None

    media_paths = None

    def setUp(self) -> None:
        # time.sleep(2)
        # if os.path.exists(self.DB_PATH):
        #     os.remove(self.DB_PATH)

        self.media_paths = config_file_handler.load_js_file()
        assert self.media_paths
        assert isinstance(self.media_paths, list)
        assert len(self.media_paths) == 3
        db_creator = DBCreator()
        for media_path in self.media_paths:
            db_creator.setup_media_directory(media_path)

        self.db_handler = database_handler.DatabaseHandler()

    def __del__(self):
        if self.db_handler:
            self.db_handler.close()


class TestDatabaseHandlerFunctions(TestDatabaseHandler):

    def test_next_content_type(self):
        content_type = database_handler.ContentType.TV
        content_type = content_type.get_next()
        assert content_type == database_handler.ContentType.TV_SHOW
        content_type = content_type.get_next()
        assert content_type == database_handler.ContentType.SEASON
        content_type = content_type.get_next()
        assert content_type == database_handler.ContentType.MEDIA

    def test_get_next_url(self):
        url = self.db_handler.get_next_in_playlist_media_metadata(1, 1)
        print(json.dumps(url, indent=4))
        assert url
        assert url.get("id") == 2
        assert url.get("tv_show_id") == 1
        assert url.get("season_id") == 1
        assert url.get("media_folder_path_id") == 1
        assert url.get("media_title") == "Episode 2"
        assert ".mp4" in url.get("path")
        assert url.get("media_type") == 1
        assert url.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
        assert url.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
        assert url.get("playlist_id") == 1
        assert url.get("tv_show_title") == "Vampire"
        assert url.get("season_title") == "Season 1"

    def test_get_previous_url(self):
        url = self.db_handler.get_previous_in_playlist_media_metadata(1, 1)
        print(json.dumps(url, indent=4))
        assert url
        assert url.get("id") == 5
        assert url.get("tv_show_id") == 1
        assert url.get("season_id") == 2
        assert url.get("media_folder_path_id") == 1
        assert url.get("media_title") == "Episode 3"
        assert ".mp4" in url.get("path")
        assert url.get("media_type") == 1
        assert url.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
        assert url.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
        assert url.get("playlist_id") == 1
        assert url.get("tv_show_title") == "Vampire"
        assert url.get("season_title") == "Season 2"

        url = self.db_handler.get_previous_in_playlist_media_metadata(3, 1)
        print(json.dumps(url, indent=4))
        assert url
        assert url.get("id") == 2
        assert url.get("tv_show_id") == 1
        assert url.get("season_id") == 1
        assert url.get("media_folder_path_id") == 1
        assert url.get("media_title") == "Episode 2"
        assert ".mp4" in url.get("path")
        assert url.get("media_type") == 1
        assert url.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
        assert url.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
        assert url.get("playlist_id") == 1
        assert url.get("tv_show_title") == "Vampire"
        assert url.get("season_title") == "Season 1"

    def test_get_media_metadata(self):
        url = self.db_handler.get_media_content(database_handler.ContentType.MEDIA.value, 1)
        print(json.dumps(url, indent=4))
        assert url
        assert url.get("id") == 1
        assert url.get("tv_show_id") == 1
        assert url.get("season_id") == 1
        assert url.get("media_folder_path_id") == 1
        assert url.get("media_title") == "Episode 1"
        assert ".mp4" in url.get("path")
        assert url.get("media_type") == 1
        assert url.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
        assert url.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
        assert url.get("playlist_id") == 1
        assert url.get("tv_show_title") == "Vampire"
        assert url.get("season_title") == "Season 1"

    def test_close(self):
        pass

    def test_get_tv_show_title(self):
        result = self.db_handler.get_tv_show_title(1)
        print(result)
        assert isinstance(result, str)
        assert result == "Vampire"

    def test_get_movie_title_list(self):
        result = self.db_handler.get_content_title_list(database_handler.ContentType.MEDIA,
                                                        database_handler.GET_MOVIE_TITLES)
        print(json.dumps(result, indent=4))
        assert result
        assert isinstance(result, dict)
        assert result.get("media_list_content_type") == database_handler.ContentType.MEDIA.value
        assert isinstance(result.get("media_list"), list)
        assert len(result.get("media_list")) == 5
        for movie in result.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "media_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["media_title"], str)

    def test_get_tv_show_title_list(self):
        result = self.db_handler.get_content_title_list(database_handler.ContentType.TV_SHOW,
                                                        database_handler.GET_TV_SHOW_TITLES)
        print(json.dumps(result, indent=4))
        assert result
        assert isinstance(result, dict)
        assert result.get("media_list_content_type") == database_handler.ContentType.TV_SHOW.value
        assert isinstance(result.get("media_list"), list)
        assert len(result.get("media_list")) == 5
        for movie in result.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "playlist_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["playlist_title"], str)

    def test_get_tv_show_season_title_list(self):
        result = self.db_handler.get_content_title_list(database_handler.ContentType.SEASON,
                                                        database_handler.GET_TV_SHOW_SEASON_TITLES, (1,))
        print(json.dumps(result, indent=4))
        assert result
        assert isinstance(result, dict)
        assert result.get("media_list_content_type") == database_handler.ContentType.SEASON.value
        assert isinstance(result.get("media_list"), list)
        assert len(result.get("media_list")) == 2
        for movie in result.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "season_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["season_title"], str)

    def test_get_tv_show_season_episode_title_list(self):
        result = self.db_handler.get_content_title_list(database_handler.ContentType.MEDIA,
                                                        database_handler.GET_TV_SHOW_SEASON_EPISODE_TITLES,
                                                        (1,))
        print(json.dumps(result, indent=4))
        assert result
        assert isinstance(result, dict)
        assert result.get("media_list_content_type") == database_handler.ContentType.MEDIA.value
        assert isinstance(result.get("media_list"), list)
        assert len(result.get("media_list")) == 2
        for movie in result.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "media_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["media_title"], str)

    def test_get_tv_show_metadata(self):
        result = self.db_handler.get_media_content(database_handler.ContentType.TV_SHOW.value, 1)
        print(json.dumps(result, indent=4))
        assert result
        assert isinstance(result, dict)
        assert result.get("container_content_type") == database_handler.ContentType.TV.value
        assert result.get("id") == 1
        assert result.get("playlist_title") == "Vampire"
        assert result.get("season_count") == 2
        assert result.get("episode_count") == 5
        assert result.get("media_list")
        assert isinstance(result.get("media_list"), list)
        assert len(result.get("media_list")) == 2
        for movie in result.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "season_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["season_title"], str)
        assert result.get("media_list_content_type") == database_handler.ContentType.SEASON.value

    def test_get_tv_show_season_metadata(self):
        result = self.db_handler.get_media_content(database_handler.ContentType.SEASON.value, 1)
        print(json.dumps(result, indent=4))
        assert result
        assert isinstance(result, dict)
        assert result.get("container_content_type") == database_handler.ContentType.TV_SHOW.value
        assert result.get("id") == 1
        assert result.get("tv_show_id") == 1
        assert result.get("tv_show_season_index") == 1
        assert result.get("playlist_id") == 1
        assert result.get("playlist_title") == "Vampire"
        assert result.get("season_title") == "Season 1"
        assert result.get("episode_count") == 2
        assert result.get("media_list")
        assert isinstance(result.get("media_list"), list)
        assert len(result.get("media_list")) == 2
        for movie in result.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "media_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["media_title"], str)
        assert result.get("media_list_content_type") == database_handler.ContentType.MEDIA.value

    def test_get_season_list_index(self):
        result = self.db_handler.get_season_list_index(1)
        print(result)
        assert result
        assert isinstance(result, int)
        assert result == 1

    def test_get_movie_media_content(self):
        content_type = database_handler.ContentType.MOVIE.value
        media_id = 14
        metadata = self.db_handler.get_media_content(content_type, media_id)
        print(json.dumps(metadata, indent=4))
        assert metadata
        assert metadata.get("media_list")
        assert isinstance(metadata.get("media_list"), list)
        assert len(metadata.get("media_list")) == 5
        for movie in metadata.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "media_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["media_title"], str)
        assert metadata.get("media_list_content_type") == database_handler.ContentType.MEDIA.value

    def test_get_tv_show_media_content(self):
        content_type = database_handler.ContentType.TV.value
        media_id = 1
        metadata = self.db_handler.get_media_content(content_type, media_id)
        print(json.dumps(metadata, indent=4))
        assert metadata
        assert metadata.get("media_list")
        assert isinstance(metadata.get("media_list"), list)
        assert len(metadata.get("media_list")) == 5
        for movie in metadata.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "playlist_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["playlist_title"], str)
        assert metadata.get("media_list_content_type") == database_handler.ContentType.TV_SHOW.value

    def test_get_tv_show_none_content(self):
        content_type = database_handler.ContentType.TV_SHOW.value
        metadata = self.db_handler.get_media_content(content_type)
        print(json.dumps(metadata, indent=4))
        assert not metadata
        assert isinstance(metadata, dict)

    def test_get_season_media_content(self):
        content_type = database_handler.ContentType.TV_SHOW.value
        media_id = 1
        metadata = self.db_handler.get_media_content(content_type, media_id)
        print(json.dumps(metadata, indent=4))
        assert metadata
        assert isinstance(metadata, dict)
        assert metadata.get("id") == 1
        assert metadata.get("playlist_title") == "Vampire"
        assert metadata.get("season_count") == 2
        assert metadata.get("episode_count") == 5
        assert metadata.get("container_content_type") == database_handler.ContentType.TV.value
        assert metadata.get("media_list")
        assert isinstance(metadata.get("media_list"), list)
        assert len(metadata.get("media_list")) == 2
        for movie in metadata.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "season_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["season_title"], str)
        assert metadata.get("media_list_content_type") == database_handler.ContentType.SEASON.value

    def test_get_media_content(self):
        content_type = database_handler.ContentType.SEASON.value
        media_id = 1
        metadata = self.db_handler.get_media_content(content_type, media_id)
        print(json.dumps(metadata, indent=4))
        assert metadata
        assert isinstance(metadata, dict)
        assert metadata.get("id") == 1
        assert metadata.get("tv_show_id") == 1
        assert metadata.get("tv_show_season_index") == 1
        assert metadata.get("playlist_id") == 1
        assert metadata.get("playlist_title") == "Vampire"
        assert metadata.get("season_title") == "Season 1"
        assert metadata.get("episode_count") == 2
        assert metadata.get("container_content_type") == database_handler.ContentType.TV_SHOW.value
        assert metadata.get("media_list")
        assert isinstance(metadata.get("media_list"), list)
        assert len(metadata.get("media_list")) == 2
        for movie in metadata.get("media_list"):
            assert isinstance(movie, dict)
            assert "id" in movie
            assert "media_title" in movie
            assert isinstance(movie["id"], int)
            assert isinstance(movie["media_title"], str)
        assert metadata.get("media_list_content_type") == database_handler.ContentType.MEDIA.value

    def test_get_media_content_metadata(self):
        content_type = database_handler.ContentType.MEDIA.value
        url = self.db_handler.get_media_content(content_type, 1)
        print(json.dumps(url, indent=4))
        assert url
        assert url.get("id") == 1
        assert url.get("tv_show_id") == 1
        assert url.get("season_id") == 1
        assert url.get("media_folder_path_id") == 1
        assert url.get("media_title") == "Episode 1"
        assert ".mp4" in url.get("path")
        assert url.get("media_type") == 1
        assert url.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
        assert url.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
        assert url.get("playlist_id") == 1
        assert url.get("tv_show_title") == "Vampire"
        assert url.get("season_title") == "Season 1"

    def test_get_media_content_none(self):
        content_type = database_handler.ContentType.PLAYLIST.value + 1
        url = self.db_handler.get_media_content(content_type, 1)
        print(url)
        assert isinstance(url, dict)
        assert url == {}
