from unittest import TestCase
import os

import config_file_handler
from database_handler import common_objects
from database_handler.create_database import DBCreator
from database_handler.database_handler import DatabaseHandler
from database_handler.media_metadata_collector import get_playlist_list_index


class TestDBCreatorInit(TestCase):
    DB_PATH = "media_metadata.db"

    vampire_playlist = {"id": None, common_objects.PLAYLIST_TITLE: "Vampire"}
    warewolf_playlist = {"id": None, common_objects.PLAYLIST_TITLE: "Werewolf"}
    human_playlist = {"id": None, common_objects.PLAYLIST_TITLE: "Human"}

    playlist_items_default = [vampire_playlist, warewolf_playlist, human_playlist]
    playlist_items = playlist_items_default.copy()

    vampire_season_1_metadata = {"id": None, common_objects.PLAYLIST_TITLE: "Vampire", 'season_index': 1}
    vampire_season_2_metadata = {"id": None, common_objects.PLAYLIST_TITLE: "Vampire", 'season_index': 2}
    vampire_season_3_metadata = {"id": None, common_objects.PLAYLIST_TITLE: "Vampire", 'season_index': 3}

    season_items_default = [vampire_season_1_metadata, vampire_season_2_metadata, vampire_season_3_metadata]
    season_items = season_items_default.copy()

    vampire_season_1_episode_1_metadata = {"id": None, common_objects.PLAYLIST_TITLE: "Vampire",
                                           'media_title': 'Episode 1', 'path': '../S1/e1.mp4', 'season_index': 1,
                                           'episode_index': 1, 'list_index': get_playlist_list_index(1, 1)}
    vampire_season_1_episode_2_metadata = {"id": None, common_objects.PLAYLIST_TITLE: "Vampire",
                                           'media_title': 'Episode 2', 'path': '../S1/e2.mp4', 'season_index': 2,
                                           'episode_index': 2, 'list_index': get_playlist_list_index(1, 2)}
    vampire_season_1_episode_3_metadata = {"id": None, common_objects.PLAYLIST_TITLE: "Vampire",
                                           'media_title': 'Episode 3', 'path': '../S1/e3.mp4', 'season_index': 3,
                                           'episode_index': 3, 'list_index': get_playlist_list_index(1, 3)}
    werewolf_season_2_episode_1_metadata = {"id": None, common_objects.PLAYLIST_TITLE: "Werewolf",
                                            'media_title': 'Episode 1', 'path': '../S2/e1.mp4', 'season_index': 1,
                                            'episode_index': 1, 'list_index': get_playlist_list_index(2, 1)}
    werewolf_season_2_episode_2_metadata = {"id": None, common_objects.PLAYLIST_TITLE: "Werewolf",
                                            'media_title': 'Episode 2', 'path': '../S2/e2.mp4', 'season_index': 2,
                                            'episode_index': 2, 'list_index': get_playlist_list_index(2, 2)}
    werewolf_season_2_episode_3_metadata = {"id": None, common_objects.PLAYLIST_TITLE: "Werewolf",
                                            'media_title': 'Episode 3', 'path': '../S2/e3.mp4', 'season_index': 3,
                                            'episode_index': 3, 'list_index': get_playlist_list_index(2, 3)}
    media_items_default = [vampire_season_1_episode_1_metadata, vampire_season_1_episode_2_metadata,
                           vampire_season_1_episode_3_metadata, werewolf_season_2_episode_1_metadata,
                           werewolf_season_2_episode_2_metadata, werewolf_season_2_episode_3_metadata]
    media_items = media_items_default.copy()

    def setUp(self) -> None:
        self.delete_db()
        self.media_directory_info = config_file_handler.load_js_file()
        with DBCreator() as db_connection:
            db_connection.create_db()

    def __del__(self):
        self.delete_db()

    def delete_db(self):
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)


