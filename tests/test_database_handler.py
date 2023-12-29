import json
from unittest import TestCase

import config_file_handler
from database_handler.create_database import DBCreator
from database_handler.database_handler import DatabaseHandler, ContentType, GET_MOVIE_TITLES, GET_TV_SHOW_TITLES, \
    GET_TV_SHOW_SEASON_TITLES, GET_TV_SHOW_SEASON_EPISODE_TITLES


class TestDatabaseHandler(TestCase):
    DB_PATH = "media_metadata.db"

    db_handler = None

    media_paths = None

    def setUp(self) -> None:
        # IMPORTANT: Delete DB once before running
        # if os.path.exists(self.DB_PATH):
        #     os.remove(self.DB_PATH)

        self.media_paths = config_file_handler.load_js_file()
        assert self.media_paths
        assert isinstance(self.media_paths, list)
        assert len(self.media_paths) == 3
        with DBCreator() as db_connection:
            db_connection.create_db()
            for media_path in self.media_paths:
                db_connection.setup_media_directory(media_path)


class TestDatabaseHandlerFunctions(TestDatabaseHandler):

    def test_next_content_type(self):
        content_type = ContentType.TV
        content_type = content_type.get_next()
        assert content_type == ContentType.TV_SHOW
        content_type = content_type.get_next()
        assert content_type == ContentType.SEASON
        content_type = content_type.get_next()
        assert content_type == ContentType.MEDIA

    def test_get_next_url(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_next_in_playlist_media_metadata(1, 1)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get("id") == 2
            assert metadata.get("tv_show_id") == 1
            assert metadata.get("season_id") == 1
            assert metadata.get("media_folder_path_id") == 1
            assert metadata.get("media_title") == "mysterious"
            assert ".mp4" in metadata.get("path")
            assert metadata.get("media_type") == 1
            assert metadata.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
            assert metadata.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
            assert metadata.get("playlist_id") == 1
            assert metadata.get("tv_show_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"

    def test_get_previous_url(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_previous_in_playlist_media_metadata(1, 1)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get("id") == 5
            assert metadata.get("tv_show_id") == 1
            assert metadata.get("season_id") == 2
            assert metadata.get("media_folder_path_id") == 1
            assert metadata.get("media_title") == "dark"
            assert ".mp4" in metadata.get("path")
            assert metadata.get("media_type") == 1
            assert metadata.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
            assert metadata.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
            assert metadata.get("playlist_id") == 1
            assert metadata.get("tv_show_title") == "Vampire"
            assert metadata.get("season_title") == "Season 2"

            metadata = db_connection.get_previous_in_playlist_media_metadata(3, 1)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get("id") == 2
            assert metadata.get("tv_show_id") == 1
            assert metadata.get("season_id") == 1
            assert metadata.get("media_folder_path_id") == 1
            assert metadata.get("media_title") == "mysterious"
            assert ".mp4" in metadata.get("path")
            assert metadata.get("media_type") == 1
            assert metadata.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
            assert metadata.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
            assert metadata.get("playlist_id") == 1
            assert metadata.get("tv_show_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"

    def test_get_media_metadata(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(ContentType.MEDIA.value, 1)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get("id") == 1
            assert metadata.get("tv_show_id") == 1
            assert metadata.get("season_id") == 1
            assert metadata.get("media_folder_path_id") == 1
            assert metadata.get("media_title") == "sparkle"
            assert ".mp4" in metadata.get("path")
            assert metadata.get("media_type") == 1
            assert metadata.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
            assert metadata.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
            assert metadata.get("playlist_id") == 1
            assert metadata.get("tv_show_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"

    def test_close(self):
        pass

    def test_get_tv_show_title(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_tv_show_title(1)
            print(metadata)
            assert isinstance(metadata, str)
            assert metadata == "Vampire"

    def test_get_movie_title_list(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_title_list(ContentType.MEDIA, GET_MOVIE_TITLES)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert "id" in movie
                assert "media_title" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["media_title"], str)

    def test_get_tv_show_title_list(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_title_list(ContentType.TV_SHOW, GET_TV_SHOW_TITLES)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.TV_SHOW.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert "id" in movie
                assert "playlist_title" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["playlist_title"], str)

    def test_get_tv_show_season_title_list(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_title_list(ContentType.SEASON, GET_TV_SHOW_SEASON_TITLES, (1,))
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.SEASON.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert "id" in movie
                assert "season_title" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["season_title"], str)

    def test_get_tv_show_season_episode_title_list(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_title_list(ContentType.MEDIA, GET_TV_SHOW_SEASON_EPISODE_TITLES,
                                                            (1,))
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert "id" in movie
                assert "media_title" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["media_title"], str)

    def test_get_tv_show_metadata(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(ContentType.TV_SHOW.value, 1)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("container_content_type") == ContentType.TV.value
            assert metadata.get("id") == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("season_count") == 2
            assert metadata.get("episode_count") == 5
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert "id" in movie
                assert "season_title" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["season_title"], str)
            assert metadata.get("media_list_content_type") == ContentType.SEASON.value

    def test_get_tv_show_season_metadata(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(ContentType.SEASON.value, 1)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("container_content_type") == ContentType.TV_SHOW.value
            assert metadata.get("id") == 1
            assert metadata.get("tv_show_id") == 1
            assert metadata.get("tv_show_season_index") == 1
            assert metadata.get("playlist_id") == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"
            assert metadata.get("episode_count") == 2
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert "id" in movie
                assert "media_title" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["media_title"], str)
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_season_list_index(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_season_list_index(1)
            print(metadata)
            assert metadata
            assert isinstance(metadata, int)
            assert metadata == 1

    def test_get_movie_media_content(self):
        content_type = ContentType.MOVIE.value
        media_id = 14
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type, media_id)
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
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_tv_show_media_content(self):
        content_type = ContentType.TV.value
        media_id = 1
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type, media_id)
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
            assert metadata.get("media_list_content_type") == ContentType.TV_SHOW.value

    def test_get_tv_show_none_content(self):
        content_type = ContentType.TV_SHOW.value
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type)
            print(json.dumps(metadata, indent=4))
            assert not metadata
            assert isinstance(metadata, dict)

    def test_get_season_media_content(self):
        content_type = ContentType.TV_SHOW.value
        media_id = 1
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type, media_id)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("id") == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("season_count") == 2
            assert metadata.get("episode_count") == 5
            assert metadata.get("container_content_type") == ContentType.TV.value
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert "id" in movie
                assert "season_title" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["season_title"], str)
            assert metadata.get("media_list_content_type") == ContentType.SEASON.value

    def test_get_media_content(self):
        content_type = ContentType.SEASON.value
        media_id = 1
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type, media_id)
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
            assert metadata.get("container_content_type") == ContentType.TV_SHOW.value
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert "id" in movie
                assert "media_title" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["media_title"], str)
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_media_content_metadata(self):
        content_type = ContentType.MEDIA.value
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type, 1)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get("id") == 1
            assert metadata.get("tv_show_id") == 1
            assert metadata.get("season_id") == 1
            assert metadata.get("media_folder_path_id") == 1
            assert metadata.get("media_title") == "sparkle"
            assert ".mp4" in metadata.get("path")
            assert metadata.get("media_type") == 1
            assert metadata.get("media_folder_path") == self.media_paths[0].get("media_folder_path")
            assert metadata.get("media_folder_url") == self.media_paths[0].get("media_folder_url")
            assert metadata.get("playlist_id") == 1
            assert metadata.get("tv_show_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"

    def test_get_media_content_none(self):
        content_type = ContentType.PLAYLIST.value + 1
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type, 1)
            print(metadata)
            assert isinstance(metadata, dict)
            assert metadata == {}
