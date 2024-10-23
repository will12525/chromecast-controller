import json
import os
from unittest import TestCase

import config_file_handler
from database_handler import common_objects
from database_handler.common_objects import DBType
from database_handler.db_setter import DBCreatorV2
from database_handler.media_metadata_collector import get_playlist_list_index
import pytest_mocks


class TestDBCreatorInit(TestCase):
    vampire_playlist = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                        common_objects.LIST_INDEX_COLUMN: 1}
    werewolf_playlist = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Werewolf",
                         common_objects.LIST_INDEX_COLUMN: 2}
    human_playlist = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Human",
                      common_objects.LIST_INDEX_COLUMN: 3}

    playlist_items_default = [vampire_playlist, werewolf_playlist, human_playlist]
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
                                           common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(1, 1),
                                           common_objects.MD5SUM_COLUMN: '00000000000000001',
                                           common_objects.DURATION_COLUMN: 1}
    vampire_season_1_episode_2_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                                           common_objects.MEDIA_TITLE_COLUMN: 'Episode 2',
                                           common_objects.PATH_COLUMN: '../S1/e2.mp4',
                                           common_objects.SEASON_INDEX_COLUMN: 1,
                                           common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(1, 2),
                                           common_objects.MD5SUM_COLUMN: '00000000000000011',
                                           common_objects.DURATION_COLUMN: 1}
    vampire_season_1_episode_3_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Vampire",
                                           common_objects.MEDIA_TITLE_COLUMN: 'Episode 3',
                                           common_objects.PATH_COLUMN: '../S1/e3.mp4',
                                           common_objects.SEASON_INDEX_COLUMN: 1,
                                           common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(1, 3),
                                           common_objects.MD5SUM_COLUMN: '00000000000000111',
                                           common_objects.DURATION_COLUMN: 1}
    werewolf_season_2_episode_1_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Werewolf",
                                            common_objects.MEDIA_TITLE_COLUMN: 'Episode 1',
                                            common_objects.PATH_COLUMN: '../S2/e1.mp4',
                                            common_objects.SEASON_INDEX_COLUMN: 2,
                                            common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(2, 1),
                                            common_objects.MD5SUM_COLUMN: '00000000000001111',
                                            common_objects.DURATION_COLUMN: 1}
    werewolf_season_2_episode_2_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Werewolf",
                                            common_objects.MEDIA_TITLE_COLUMN: 'Episode 2',
                                            common_objects.PATH_COLUMN: '../S2/e2.mp4',
                                            common_objects.SEASON_INDEX_COLUMN: 2,
                                            common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(2, 2),
                                            common_objects.MD5SUM_COLUMN: '00000000000011111',
                                            common_objects.DURATION_COLUMN: 1}
    werewolf_season_2_episode_3_metadata = {common_objects.ID_COLUMN: None, common_objects.PLAYLIST_TITLE: "Werewolf",
                                            common_objects.MEDIA_TITLE_COLUMN: 'Episode 3',
                                            common_objects.PATH_COLUMN: '../S2/e3.mp4',
                                            common_objects.SEASON_INDEX_COLUMN: 2,
                                            common_objects.LIST_INDEX_COLUMN: get_playlist_list_index(2, 3),
                                            common_objects.MD5SUM_COLUMN: '00000000000111111',
                                            common_objects.DURATION_COLUMN: 1}
    media_items_default = [vampire_season_1_episode_1_metadata, vampire_season_1_episode_2_metadata,
                           vampire_season_1_episode_3_metadata, werewolf_season_2_episode_1_metadata,
                           werewolf_season_2_episode_2_metadata, werewolf_season_2_episode_3_metadata]
    media_items = media_items_default.copy()

    DB_PATH = "media_metadata.db"

    def setUp(self) -> None:
        self.media_directory_info = config_file_handler.load_json_file_content().get("media_folders")

        pytest_mocks.patch_get_file_hash(self)
        pytest_mocks.patch_get_ffmpeg_metadata(self)
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)

    def erase_db(self):
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)


class TestDBCreator(TestDBCreatorInit):

    def test_setup_media_metadata_v2(self):
        self.erase_db()
        with DBCreatorV2(DBType.PHYSICAL) as db_setter_connection:
            db_setter_connection.create_db()

            if self.media_directory_info:
                for media_path in self.media_directory_info:
                    # print(media_path)
                    db_setter_connection.setup_content_directory(media_path)

    def test_scan_media_metadata_v2(self):
        self.erase_db()
        with DBCreatorV2(DBType.PHYSICAL) as db_setter_connection:
            db_setter_connection.create_db()

            if self.media_directory_info:
                for media_path in self.media_directory_info:
                    # print(media_path)
                    db_setter_connection.setup_content_directory(media_path)

            db_setter_connection.scan_content_directories()
