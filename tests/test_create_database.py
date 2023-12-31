from unittest import TestCase

import config_file_handler
from database_handler import common_objects, DBType
from database_handler.create_database import DBCreator
from database_handler.media_metadata_collector import get_playlist_list_index


class TestDBCreatorInit(TestCase):
    vampire_playlist = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                        common_objects.LIST_INDEX_COLUMN: 1}
    warewolf_playlist = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Werewolf",
                         common_objects.LIST_INDEX_COLUMN: 2}
    human_playlist = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Human",
                      common_objects.LIST_INDEX_COLUMN: 3}

    playlist_items_default = [vampire_playlist, warewolf_playlist, human_playlist]
    playlist_items = playlist_items_default.copy()

    vampire_season_1_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                                 common_objects.SEASON_INDEX_COLUMN: 1}
    vampire_season_2_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                                 common_objects.SEASON_INDEX_COLUMN: 2}
    vampire_season_3_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                                 common_objects.SEASON_INDEX_COLUMN: 3}

    season_items_default = [vampire_season_1_metadata, vampire_season_2_metadata, vampire_season_3_metadata]
    season_items = season_items_default.copy()

    vampire_season_1_episode_1_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                                           common_objects.MEDIA_TITLE_COLUMN: 'Episode 1',
                                           common_objects.PATH_COLUMN: '../S1/e1.mp4',
                                           common_objects.SEASON_INDEX_COLUMN: 1,
                                           common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(1, 1)}
    vampire_season_1_episode_2_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                                           common_objects.MEDIA_TITLE_COLUMN: 'Episode 2',
                                           common_objects.PATH_COLUMN: '../S1/e2.mp4',
                                           common_objects.SEASON_INDEX_COLUMN: 1,
                                           common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(1, 2)}
    vampire_season_1_episode_3_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                                           common_objects.MEDIA_TITLE_COLUMN: 'Episode 3',
                                           common_objects.PATH_COLUMN: '../S1/e3.mp4',
                                           common_objects.SEASON_INDEX_COLUMN: 1,
                                           common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(1, 3)}
    werewolf_season_2_episode_1_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Werewolf",
                                            common_objects.MEDIA_TITLE_COLUMN: 'Episode 1',
                                            common_objects.PATH_COLUMN: '../S2/e1.mp4',
                                            common_objects.SEASON_INDEX_COLUMN: 2,
                                            common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(2, 1)}
    werewolf_season_2_episode_2_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Werewolf",
                                            common_objects.MEDIA_TITLE_COLUMN: 'Episode 2',
                                            common_objects.PATH_COLUMN: '../S2/e2.mp4',
                                            common_objects.SEASON_INDEX_COLUMN: 2,
                                            common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(2, 2)}
    werewolf_season_2_episode_3_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Werewolf",
                                            common_objects.MEDIA_TITLE_COLUMN: 'Episode 3',
                                            common_objects.PATH_COLUMN: '../S2/e3.mp4',
                                            common_objects.SEASON_INDEX_COLUMN: 2,
                                            common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(2, 3)}
    media_items_default = [vampire_season_1_episode_1_metadata, vampire_season_1_episode_2_metadata,
                           vampire_season_1_episode_3_metadata, werewolf_season_2_episode_1_metadata,
                           werewolf_season_2_episode_2_metadata, werewolf_season_2_episode_3_metadata]
    media_items = media_items_default.copy()

    def setUp(self) -> None:
        self.media_directory_info = config_file_handler.load_js_file()


