import json
import os
from unittest import TestCase

import config_file_handler
from database_handler import common_objects
from database_handler.create_database import DBCreator
from database_handler.database_handler import DatabaseHandler
from database_handler.common_objects import ContentType
import __init__


class TestDatabaseHandler(TestCase):
    DB_PATH = "media_metadata.db"

    db_handler = None

    media_paths = None

    def setUp(self) -> None:

        __init__.patch_get_file_hash(self)
        __init__.patch_get_ffmpeg_metadata(self)
        __init__.patch_move_media_file(self)
        __init__.patch_collect_tv_shows(self)
        __init__.patch_collect_new_tv_shows(self)
        __init__.patch_collect_movies(self)

        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)

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
        data = {common_objects.MEDIA_ID_COLUMN: 1, common_objects.PLAYLIST_ID_COLUMN: 1}
        data2 = {common_objects.MEDIA_ID_COLUMN: 5, common_objects.PLAYLIST_ID_COLUMN: 1}
        data3 = {common_objects.MEDIA_ID_COLUMN: 4, common_objects.PLAYLIST_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_next_in_playlist_media_metadata(data)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 2
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "mysterious"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Season 1\\Vampire - s01e002.mp4" == metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("season_title") == "Season 1"
            assert metadata.get("tv_show_title") == "Vampire"

            metadata = db_connection.get_next_in_playlist_media_metadata(data2)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "sparkle"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Season 1\\Vampire - s01e001.mp4" == metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("season_title") == "Season 1"
            assert metadata.get("tv_show_title") == "Vampire"

            metadata = db_connection.get_next_in_playlist_media_metadata(data3)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 5
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 2
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "dark"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Season 2\\Vampire - s02e003.mp4" == metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("season_title") == "Season 2"
            assert metadata.get("tv_show_title") == "Vampire"

    def test_get_previous_url(self):
        data = {common_objects.MEDIA_ID_COLUMN: 1, common_objects.PLAYLIST_ID_COLUMN: 1}
        data2 = {common_objects.MEDIA_ID_COLUMN: 3, common_objects.PLAYLIST_ID_COLUMN: 1}

        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_previous_in_playlist_media_metadata(data)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 5
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 2
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "dark"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Season 2\\Vampire - s02e003.mp4" == metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("season_title") == "Season 2"
            assert metadata.get("tv_show_title") == "Vampire"

            metadata = db_connection.get_previous_in_playlist_media_metadata(data2)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 2
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "mysterious"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert "\\Vampire\\Season 1\\Vampire - s01e002.mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("tv_show_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"

    def test_get_media_metadata(self):
        data = {common_objects.MEDIA_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=ContentType.MEDIA, params_dict=data)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
            assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
            # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "sparkle"
            assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
            assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("tv_show_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"

    def test_close(self):
        pass

    def test_get_tv_show_title(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_tv_show_title({common_objects.TV_SHOW_ID_COLUMN: 1})
            # print(metadata)
            assert isinstance(metadata, str)
            assert metadata == "Vampire"

    def test_get_movie_title_list(self):
        compare = [{'id': 13, 'media_title': 'Vampire - s01e001'}, {'id': 14, 'media_title': 'Vampire - s01e002'},
                   {'id': 15, 'media_title': 'Vampire - s02e001'}, {'id': 16, 'media_title': 'Vampire - s02e002'},
                   {'id': 17, 'media_title': 'Vampire - s02e003'}]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_title_list(ContentType.MOVIE)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert common_objects.MEDIA_TITLE_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                assert movie in compare

    def test_get_tv_show_title_list(self):
        movie_titles = [{'id': 4, 'playlist_title': 'Animal Party'}, {'id': 5, 'playlist_title': 'Sparkles'},
                        {'id': 1, 'playlist_title': 'Vampire'}, {'id': 2, 'playlist_title': 'Vans'},
                        {'id': 3, 'playlist_title': 'Warewolf'}]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_title_list(ContentType.TV)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.TV_SHOW.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "playlist_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["playlist_title"], str)
                assert movie in movie_titles

    def test_get_tv_show_season_title_list(self):
        compare = [{'id': 1, 'season_title': 'Season 1', 'season_index': 1},
                   {'id': 2, 'season_title': 'Season 2', 'season_index': 2}]
        data = {common_objects.TV_SHOW_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_title_list(ContentType.TV_SHOW, data)
            # # print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.SEASON.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "season_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["season_title"], str)
                assert movie in compare

    def test_get_tv_show_season_episode_title_list(self):
        compare = [{'id': 1, 'media_title': ''},
                   {'id': 2, 'media_title': ''}]
        data = {common_objects.SEASON_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_content_title_list(ContentType.SEASON, data)
            # # print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert common_objects.MEDIA_TITLE_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                assert movie in compare

    def test_get_tv_show_metadata(self):
        compare = [{'id': 1, 'season_title': 'Season 1', 'season_index': 1},
                   {'id': 2, 'season_title': 'Season 2', 'season_index': 2}]
        data = {common_objects.TV_SHOW_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=ContentType.TV_SHOW, params_dict=data)
            # print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("container_content_type") == ContentType.TV.value
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("season_count") == 2
            assert metadata.get("episode_count") == 5
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "season_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["season_title"], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.SEASON.value

    def test_get_movie_metadata(self):
        compare = [{'id': 13, 'media_title': 'Vampire - s01e001'}, {'id': 14, 'media_title': 'Vampire - s01e002'},
                   {'id': 15, 'media_title': 'Vampire - s02e001'}, {'id': 16, 'media_title': 'Vampire - s02e002'},
                   {'id': 17, 'media_title': 'Vampire - s02e003'}]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=ContentType.MOVIE)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_tv_show_season_metadata(self):
        compare = [{'id': 1, 'media_title': ''},
                   {'id': 2, 'media_title': ''}]
        data = {common_objects.SEASON_ID_COLUMN: 1}

        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=ContentType.SEASON, params_dict=data)
            # # print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get("container_content_type") == ContentType.TV_SHOW.value
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
            assert metadata.get(common_objects.SEASON_INDEX_COLUMN) == 1
            assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("season_title") == "Season 1"
            assert metadata.get("episode_count") == 2
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert common_objects.MEDIA_TITLE_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_season_list_index(self):
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_season_list_index({common_objects.SEASON_ID_COLUMN: 1})
            # print(metadata)
            assert metadata
            assert isinstance(metadata, int)
            assert metadata == 1

    def test_get_movie_media_content(self):
        content_type = ContentType.MOVIE
        media_id = 14
        compare = [{'id': 13, 'media_title': 'Vampire - s01e001'}, {'id': 14, 'media_title': 'Vampire - s01e002'},
                   {'id': 15, 'media_title': 'Vampire - s02e001'}, {'id': 16, 'media_title': 'Vampire - s02e002'},
                   {'id': 17, 'media_title': 'Vampire - s02e003'}]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type)
            print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert common_objects.MEDIA_TITLE_COLUMN in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
                # print(movie)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_tv_show_media_content(self):
        content_type = ContentType.TV
        media_id = 1
        compare = [{'id': 4, 'playlist_title': 'Animal Party'}, {'id': 5, 'playlist_title': 'Sparkles'},
                   {'id': 1, 'playlist_title': 'Vampire'}, {'id': 2, 'playlist_title': 'Vans'},
                   {'id': 3, 'playlist_title': 'Warewolf'}]
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type)
            # # print(json.dumps(metadata, indent=4))
            assert metadata
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 5
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "playlist_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["playlist_title"], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.TV_SHOW.value

    def test_get_tv_show_none_content(self):
        content_type = ContentType.TV_SHOW
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type)
            assert not metadata
            assert isinstance(metadata, dict)
            assert metadata == {}

    def test_get_season_media_content(self):
        content_type = ContentType.TV_SHOW
        media_id = 1
        compare = [{'id': 1, 'season_title': 'Season 1', 'season_index': 1},
                   {'id': 2, 'season_title': 'Season 2', 'season_index': 2}]
        params = {common_objects.TV_SHOW_ID_COLUMN: media_id}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=params)
            # # print(json.dumps(metadata, indent=4))
            assert metadata
            assert isinstance(metadata, dict)
            assert metadata.get(common_objects.ID_COLUMN) == 1
            assert metadata.get("playlist_title") == "Vampire"
            assert metadata.get("season_count") == 2
            assert metadata.get("episode_count") == 5
            assert metadata.get("container_content_type") == ContentType.TV.value
            assert metadata.get("media_list")
            assert isinstance(metadata.get("media_list"), list)
            assert len(metadata.get("media_list")) == 2
            for movie in metadata.get("media_list"):
                assert isinstance(movie, dict)
                assert common_objects.ID_COLUMN in movie
                assert "season_title" in movie
                assert isinstance(movie[common_objects.ID_COLUMN], int)
                assert isinstance(movie["season_title"], str)
                assert movie in compare
            assert metadata.get("media_list_content_type") == ContentType.SEASON.value

    def test_get_media_content(self):
        content_type = ContentType.SEASON
        media_id = 1
        compare = [{'id': 1, 'media_title': ''},
                   {'id': 2, 'media_title': ''}]
        params = {common_objects.SEASON_ID_COLUMN: media_id}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=params)
            # print(json.dumps(metadata, indent=4))
        assert metadata
        assert isinstance(metadata, dict)
        assert metadata.get(common_objects.ID_COLUMN) == 1
        assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
        assert metadata.get(common_objects.SEASON_INDEX_COLUMN) == 1
        assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
        assert metadata.get("playlist_title") == "Vampire"
        assert metadata.get("season_title") == "Season 1"
        assert metadata.get("episode_count") == 2
        assert metadata.get("container_content_type") == ContentType.TV_SHOW.value
        assert metadata.get("media_list")
        assert isinstance(metadata.get("media_list"), list)
        assert len(metadata.get("media_list")) == 2
        for movie in metadata.get("media_list"):
            assert isinstance(movie, dict)
            assert common_objects.ID_COLUMN in movie
            assert common_objects.MEDIA_TITLE_COLUMN in movie
            assert isinstance(movie[common_objects.ID_COLUMN], int)
            assert isinstance(movie[common_objects.MEDIA_TITLE_COLUMN], str)
            assert movie in compare
        assert metadata.get("media_list_content_type") == ContentType.MEDIA.value

    def test_get_media_content_metadata(self):
        content_type = ContentType.MEDIA
        data = {common_objects.MEDIA_ID_COLUMN: 1}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type, params_dict=data)
        print(json.dumps(metadata, indent=4))
        assert metadata
        assert metadata.get(common_objects.ID_COLUMN) == 1
        assert metadata.get(common_objects.TV_SHOW_ID_COLUMN) == 1
        assert metadata.get(common_objects.SEASON_ID_COLUMN) == 1
        assert metadata.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN) == 1
        # assert metadata.get(common_objects.MEDIA_TITLE_COLUMN) == "sparkle"
        assert ".mp4" in metadata.get(common_objects.PATH_COLUMN)
        assert metadata.get(common_objects.MEDIA_TYPE_COLUMN) == 5
        assert metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == self.media_paths[0].get(
            common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
        assert metadata.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == self.media_paths[0].get(
            common_objects.MEDIA_DIRECTORY_URL_COLUMN)
        assert metadata.get(common_objects.PLAYLIST_ID_COLUMN) == 1
        assert metadata.get("tv_show_title") == "Vampire"
        assert metadata.get("season_title") == "Season 1"

    def test_get_media_content_none(self):
        content_type = ContentType.PLAYLIST
        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_media_content(content_type=content_type)
        # print(metadata)
        assert isinstance(metadata, dict)
        assert metadata == {}

    def test_set_new_media_metadata(self):
        data = {common_objects.MEDIA_ID_COLUMN: 1, "description": "Hello world!",
                "image_url": "https://www.serebii.net/pokedex/evo/001.gif"}
        with DatabaseHandler() as db_connection:
            metadata = db_connection.set_new_media_metadata(content_type=ContentType.MEDIA, params=data)
            print(json.dumps(metadata, indent=4))

    def test_set_new_media_metadata_no_file(self):
        data = {common_objects.MEDIA_ID_COLUMN: 1, "description": "Hello world!",
                "image_url": "https://www.serebii.net/pokedex/evo/001.gif"}
        if os.path.exists("new_media_metadata_file.json"):
            os.remove("new_media_metadata_file.json")

        with DatabaseHandler() as db_connection:
            metadata = db_connection.set_new_media_metadata(content_type=ContentType.MEDIA, params=data)
        print(json.dumps(metadata, indent=4))

        assert metadata
        assert "description" in metadata
        assert "image_url" in metadata
        assert data["description"] == metadata["description"]
        assert data["image_url"] == metadata["image_url"]
        assert data.items() >= metadata.items()

    def test_set_season_new_media_metadata_no_file(self):
        data = {common_objects.SEASON_ID_COLUMN: 1, "description": "Hello world!, SEASON",
                "image_url": "https://www.serebii.net/pokedex/evo/001.gif"}

        if os.path.exists("new_media_metadata_file.json"):
            os.remove("new_media_metadata_file.json")

        with DatabaseHandler() as db_connection:
            metadata = db_connection.set_new_media_metadata(content_type=ContentType.SEASON, params=data)
        # print(json.dumps(metadata, indent=4))

        assert metadata
        assert "description" in metadata
        assert "image_url" in metadata
        assert data["description"] == metadata["description"]
        assert data["image_url"] == metadata["image_url"]
        assert data.items() >= metadata.items()

    def test_set_tv_show_new_media_metadata_no_file(self):
        data = {common_objects.TV_SHOW_ID_COLUMN: 1, "description": "Hello world!, TV_SHOW",
                "image_url": "https://www.serebii.net/pokedex/evo/001.gif"}

        if os.path.exists("new_media_metadata_file.json"):
            os.remove("new_media_metadata_file.json")

        with DatabaseHandler() as db_connection:
            metadata = db_connection.set_new_media_metadata(content_type=ContentType.TV_SHOW, params=data)
        print(json.dumps(metadata, indent=4))

        assert metadata
        assert "description" in metadata
        assert "image_url" in metadata
        assert data["description"] == metadata["description"]
        assert data["image_url"] == metadata["image_url"]
        assert data.items() >= metadata.items()

    def test_set_movie_new_media_metadata_no_file(self):
        data = {common_objects.MEDIA_ID_COLUMN: 16, "description": "Hello world!, MOVIE",
                "image_url": "https://www.serebii.net/pokedex/evo/001.gif"}

        if os.path.exists("new_media_metadata_file.json"):
            os.remove("new_media_metadata_file.json")

        with DatabaseHandler() as db_connection:
            metadata = db_connection.set_new_media_metadata(content_type=ContentType.MEDIA, params=data)
        # print(json.dumps(metadata, indent=4))

        assert metadata
        assert "description" in metadata
        assert "image_url" in metadata
        assert data["description"] == metadata["description"]
        assert data["image_url"] == metadata["image_url"]
        assert data.items() >= metadata.items()

    def test_get_movie_new_media_metadata_no_file(self):
        data = {common_objects.MEDIA_ID_COLUMN: 16, "description": "Hello world!, MOVIE",
                "image_url": "https://www.serebii.net/pokedex/evo/001.gif"}

        if os.path.exists("new_media_metadata_file.json"):
            os.remove("new_media_metadata_file.json")

        with DatabaseHandler() as db_connection:
            new_media_metadata = db_connection.set_new_media_metadata(content_type=ContentType.MEDIA, params=data)

        with DatabaseHandler() as db_connection:
            metadata = db_connection.get_new_media_metadata(content_type=ContentType.MEDIA, params=data)

        print(json.dumps(metadata, indent=4))

        assert metadata
        assert "description" in metadata
        assert "image_url" in metadata
        assert data["description"] == metadata["description"]
        assert data["image_url"] == metadata["image_url"]
        assert data.items() >= metadata.items()

        assert new_media_metadata == metadata
