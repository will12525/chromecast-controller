from unittest import TestCase
import os

import config_file_handler
from database_handler.create_database import DBCreator
from database_handler.database_handler import DatabaseHandler


class TestDBCreatorInit(TestCase):
    DB_PATH = "media_metadata.db"

    def setUp(self) -> None:
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)
        self.media_paths = config_file_handler.load_js_file()
        with DBCreator() as db_connection:
            db_connection.create_db()


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
        with DBCreator() as db_setter_connection, DatabaseHandler() as db_getter_connection:
            set_media_info = self.media_paths[0]
            media_directory_id = db_setter_connection.setup_media_directory(set_media_info)
            media_directory_info_list = db_getter_connection.get_media_folder_path(media_directory_id)
            print(media_directory_info_list)
            assert isinstance(media_directory_info_list, list)
            media_directory_info = media_directory_info_list[0]
            assert media_directory_id == media_directory_info.get("id")
            assert set_media_info.get("media_type") == media_directory_info.get("media_type")
            assert set_media_info.get("media_folder_path") == media_directory_info.get("media_folder_path")
            assert set_media_info.get("media_folder_url") == media_directory_info.get("media_folder_url")
            media_directory_id = db_setter_connection.setup_media_directory(self.media_paths[1])
            assert media_directory_id == 2

    def test_setup_new_tv_show_media_directory(self):
        with DBCreator() as db_setter_connection, DatabaseHandler() as db_getter_connection:
            set_media_info = self.media_paths[2]
            media_directory_id = db_setter_connection.setup_media_directory(set_media_info)
            media_directory_info_list = db_getter_connection.get_media_folder_path(media_directory_id)
            print(media_directory_info_list)
            assert isinstance(media_directory_info_list, list)
            media_directory_info = media_directory_info_list[0]
            assert media_directory_id == media_directory_info.get("id")
            assert set_media_info.get("media_type") == media_directory_info.get("media_type")
            assert set_media_info.get("media_folder_path") == media_directory_info.get("media_folder_path")
            assert set_media_info.get("media_folder_url") == media_directory_info.get("media_folder_url")
            media_directory_id = db_setter_connection.setup_media_directory(self.media_paths[1])
            assert media_directory_id == 2

    def test_add_media_directory(self):
        with DBCreator() as db_setter_connection, DatabaseHandler() as db_getter_connection:
            set_media_info = self.media_paths[0]
            media_directory_id = db_setter_connection.add_media_directory(set_media_info)
            media_directory_info_list = db_getter_connection.get_media_folder_path(media_directory_id)
            print(media_directory_info_list)
            assert isinstance(media_directory_info_list, list)
            media_directory_info = media_directory_info_list[0]
            assert media_directory_id == media_directory_info.get("id")
            assert set_media_info.get("media_type") == media_directory_info.get("media_type")
            assert set_media_info.get("media_folder_path") == media_directory_info.get("media_folder_path")
            assert set_media_info.get("media_folder_url") == media_directory_info.get("media_folder_url")
            print(db_setter_connection.add_media_directory(set_media_info))
            assert not db_setter_connection.add_media_directory(set_media_info)

    def test_add_playlist(self):
        with DBCreator() as db_connection:
            playlist_id = db_connection.add_playlist("Vampire")
            assert playlist_id == 1
            playlist_id = db_connection.add_playlist("Warewolf")
            assert playlist_id == 2
            playlist_id = db_connection.add_playlist("Human")
            assert playlist_id == 3
            playlist_id = db_connection.add_playlist("Human")
            assert playlist_id == 3
            playlist_id = db_connection.add_playlist("Human")
            assert playlist_id == 3
            playlist_id = db_connection.add_playlist("Human")
            assert playlist_id == 3
            playlist_id = db_connection.add_playlist("Warewolf")
            assert playlist_id == 2
            for i in range(20):
                playlist_id = db_connection.add_playlist("Warewolf")
                assert playlist_id == 2
            playlist_id = db_connection.add_playlist("Vampire")
            assert playlist_id == 1

    def test_add_media_to_playlist(self):
        with DBCreator() as db_connection:
            set_media_info = self.media_paths[0]
            media_directory_id = db_connection.add_media_directory(set_media_info)

            (playlist_id, tv_show_id) = db_connection.add_tv_show("Vampire")
            assert playlist_id == tv_show_id == 1
            season_id = db_connection.add_season(tv_show_id, 1)
            assert season_id == 1
            media_id = db_connection.add_media(media_directory_id, "Episode 1", "../e1.mp4", season_id, tv_show_id)
            assert media_id == 1
            media_id_2 = db_connection.add_media(media_directory_id, "Episode 2", "../e2.mp4", season_id, tv_show_id)
            assert media_id_2 == 2
            playlist_media_id = db_connection.add_media_to_playlist(playlist_id, media_id, 1001)
            assert playlist_media_id == 1
            playlist_media_id = db_connection.add_media_to_playlist(playlist_id, media_id_2, 2002)
            assert playlist_media_id == 2

    def test_add_media(self):
        set_media_info = self.media_paths[0]
        with DBCreator() as db_connection:
            media_directory_id = db_connection.add_media_directory(set_media_info)

            (playlist_id, tv_show_id) = db_connection.add_tv_show("Vampire")
            assert playlist_id == tv_show_id == 1
            season_id = db_connection.add_season(tv_show_id, 1)
            assert season_id == 1
            media_id = db_connection.add_media(media_directory_id, "Episode 1", "../e1.mp4", season_id, tv_show_id)
            assert media_id == 1
            media_id = db_connection.add_media(media_directory_id, "Episode 2", "../e2.mp4", season_id, tv_show_id)
            assert media_id == 2
            media_id = db_connection.add_media(media_directory_id, "Episode 2", "../e2.mp4", season_id, tv_show_id)
            assert media_id == 2
            media_id = db_connection.add_media(media_directory_id, "Episode 3", "../e3.mp4", season_id, tv_show_id)
            assert media_id == 3
            media_id = db_connection.add_media(media_directory_id, "Episode 1", "../e1.mp4", season_id, tv_show_id)
            assert media_id == 1

    def test_add_season(self):
        with DBCreator() as db_connection:
            (playlist_id, tv_show_id) = db_connection.add_tv_show("Vampire")
            assert playlist_id == tv_show_id == 1
            season_id = db_connection.add_season(tv_show_id, 1)
            assert season_id == 1
            season_id = db_connection.add_season(tv_show_id, 2)
            assert season_id == 2
            season_id = db_connection.add_season(tv_show_id, 3)
            assert season_id == 3
            season_id = db_connection.add_season(tv_show_id, 2)
            assert season_id == 2
            season_id = db_connection.add_season(tv_show_id, 1)
            assert season_id == 1

    def test_add_tv_show(self):
        with DBCreator() as db_connection:
            (playlist_id, tv_show_id) = db_connection.add_tv_show("Vampire")
            assert playlist_id == tv_show_id == 1
            (playlist_id, tv_show_id) = db_connection.add_tv_show("Warewolf")
            assert playlist_id == tv_show_id == 2
            (playlist_id, tv_show_id) = db_connection.add_tv_show("Human")
            assert playlist_id == tv_show_id == 3
            for i in range(2000):
                playlist_id = db_connection.add_playlist("Warewolf")
                assert playlist_id == 2
            (playlist_id, tv_show_id) = db_connection.add_tv_show("Human")
            assert playlist_id == tv_show_id == 3
            (playlist_id, tv_show_id) = db_connection.add_tv_show("Warewolf")
            assert playlist_id == tv_show_id == 2