class TestDBCreator(TestDBCreatorInit):

    def test_setup_new_media_metadata(self):
        with DBCreator() as db_connection:

            if media_path_data := config_file_handler.load_js_file():
                for media_path in media_path_data:
                    print(media_path)
                    db_connection.setup_media_directory(media_path)

    def test_scan_media_directories(self):
        pass

    def test_setup_media_directory(self):
        set_media_info = self.media_directory_info[0]
        with DBCreator() as db_setter_connection, DatabaseHandler() as db_getter_connection:
            media_directory_id = db_setter_connection.setup_media_directory(set_media_info)
            assert 2 == db_setter_connection.setup_media_directory(self.media_directory_info[1])
            media_directory_info = db_getter_connection.get_media_folder_path(media_directory_id)
        print(media_directory_info)
        assert isinstance(media_directory_info, dict)
        assert media_directory_id == media_directory_info.get("id")
        assert set_media_info.get("media_type") == media_directory_info.get("media_type")
        assert set_media_info.get("media_folder_path") == media_directory_info.get("media_folder_path")
        assert set_media_info.get("media_folder_url") == media_directory_info.get("media_folder_url")

    def test_setup_new_tv_show_media_directory(self):
        with DBCreator() as db_setter_connection:
            media_directory_info = self.media_directory_info[2]
            db_setter_connection.setup_media_directory(media_directory_info)
            assert media_directory_info.get("media_folder_path_id")
            assert isinstance(media_directory_info.get("media_folder_path_id"), int)
            assert 1 == media_directory_info.get("media_folder_path_id")
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 10 == len(media_metadata)
            for item in media_metadata:
                print(item)
                assert isinstance(item, dict)
                assert len(item) == 6
                assert 'id' in item
                assert 'tv_show_id' in item
                assert 'season_id' in item
                assert 'media_folder_path_id' in item
                assert 'media_title' in item
                assert 'path' in item
                assert item.get('id')
                assert item.get('tv_show_id')
                assert item.get('season_id')
                assert item.get('media_folder_path_id')
                assert item.get('media_title')
                assert item.get('path')
                assert isinstance(item.get('id'), int)
                assert isinstance(item.get('tv_show_id'), int)
                assert isinstance(item.get('season_id'), int)
                assert isinstance(item.get('media_folder_path_id'), int)
                assert isinstance(item.get('media_title'), str)
                assert isinstance(item.get('path'), str)

    def test_setup_tv_show_media_directory(self):
        with DBCreator() as db_setter_connection:
            media_directory_info = self.media_directory_info[0]
            db_setter_connection.setup_media_directory(media_directory_info)
            assert media_directory_info.get("media_folder_path_id")
            assert isinstance(media_directory_info.get("media_folder_path_id"), int)
            assert 1 == media_directory_info.get("media_folder_path_id")
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 13 == len(media_metadata)
            for item in media_metadata:
                print(item)
                assert isinstance(item, dict)
                assert len(item) == 6
                assert 'id' in item
                assert 'tv_show_id' in item
                assert 'season_id' in item
                assert 'media_folder_path_id' in item
                assert 'media_title' in item
                assert 'path' in item
                assert item.get('id')
                assert item.get('tv_show_id')
                assert item.get('season_id')
                assert item.get('media_folder_path_id')
                assert item.get('media_title')
                assert item.get('path')
                assert isinstance(item.get('id'), int)
                assert isinstance(item.get('tv_show_id'), int)
                assert isinstance(item.get('season_id'), int)
                assert isinstance(item.get('media_folder_path_id'), int)
                assert isinstance(item.get('media_title'), str)
                assert isinstance(item.get('path'), str)

    def test_setup_movie_media_directory(self):
        with DBCreator() as db_setter_connection:
            media_directory_info = self.media_directory_info[1]
            db_setter_connection.setup_media_directory(media_directory_info)
            assert media_directory_info.get("media_folder_path_id")
            assert isinstance(media_directory_info.get("media_folder_path_id"), int)
            assert 1 == media_directory_info.get("media_folder_path_id")
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 5 == len(media_metadata)
            for item in media_metadata:
                assert isinstance(item, dict)
                assert len(item) == 6
                assert 'id' in item
                assert 'tv_show_id' in item
                assert 'season_id' in item
                assert 'media_folder_path_id' in item
                assert 'media_title' in item
                assert 'path' in item
                assert item.get('id')
                assert not item.get('tv_show_id')
                assert not item.get('season_id')
                assert item.get('media_folder_path_id')
                assert item.get('media_title')
                assert item.get('path')
                assert isinstance(item.get('media_folder_path_id'), int)
                assert isinstance(item.get('media_title'), str)
                assert isinstance(item.get('path'), str)

    def test_scan_movie_media_directory(self):
        with DBCreator() as db_setter_connection:
            media_directory_info = self.media_directory_info[1]
            media_directory_info['media_folder_path_id'] = db_setter_connection.set_media_directory_info(
                media_directory_info)
            db_setter_connection.scan_media_directory(media_directory_info)
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 5 == len(media_metadata)
            for item in media_metadata:
                assert isinstance(item, dict)
                assert len(item) == 6
                assert 'id' in item
                assert 'tv_show_id' in item
                assert 'season_id' in item
                assert 'media_folder_path_id' in item
                assert 'media_title' in item
                assert 'path' in item
                assert item.get('id')
                assert not item.get('tv_show_id')
                assert not item.get('season_id')
                assert item.get('media_folder_path_id')
                assert item.get('media_title')
                assert item.get('path')
                assert isinstance(item.get('media_folder_path_id'), int)
                assert isinstance(item.get('media_title'), str)
                assert isinstance(item.get('path'), str)

    def test_scan_tv_show_media_directory(self):
        with DBCreator() as db_setter_connection:
            media_directory_info = self.media_directory_info[0]
            media_directory_info['media_folder_path_id'] = db_setter_connection.set_media_directory_info(
                media_directory_info)
            db_setter_connection.scan_media_directory(media_directory_info)
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 13 == len(media_metadata)
            for item in media_metadata:
                print(item)
                assert isinstance(item, dict)
                assert len(item) == 6
                assert 'id' in item
                assert 'tv_show_id' in item
                assert 'season_id' in item
                assert 'media_folder_path_id' in item
                assert 'media_title' in item
                assert 'path' in item
                assert item.get('id')
                assert item.get('tv_show_id')
                assert item.get('season_id')
                assert item.get('media_folder_path_id')
                assert item.get('media_title')
                assert item.get('path')
                assert isinstance(item.get('id'), int)
                assert isinstance(item.get('tv_show_id'), int)
                assert isinstance(item.get('season_id'), int)
                assert isinstance(item.get('media_folder_path_id'), int)
                assert isinstance(item.get('media_title'), str)
                assert isinstance(item.get('path'), str)

    def test_add_tv_show_data(self):
        with DBCreator() as db_setter_connection:
            media_directory_info = self.media_directory_info[0]
            media_directory_info['media_folder_path_id'] = db_setter_connection.set_media_directory_info(
                media_directory_info)
            db_setter_connection.add_tv_show_data(media_directory_info)
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 13 == len(media_metadata)
            for item in media_metadata:
                print(item)
                assert isinstance(item, dict)
                assert len(item) == 6
                assert 'id' in item
                assert 'tv_show_id' in item
                assert 'season_id' in item
                assert 'media_folder_path_id' in item
                assert 'media_title' in item
                assert 'path' in item
                assert item.get('id')
                assert item.get('tv_show_id')
                assert item.get('season_id')
                assert item.get('media_folder_path_id')
                assert item.get('media_title')
                assert item.get('path')
                assert isinstance(item.get('id'), int)
                assert isinstance(item.get('tv_show_id'), int)
                assert isinstance(item.get('season_id'), int)
                assert isinstance(item.get('media_folder_path_id'), int)
                assert isinstance(item.get('media_title'), str)
                assert isinstance(item.get('path'), str)

    def test_add_movie_data(self):
        with DBCreator() as db_setter_connection:
            media_directory_info = self.media_directory_info[1]
            media_directory_info['media_folder_path_id'] = db_setter_connection.set_media_directory_info(
                media_directory_info)
            db_setter_connection.add_movie_data(media_directory_info)
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 5 == len(media_metadata)
            for index, item in enumerate(media_metadata, 1):
                print(item)
                assert isinstance(item, dict)
                assert len(item) == 6
                assert 'id' in item
                assert 'tv_show_id' in item
                assert 'season_id' in item
                assert 'media_folder_path_id' in item
                assert 'media_title' in item
                assert 'path' in item
                assert item.get('id') == index
                assert not item.get('tv_show_id')
                assert not item.get('season_id')
                assert item.get('media_folder_path_id')
                assert item.get('media_title')
                assert item.get('path')
                assert isinstance(item.get('media_folder_path_id'), int)
                assert isinstance(item.get('media_title'), str)
                assert isinstance(item.get('path'), str)

    def test_set_media_directory_info(self):
        with DBCreator() as db_setter_connection:
            set_media_directory_info = self.media_directory_info[0]
            set_media_directory_info['id'] = db_setter_connection.set_media_directory_info(set_media_directory_info)
            media_directory_info = db_setter_connection.get_media_directory_info(set_media_directory_info['id'])
            assert not db_setter_connection.set_media_directory_info(set_media_directory_info)
        assert isinstance(media_directory_info, dict)
        assert set_media_directory_info['id'] == media_directory_info.get("id")
        assert set_media_directory_info.get("media_type") == media_directory_info.get("media_type")
        assert set_media_directory_info.get("media_folder_path") == media_directory_info.get("media_folder_path")
        assert set_media_directory_info.get("media_folder_url") == media_directory_info.get("media_folder_url")
        assert set_media_directory_info == media_directory_info

    def test_set_playlist_metadata(self):
        with DBCreator() as db_setter_connection:
            for index, item in enumerate(self.playlist_items, 1):
                item_id = db_setter_connection.set_playlist_metadata(item)
                assert not db_setter_connection.set_playlist_metadata(item)

                item['id'] = item_id
                assert index == item_id
                assert item == db_setter_connection.get_playlist_metadata(item_id)

                assert not db_setter_connection.get_playlist_metadata(item_id + 1)
            for i in range(20):
                assert not db_setter_connection.set_playlist_metadata(self.playlist_items[0])

    def test_set_tv_show_metadata(self):
        with DBCreator() as db_setter_connection:
            for index, item in enumerate(self.playlist_items, 1):
                item['playlist_id'] = db_setter_connection.set_playlist_metadata(item)
                item_id = db_setter_connection.set_tv_show_metadata(item)
                assert not db_setter_connection.set_tv_show_metadata(item)

                item['id'] = item_id
                assert index == item_id
                assert db_setter_connection.get_tv_show_metadata(item_id).items() <= item.items()

            for i in range(20):
                assert not db_setter_connection.set_tv_show_metadata(self.playlist_items[1])

    def test_set_season_metadata(self):
        with DBCreator() as db_setter_connection:
            playlist_id = None
            tv_show_id = None
            for index, item in enumerate(self.season_items, 1):
                if not playlist_id:
                    playlist_id = db_setter_connection.set_playlist_metadata(item)
                item['playlist_id'] = playlist_id
                if not tv_show_id:
                    tv_show_id = db_setter_connection.set_tv_show_metadata(item)
                item['tv_show_id'] = tv_show_id

                item_id = db_setter_connection.set_season_metadata(item)
                assert not db_setter_connection.set_season_metadata(item)

                item['id'] = item_id
                assert index == item_id
                assert db_setter_connection.get_season_metadata(item_id).items() <= item.items()

            for i in range(20):
                assert not db_setter_connection.set_season_metadata(self.playlist_items[1])

    def test_set_media_metadata(self):

        with DBCreator() as db_setter_connection:
            media_folder_path_id = None
            playlist_id = None
            tv_show_id = None
            season_id = None
            for index, item in enumerate(self.media_items, 1):
                if not media_folder_path_id:
                    media_folder_path_id = db_setter_connection.set_media_directory_info(self.media_directory_info[0])
                item['media_folder_path_id'] = media_folder_path_id
                if not playlist_id:
                    playlist_id = db_setter_connection.set_playlist_metadata(item)
                item['playlist_id'] = playlist_id
                if not tv_show_id:
                    tv_show_id = db_setter_connection.set_tv_show_metadata(item)
                item['tv_show_id'] = tv_show_id
                if not season_id:
                    season_id = db_setter_connection.set_season_metadata(item)
                item['season_id'] = season_id

                item_id = db_setter_connection.set_media_metadata(item)
                assert not db_setter_connection.set_media_metadata(item)

                item['id'] = item_id
                assert index == item_id
                print(item)
                print(db_setter_connection.get_media_metadata(item_id))
                assert db_setter_connection.get_media_metadata(item_id).items() <= item.items()

            for i in range(20):
                assert not db_setter_connection.set_media_metadata(self.playlist_items[1])

    def test_add_media_to_playlist(self):

        with DBCreator() as db_setter_connection:
            media_folder_path_id = None
            playlist_id = None
            tv_show_id = None
            season_id = None
            for index, item in enumerate(self.media_items, 1):
                if not media_folder_path_id:
                    media_folder_path_id = db_setter_connection.set_media_directory_info(self.media_directory_info[0])
                item['media_folder_path_id'] = media_folder_path_id
                if not playlist_id:
                    playlist_id = db_setter_connection.set_playlist_metadata(item)
                item['playlist_id'] = playlist_id
                if not tv_show_id:
                    tv_show_id = db_setter_connection.set_tv_show_metadata(item)
                item['tv_show_id'] = tv_show_id
                if not season_id:
                    season_id = db_setter_connection.set_season_metadata(item)
                item['season_id'] = season_id
                item['media_id'] = db_setter_connection.set_media_metadata(item)

                item_id = db_setter_connection.add_media_to_playlist(item)
                assert not db_setter_connection.add_media_to_playlist(item)

                item['id'] = item_id
                assert index == item_id
                assert db_setter_connection.get_playlist_entry(item_id).items() <= item.items()

            for i in range(20):
                assert not db_setter_connection.add_media_to_playlist(self.playlist_items[1])
