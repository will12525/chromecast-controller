import os
from unittest import TestCase

import media_folder_metadata_handler

MEDIA_FOLDER_SAMPLE_PATH = "../media_folder_sample/"
MEDIA_METADATA_FILE = "tv_show_metadata.json"


class TestMediaMetadata(TestCase):

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


class MediaFolderMetadataHandler(TestCase):
    SERVER_URL_TV_SHOWS = "http://192.168.1.200:8000/tv_shows/"
    test_base_tv_show_id = 0
    test_base_tv_show_season_id = 0
    test_base_tv_show_season_episode_id = 0
    current_episode = media_folder_metadata_handler.MediaFolderMetadataHandler(MEDIA_METADATA_FILE,
                                                                               MEDIA_FOLDER_SAMPLE_PATH)

    def reset(self):
        self.current_episode = media_folder_metadata_handler.MediaFolderMetadataHandler(MEDIA_METADATA_FILE,
                                                                                        MEDIA_FOLDER_SAMPLE_PATH)

    def test_init(self):
        self.assertNotEqual(self.current_episode.media_metadata, None)

    def test_is_valid(self):
        self.assertNotEqual(self.current_episode.get_episode_info(), None)

    def test_is_not_valid(self):
        self.current_episode.tv_show_id = 4
        self.assertEqual(self.current_episode.get_episode_info(), None)
        self.current_episode.tv_show_id = self.test_base_tv_show_id

    def test_get_url(self):
        current_episode_url = self.current_episode.get_url(self.SERVER_URL_TV_SHOWS)
        self.assertTrue(current_episode_url)
        self.assertEqual(type(current_episode_url), str)
        self.assertTrue(self.SERVER_URL_TV_SHOWS in current_episode_url)
        self.assertTrue(".mp4" in current_episode_url)
        self.assertFalse(MEDIA_FOLDER_SAMPLE_PATH in current_episode_url)

    def test_increment_episode(self):
        self.reset()

        self.current_episode.increment_next_episode()

        self.assertEqual(self.current_episode.tv_show_season_episode_id, self.test_base_tv_show_season_episode_id + 1)
        self.assertEqual(self.current_episode.tv_show_season_id, self.test_base_tv_show_season_id)
        self.assertEqual(self.current_episode.tv_show_id, self.test_base_tv_show_id)

    def test_increment_season(self):
        self.reset()
        self.current_episode.tv_show_season_episode_id = 10

        self.current_episode.increment_next_episode()

        self.assertEqual(self.current_episode.tv_show_season_episode_id, 0)
        self.assertEqual(self.current_episode.tv_show_season_id, self.test_base_tv_show_season_id + 1)
        self.assertEqual(self.current_episode.tv_show_id, self.test_base_tv_show_id)

    def test_reset_to_base_episode(self):
        self.reset()
        self.current_episode.tv_show_season_episode_id = 10
        self.current_episode.tv_show_season_id = 10

        self.current_episode.increment_next_episode()

        self.assertEqual(self.current_episode.tv_show_season_episode_id, 0)
        self.assertEqual(self.current_episode.tv_show_season_id, 0)
        self.assertEqual(self.current_episode.tv_show_id, self.test_base_tv_show_id)


class TestEpisodeInfo(TestCase):
    SERVER_URL_TV_SHOWS = "http://192.168.1.200:8000/tv_shows/"
    test_base_tv_show_id = 0
    test_base_tv_show_season_id = 0
    test_base_tv_show_season_episode_id = 0
    current_episode = media_folder_metadata_handler.EpisodeInfo(
        MEDIA_METADATA_FILE, MEDIA_FOLDER_SAMPLE_PATH, test_base_tv_show_id, test_base_tv_show_season_id,
        test_base_tv_show_season_episode_id)

    def reset(self):
        self.current_episode = media_folder_metadata_handler.EpisodeInfo(MEDIA_METADATA_FILE,
                                                                         MEDIA_FOLDER_SAMPLE_PATH,
                                                                         self.test_base_tv_show_id,
                                                                         self.test_base_tv_show_season_id,
                                                                         self.test_base_tv_show_season_episode_id)

    def test_init(self):
        self.assertNotEqual(self.current_episode.media_metadata, None)

    def test_is_valid(self):
        self.assertNotEqual(self.current_episode.get_episode_info(), None)

    def test_is_not_valid(self):
        self.current_episode.tv_show_id = 4
        self.assertEqual(self.current_episode.get_episode_info(), None)
        self.current_episode.tv_show_id = self.test_base_tv_show_id

    def test_get_url(self):
        current_episode_url = self.current_episode.get_url(self.SERVER_URL_TV_SHOWS)
        self.assertTrue(current_episode_url)
        self.assertEqual(type(current_episode_url), str)
        self.assertTrue(self.SERVER_URL_TV_SHOWS in current_episode_url)
        self.assertTrue(".mp4" in current_episode_url)
        self.assertFalse(MEDIA_FOLDER_SAMPLE_PATH in current_episode_url)

    def test_increment_episode(self):
        self.reset()

        self.current_episode.increment_next_episode()

        self.assertEqual(self.current_episode.tv_show_season_episode_id, self.test_base_tv_show_season_episode_id + 1)
        self.assertEqual(self.current_episode.tv_show_season_id, self.test_base_tv_show_season_id)
        self.assertEqual(self.current_episode.tv_show_id, self.test_base_tv_show_id)

    def test_increment_season(self):
        self.reset()
        self.current_episode.tv_show_season_episode_id = 10

        self.current_episode.increment_next_episode()

        self.assertEqual(self.current_episode.tv_show_season_episode_id, 0)
        self.assertEqual(self.current_episode.tv_show_season_id, self.test_base_tv_show_season_id + 1)
        self.assertEqual(self.current_episode.tv_show_id, self.test_base_tv_show_id)

    def test_reset_to_base_episode(self):
        self.reset()
        self.current_episode.tv_show_season_episode_id = 10
        self.current_episode.tv_show_season_id = 10

        self.current_episode.increment_next_episode()

        self.assertEqual(self.current_episode.tv_show_season_episode_id, 0)
        self.assertEqual(self.current_episode.tv_show_season_id, 0)
        self.assertEqual(self.current_episode.tv_show_id, self.test_base_tv_show_id)
