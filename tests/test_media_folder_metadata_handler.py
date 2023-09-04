import os
from unittest import TestCase

import media_folder_metadata_handler
from media_folder_metadata_handler import MediaID

MEDIA_FOLDER_SAMPLE_PATH = "../media_folder_sample/"
MEDIA_METADATA_FILE = "tv_show_metadata.json"


class TestMediaFolderMetadataHandler(TestCase):
    SERVER_URL_TV_SHOWS = "http://192.168.1.200:8000/tv_shows/"
    media_folder_metadata_handler = None
    test_base_tv_show_id = 0
    test_base_tv_show_season_id = 0
    test_base_tv_show_season_episode_id = 0

    def setUp(self):
        media_id = MediaID(0, 0, 0)
        self.media_folder_metadata_handler = media_folder_metadata_handler.MediaFolderMetadataHandler(
            MEDIA_METADATA_FILE, MEDIA_FOLDER_SAMPLE_PATH)
        self.assertTrue(self.media_folder_metadata_handler.set_media_id(media_id))


class TestMediaMetadata(TestMediaFolderMetadataHandler):

    def test_generate_tv_show_list(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        self.assertEqual(type(media_folder_metadata), dict)
        self.assertTrue(media_folder_metadata.get("path"))

    def test_save_metadata_to_file(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        media_folder_metadata_handler.save_metadata_to_file(MEDIA_METADATA_FILE, media_folder_metadata)
        self.assertTrue(os.path.exists(MEDIA_METADATA_FILE))

    def test_get_tv_show_metadata(self):
        tv_show_id = 0
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        fn_tv_show_metadata = media_folder_metadata_handler.get_tv_show_metadata(media_folder_metadata, tv_show_id)
        dr_tv_show_metadata = media_folder_metadata.get("tv_shows")[tv_show_id]
        self.assertEqual(fn_tv_show_metadata, dr_tv_show_metadata)

    def test_get_tv_show_metadata_out_of_bounds(self):
        tv_show_id = 3
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        tv_show_metadata = media_folder_metadata_handler.get_tv_show_metadata(media_folder_metadata, tv_show_id)
        self.assertEqual(tv_show_metadata, None)

    def test_get_tv_show_season_metadata(self):
        tv_show_id = 2
        tv_show_season_id = 2
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        fn_tv_show_season_metadata = media_folder_metadata_handler.get_tv_show_season_metadata(media_folder_metadata,
                                                                                               tv_show_id,
                                                                                               tv_show_season_id)
        dr_tv_show_season_metadata = media_folder_metadata.get("tv_shows")[tv_show_id].get("seasons")[tv_show_season_id]
        self.assertEqual(fn_tv_show_season_metadata, dr_tv_show_season_metadata)

    def test_get_tv_show_season_metadata_out_of_bounds(self):
        tv_show_id = 2
        tv_show_season_id = 3
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        tv_show_season_metadata = media_folder_metadata_handler.get_tv_show_season_metadata(media_folder_metadata,
                                                                                            tv_show_id,
                                                                                            tv_show_season_id)
        self.assertEqual(tv_show_season_metadata, None)

    def test_get_tv_show_season_episode_metadata(self):
        tv_show_id = 2
        tv_show_season_id = 2
        tv_show_season_episode_id = 0
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        fn_tv_show_season_episode_metadata = media_folder_metadata_handler.get_tv_show_season_episode_metadata(
            media_folder_metadata,
            tv_show_id,
            tv_show_season_id,
            tv_show_season_episode_id)
        dr_tv_show_season_metadata = media_folder_metadata.get("tv_shows")[tv_show_id].get("seasons")[tv_show_season_id]
        dr_tv_show_season_episode_metadata = dr_tv_show_season_metadata.get("episodes")[tv_show_season_episode_id]
        self.assertEqual(fn_tv_show_season_episode_metadata, dr_tv_show_season_episode_metadata)

    def test_get_tv_show_season_episode_metadata_out_of_bounds(self):
        tv_show_id = 2
        tv_show_season_id = 2
        tv_show_season_episode_id = 1
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        tv_show_season_episode_metadata = media_folder_metadata_handler.get_tv_show_season_episode_metadata(
            media_folder_metadata,
            tv_show_id,
            tv_show_season_id,
            tv_show_season_episode_id)
        self.assertEqual(tv_show_season_episode_metadata, None)

    def test_get_media_metadata(self):
        media_folder_metadata = media_folder_metadata_handler.get_media_metadata(
            MEDIA_METADATA_FILE, MEDIA_FOLDER_SAMPLE_PATH)
        self.assertTrue(media_folder_metadata)
        self.assertEqual(type(media_folder_metadata), dict)

    def test_generate_media_metadata(self):
        media_folder_metadata = media_folder_metadata_handler.generate_media_metadata(
            MEDIA_METADATA_FILE, MEDIA_FOLDER_SAMPLE_PATH)
        self.assertTrue(media_folder_metadata)
        self.assertEqual(type(media_folder_metadata), dict)
        self.assertEqual(media_folder_metadata.get("version"), media_folder_metadata_handler.MEDIA_METADATA_VERSION)

    def test_load_metadata_from_file(self):
        media_folder_metadata = media_folder_metadata_handler.load_media_metadata_from_file(MEDIA_METADATA_FILE)
        self.assertEqual(type(media_folder_metadata), dict)

    def test_get_tv_show_name_list(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        tv_show_name_list = media_folder_metadata_handler.get_tv_show_name_list(media_folder_metadata)
        self.assertEqual(len(tv_show_name_list), 3)

    def test_get_tv_show_season_name_list(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        tv_show_season_name_list = media_folder_metadata_handler.get_tv_show_season_name_list(media_folder_metadata, 0)
        self.assertEqual(len(tv_show_season_name_list), 2)

    def test_get_tv_show_season_episode_name_list(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(MEDIA_FOLDER_SAMPLE_PATH)
        tv_show_season_episode_name_list = media_folder_metadata_handler.get_tv_show_season_episode_name_list(
            media_folder_metadata, 0, 0)
        self.assertEqual(len(tv_show_season_episode_name_list), 2)


class MediaFolderMetadataHandler(TestMediaFolderMetadataHandler):

    def test_init(self):
        self.assertNotEqual(self.media_folder_metadata_handler.media_metadata, None)

    def test_is_valid(self):
        self.assertNotEqual(self.media_folder_metadata_handler.get_episode_info(), None)

    def test_is_not_valid(self):
        self.media_folder_metadata_handler.media_id.tv_show_id = 4
        self.assertEqual(self.media_folder_metadata_handler.get_episode_info(), None)
        self.media_folder_metadata_handler.media_id.tv_show_id = self.test_base_tv_show_id

    def test_get_url(self):
        current_episode_url = self.media_folder_metadata_handler.get_url(self.SERVER_URL_TV_SHOWS)
        self.assertTrue(current_episode_url)
        self.assertEqual(type(current_episode_url), str)
        self.assertTrue(self.SERVER_URL_TV_SHOWS in current_episode_url)
        self.assertTrue(".mp4" in current_episode_url)
        self.assertFalse(MEDIA_FOLDER_SAMPLE_PATH in current_episode_url)

    def test_increment_episode(self):
        self.media_folder_metadata_handler.increment_next_episode()

        self.assertEqual(self.media_folder_metadata_handler.media_id.tv_show_season_episode_id,
                         self.test_base_tv_show_season_episode_id + 1)
        self.assertEqual(self.media_folder_metadata_handler.media_id.tv_show_season_id,
                         self.test_base_tv_show_season_id)
        self.assertEqual(self.media_folder_metadata_handler.media_id.tv_show_id, self.test_base_tv_show_id)

    def test_increment_season(self):
        self.media_folder_metadata_handler.media_id.tv_show_season_episode_id = 10

        self.media_folder_metadata_handler.increment_next_episode()

        self.assertEqual(self.media_folder_metadata_handler.media_id.tv_show_season_episode_id, 0)
        self.assertEqual(self.media_folder_metadata_handler.media_id.tv_show_season_id,
                         self.test_base_tv_show_season_id + 1)
        self.assertEqual(self.media_folder_metadata_handler.media_id.tv_show_id, self.test_base_tv_show_id)

    def test_reset_to_base_episode(self):
        self.media_folder_metadata_handler.media_id.tv_show_season_episode_id = 10
        self.media_folder_metadata_handler.media_id.tv_show_season_id = 10

        self.media_folder_metadata_handler.increment_next_episode()

        self.assertEqual(self.media_folder_metadata_handler.media_id.tv_show_season_episode_id, 0)
        self.assertEqual(self.media_folder_metadata_handler.media_id.tv_show_season_id, 0)
        self.assertEqual(self.media_folder_metadata_handler.media_id.tv_show_id, self.test_base_tv_show_id)

    def test_get_tv_show_name_list(self):
        tv_show_name_list = self.media_folder_metadata_handler.get_tv_show_name_list()
        self.assertEqual(len(tv_show_name_list), 3)

    def test_get_tv_show_season_name_list(self):
        media_id = MediaID(0, 0, 0)
        self.media_folder_metadata_handler.set_media_id(media_id)
        tv_show_season_name_list = self.media_folder_metadata_handler.get_tv_show_season_name_list()
        self.assertEqual(len(tv_show_season_name_list), 2)

    def test_get_tv_show_season_episode_name_list(self):
        media_id = MediaID(1, 0, 0)
        self.media_folder_metadata_handler.set_media_id(media_id)
        tv_show_season_episode_name_list = self.media_folder_metadata_handler.get_tv_show_season_episode_name_list()
        self.assertEqual(len(tv_show_season_episode_name_list), 2)


class MediaFolderMetadataHandlerUpdate(TestMediaFolderMetadataHandler):

    def test_update_tv_show(self):
        media_id = MediaID(0, 0, 0)
        new_tv_show_id = 1
        changed_type = self.media_folder_metadata_handler.update_tv_show(new_tv_show_id, media_id)
        self.assertEqual(changed_type, media_folder_metadata_handler.PathType.TV_SHOW)

    def test_update_tv_show_no_change(self):
        media_id = MediaID(0, 0, 0)
        changed_type = self.media_folder_metadata_handler.update_tv_show(media_id.tv_show_id, media_id)
        self.assertFalse(changed_type)

    def test_update_tv_show_season(self):
        media_id = MediaID(0, 0, 0)
        new_tv_show_season_id = 1
        changed_type = self.media_folder_metadata_handler.update_tv_show_season(new_tv_show_season_id, media_id)
        self.assertEqual(changed_type, media_folder_metadata_handler.PathType.TV_SHOW_SEASON)

    def test_update_tv_show_season_no_change(self):
        media_id = MediaID(0, 0, 0)
        changed_type = self.media_folder_metadata_handler.update_tv_show_season(media_id.tv_show_season_id, media_id)
        self.assertFalse(changed_type)

    def test_update_tv_show_season_episode(self):
        media_id = MediaID(0, 0, 0)
        new_tv_show_season_episode_id = 1
        changed_type = self.media_folder_metadata_handler.update_tv_show_season_episode(new_tv_show_season_episode_id,
                                                                                        media_id)
        self.assertEqual(changed_type, media_folder_metadata_handler.PathType.TV_SHOW_SEASON_EPISODE)

    def test_update_tv_show_season_episode_no_change(self):
        media_id = MediaID(0, 0, 0)
        changed_type = self.media_folder_metadata_handler.update_tv_show_season_episode(
            media_id.tv_show_season_episode_id, media_id)
        self.assertFalse(changed_type)

    def test_update_media_id_selection_tv_show(self):
        new_media_id = MediaID(1, 0, 0)
        change_type = self.media_folder_metadata_handler.update_media_id_selection(new_media_id)
        self.assertEqual(change_type, media_folder_metadata_handler.PathType.TV_SHOW)

    def test_update_media_id_selection_tv_show_season(self):
        new_media_id = MediaID(0, 1, 0)
        change_type = self.media_folder_metadata_handler.update_media_id_selection(new_media_id)
        self.assertEqual(change_type, media_folder_metadata_handler.PathType.TV_SHOW_SEASON)

    def test_update_media_id_selection_tv_show_season_episode(self):
        new_media_id = MediaID(0, 0, 1)
        change_type = self.media_folder_metadata_handler.update_media_id_selection(new_media_id)
        self.assertEqual(change_type, media_folder_metadata_handler.PathType.TV_SHOW_SEASON_EPISODE)