class TestDBCreator(TestDBCreatorInit):

    def test_setup_new_media_metadata(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()

            if media_path_data := config_file_handler.load_js_file():
                for media_path in media_path_data:
                    print(media_path)
                    db_setter_connection.setup_media_directory(media_path)

    def test_scan_media_directories(self):
        pass

    def test_setup_media_directory(self):
        set_media_info = self.media_directory_info[0]
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_directory_id = db_setter_connection.setup_media_directory(set_media_info)
            assert 2 == db_setter_connection.setup_media_directory(self.media_directory_info[1])
            media_directory_info = db_setter_connection.get_media_directory_info(media_directory_id)
        print(media_directory_info)
        assert isinstance(media_directory_info, dict)
        assert media_directory_id == media_directory_info.get(common_objects.ID_COLUMN)
        assert set_media_info.get(common_objects.MEDIA_TYPE_COLUMN) == media_directory_info.get(
            common_objects.MEDIA_TYPE_COLUMN)
        assert set_media_info.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == media_directory_info.get(
            common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
        assert set_media_info.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == media_directory_info.get(
            common_objects.MEDIA_DIRECTORY_URL_COLUMN)

    def test_setup_new_tv_show_media_directory(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_directory_info = self.media_directory_info[2]
            db_setter_connection.setup_media_directory(media_directory_info)
            assert media_directory_info.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
            assert isinstance(media_directory_info.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
            assert 1 == media_directory_info.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 10 == len(media_metadata)
            for item in media_metadata:
                print(item)
                assert isinstance(item, dict)
                assert len(item) == 6
                assert common_objects.ID_COLUMN in item
                assert common_objects.TV_SHOW_ID_COLUMN in item
                assert common_objects.SEASON_ID_COLUMN in item
                assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
                assert common_objects.MEDIA_TITLE_COLUMN in item
                assert common_objects.PATH_COLUMN in item
                assert item.get(common_objects.ID_COLUMN)
                assert item.get(common_objects.TV_SHOW_ID_COLUMN)
                assert item.get(common_objects.SEASON_ID_COLUMN)
                assert item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
                assert item.get(common_objects.MEDIA_TITLE_COLUMN)
                assert item.get(common_objects.PATH_COLUMN)
                assert isinstance(item.get(common_objects.ID_COLUMN), int)
                assert isinstance(item.get(common_objects.TV_SHOW_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.SEASON_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
                assert isinstance(item.get(common_objects.PATH_COLUMN), str)

    def test_setup_tv_show_media_directory(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_directory_info = self.media_directory_info[0]
            db_setter_connection.setup_media_directory(media_directory_info)
            assert media_directory_info.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
            assert isinstance(media_directory_info.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
            assert 1 == media_directory_info.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 13 == len(media_metadata)
            for item in media_metadata:
                print(item)
                assert isinstance(item, dict)
                assert len(item) == 6
                assert common_objects.ID_COLUMN in item
                assert common_objects.TV_SHOW_ID_COLUMN in item
                assert common_objects.SEASON_ID_COLUMN in item
                assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
                assert common_objects.MEDIA_TITLE_COLUMN in item
                assert common_objects.PATH_COLUMN in item
                assert item.get(common_objects.ID_COLUMN)
                assert item.get(common_objects.TV_SHOW_ID_COLUMN)
                assert item.get(common_objects.SEASON_ID_COLUMN)
                assert item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
                assert item.get(common_objects.MEDIA_TITLE_COLUMN)
                assert item.get(common_objects.PATH_COLUMN)
                assert isinstance(item.get(common_objects.ID_COLUMN), int)
                assert isinstance(item.get(common_objects.TV_SHOW_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.SEASON_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
                assert isinstance(item.get(common_objects.PATH_COLUMN), str)

    def test_setup_movie_media_directory(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_directory_info = self.media_directory_info[1]
            db_setter_connection.setup_media_directory(media_directory_info)
            assert media_directory_info.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
            assert isinstance(media_directory_info.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
            assert 1 == media_directory_info.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
            media_metadata = db_setter_connection.get_media_metadata_from_media_folder_path_id(media_directory_info)
            print(media_metadata)
            assert media_metadata
            assert isinstance(media_metadata, list)
            assert 5 == len(media_metadata)
            for item in media_metadata:
                assert isinstance(item, dict)
                assert len(item) == 6
                assert common_objects.ID_COLUMN in item
                assert common_objects.TV_SHOW_ID_COLUMN in item
                assert common_objects.SEASON_ID_COLUMN in item
                assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
                assert common_objects.MEDIA_TITLE_COLUMN in item
                assert common_objects.PATH_COLUMN in item
                assert item.get(common_objects.ID_COLUMN)
                assert not item.get(common_objects.TV_SHOW_ID_COLUMN)
                assert not item.get(common_objects.SEASON_ID_COLUMN)
                assert item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
                assert item.get(common_objects.MEDIA_TITLE_COLUMN)
                assert item.get(common_objects.PATH_COLUMN)
                assert isinstance(item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
                assert isinstance(item.get(common_objects.PATH_COLUMN), str)

    def test_scan_movie_media_directory(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_directory_info = self.media_directory_info[1]
            media_directory_info[
                common_objects.MEDIA_DIRECTORY_ID_COLUMN] = db_setter_connection.set_media_directory_info(
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
                assert common_objects.ID_COLUMN in item
                assert common_objects.TV_SHOW_ID_COLUMN in item
                assert common_objects.SEASON_ID_COLUMN in item
                assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
                assert common_objects.MEDIA_TITLE_COLUMN in item
                assert common_objects.PATH_COLUMN in item
                assert item.get(common_objects.ID_COLUMN)
                assert not item.get(common_objects.TV_SHOW_ID_COLUMN)
                assert not item.get(common_objects.SEASON_ID_COLUMN)
                assert item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
                assert item.get(common_objects.MEDIA_TITLE_COLUMN)
                assert item.get(common_objects.PATH_COLUMN)
                assert isinstance(item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
                assert isinstance(item.get(common_objects.PATH_COLUMN), str)

    def test_scan_tv_show_media_directory(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_directory_info = self.media_directory_info[0]
            media_directory_info[
                common_objects.MEDIA_DIRECTORY_ID_COLUMN] = db_setter_connection.set_media_directory_info(
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
                assert common_objects.ID_COLUMN in item
                assert common_objects.TV_SHOW_ID_COLUMN in item
                assert common_objects.SEASON_ID_COLUMN in item
                assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
                assert common_objects.MEDIA_TITLE_COLUMN in item
                assert common_objects.PATH_COLUMN in item
                assert item.get(common_objects.ID_COLUMN)
                assert item.get(common_objects.TV_SHOW_ID_COLUMN)
                assert item.get(common_objects.SEASON_ID_COLUMN)
                assert item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
                assert item.get(common_objects.MEDIA_TITLE_COLUMN)
                assert item.get(common_objects.PATH_COLUMN)
                assert isinstance(item.get(common_objects.ID_COLUMN), int)
                assert isinstance(item.get(common_objects.TV_SHOW_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.SEASON_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
                assert isinstance(item.get(common_objects.PATH_COLUMN), str)

    def test_add_tv_show_data(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_directory_info = self.media_directory_info[0]
            media_directory_info[
                common_objects.MEDIA_DIRECTORY_ID_COLUMN] = db_setter_connection.set_media_directory_info(
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
                assert common_objects.ID_COLUMN in item
                assert common_objects.TV_SHOW_ID_COLUMN in item
                assert common_objects.SEASON_ID_COLUMN in item
                assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
                assert common_objects.MEDIA_TITLE_COLUMN in item
                assert common_objects.PATH_COLUMN in item
                assert item.get(common_objects.ID_COLUMN)
                assert item.get(common_objects.TV_SHOW_ID_COLUMN)
                assert item.get(common_objects.SEASON_ID_COLUMN)
                assert item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
                assert item.get(common_objects.MEDIA_TITLE_COLUMN)
                assert item.get(common_objects.PATH_COLUMN)
                assert isinstance(item.get(common_objects.ID_COLUMN), int)
                assert isinstance(item.get(common_objects.TV_SHOW_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.SEASON_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
                assert isinstance(item.get(common_objects.PATH_COLUMN), str)

    def test_add_movie_data(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_directory_info = self.media_directory_info[1]
            media_directory_info[
                common_objects.MEDIA_DIRECTORY_ID_COLUMN] = db_setter_connection.set_media_directory_info(
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
                assert common_objects.ID_COLUMN in item
                assert common_objects.TV_SHOW_ID_COLUMN in item
                assert common_objects.SEASON_ID_COLUMN in item
                assert common_objects.MEDIA_DIRECTORY_ID_COLUMN in item
                assert common_objects.MEDIA_TITLE_COLUMN in item
                assert common_objects.PATH_COLUMN in item
                assert item.get(common_objects.ID_COLUMN) == index
                assert not item.get(common_objects.TV_SHOW_ID_COLUMN)
                assert not item.get(common_objects.SEASON_ID_COLUMN)
                assert item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN)
                assert item.get(common_objects.MEDIA_TITLE_COLUMN)
                assert item.get(common_objects.PATH_COLUMN)
                assert isinstance(item.get(common_objects.MEDIA_DIRECTORY_ID_COLUMN), int)
                assert isinstance(item.get(common_objects.MEDIA_TITLE_COLUMN), str)
                assert isinstance(item.get(common_objects.PATH_COLUMN), str)

    def test_set_media_directory_info(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            set_media_directory_info = self.media_directory_info[0]
            set_media_directory_info[common_objects.ID_COLUMN] = db_setter_connection.set_media_directory_info(
                set_media_directory_info)
            media_directory_info = db_setter_connection.get_media_directory_info(
                set_media_directory_info[common_objects.ID_COLUMN])
            assert not db_setter_connection.set_media_directory_info(set_media_directory_info)
        assert isinstance(media_directory_info, dict)
        assert set_media_directory_info[common_objects.ID_COLUMN] == media_directory_info.get(common_objects.ID_COLUMN)
        assert set_media_directory_info.get(common_objects.MEDIA_TYPE_COLUMN) == media_directory_info.get(
            common_objects.MEDIA_TYPE_COLUMN)
        assert set_media_directory_info.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == media_directory_info.get(
            common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
        assert set_media_directory_info.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == media_directory_info.get(
            common_objects.MEDIA_DIRECTORY_URL_COLUMN)
        assert set_media_directory_info == media_directory_info

    def test_set_playlist_metadata(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            for index, item in enumerate(self.playlist_items, 1):
                item_id = db_setter_connection.set_playlist_metadata(item)
                assert not db_setter_connection.set_playlist_metadata(item)

                item[common_objects.ID_COLUMN] = item_id
                assert index == item_id
                assert item.items() >= db_setter_connection.get_playlist_metadata(item_id).items()

                assert not db_setter_connection.get_playlist_metadata(item_id + 1)
            for i in range(20):
                assert not db_setter_connection.set_playlist_metadata(self.playlist_items[0])

    def test_set_tv_show_metadata(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            for index, item in enumerate(self.playlist_items, 1):
                item[common_objects.PLAYLIST_ID_COLUMN] = db_setter_connection.set_playlist_metadata(item)
                item_id = db_setter_connection.set_tv_show_metadata(item)
                assert not db_setter_connection.set_tv_show_metadata(item)

                item[common_objects.ID_COLUMN] = item_id
                assert index == item_id
                assert db_setter_connection.get_tv_show_metadata(item_id).items() <= item.items()

            for i in range(20):
                assert not db_setter_connection.set_tv_show_metadata(self.playlist_items[1])

    def test_set_season_metadata(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            playlist_id = None
            tv_show_id = None
            for index, item in enumerate(self.season_items, 1):
                if not playlist_id:
                    playlist_id = db_setter_connection.set_playlist_metadata(item)
                item[common_objects.PLAYLIST_ID_COLUMN] = playlist_id
                if not tv_show_id:
                    tv_show_id = db_setter_connection.set_tv_show_metadata(item)
                item[common_objects.TV_SHOW_ID_COLUMN] = tv_show_id

                item_id = db_setter_connection.set_season_metadata(item)
                assert not db_setter_connection.set_season_metadata(item)

                item[common_objects.ID_COLUMN] = item_id
                assert index == item_id
                assert db_setter_connection.get_season_metadata(item_id).items() <= item.items()

            for i in range(20):
                assert not db_setter_connection.set_season_metadata(self.playlist_items[1])

    def test_set_media_metadata(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_folder_path_id = None
            playlist_id = None
            tv_show_id = None
            season_id = None
            for index, item in enumerate(self.media_items, 1):
                if not media_folder_path_id:
                    media_folder_path_id = db_setter_connection.set_media_directory_info(self.media_directory_info[0])
                item[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_folder_path_id
                if not playlist_id:
                    playlist_id = db_setter_connection.set_playlist_metadata(item)
                item[common_objects.PLAYLIST_ID_COLUMN] = playlist_id
                if not tv_show_id:
                    tv_show_id = db_setter_connection.set_tv_show_metadata(item)
                item[common_objects.TV_SHOW_ID_COLUMN] = tv_show_id
                if not season_id:
                    season_id = db_setter_connection.set_season_metadata(item)
                item[common_objects.SEASON_ID_COLUMN] = season_id

                item_id = db_setter_connection.set_media_metadata(item)
                assert not db_setter_connection.set_media_metadata(item)

                item[common_objects.ID_COLUMN] = item_id
                assert index == item_id
                print(item)
                print(db_setter_connection.get_media_metadata(item_id))
                assert db_setter_connection.get_media_metadata(item_id).items() <= item.items()

            for i in range(20):
                assert not db_setter_connection.set_media_metadata(self.playlist_items[1])

    def test_add_media_to_playlist(self):
        with DBCreator(DBType.MEMORY) as db_setter_connection:
            db_setter_connection.create_db()
            media_folder_path_id = None
            playlist_id = None
            tv_show_id = None
            season_id = None
            for index, item in enumerate(self.media_items, 1):
                if not media_folder_path_id:
                    media_folder_path_id = db_setter_connection.set_media_directory_info(self.media_directory_info[0])
                item[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_folder_path_id
                if not playlist_id:
                    playlist_id = db_setter_connection.set_playlist_metadata(item)
                item[common_objects.PLAYLIST_ID_COLUMN] = playlist_id
                if not tv_show_id:
                    tv_show_id = db_setter_connection.set_tv_show_metadata(item)
                item[common_objects.TV_SHOW_ID_COLUMN] = tv_show_id
                if not season_id:
                    season_id = db_setter_connection.set_season_metadata(item)
                item[common_objects.SEASON_ID_COLUMN] = season_id
                media_id = db_setter_connection.set_media_metadata(item)
                item[common_objects.MEDIA_ID_COLUMN] = media_id
                item_id = db_setter_connection.add_media_to_playlist(item)
                assert not db_setter_connection.add_media_to_playlist(item)

                item[common_objects.ID_COLUMN] = item_id
                assert index == item_id
                assert db_setter_connection.get_playlist_entry(item_id).items() <= item.items()

            for i in range(20):
                assert not db_setter_connection.add_media_to_playlist(self.media_items[1])
