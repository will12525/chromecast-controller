from unittest import TestCase
import os
import media_folder_metadata_handler

media_folder_sample_path = "../media_folder_sample/"


class TestMediaMetadata(TestCase):

    def test_generate_tv_show_list(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        self.assertEqual(type(media_folder_metadata), dict)

    def test_save_metadata_to_file(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        media_folder_metadata_handler.save_metadata_to_file(media_folder_metadata)
        self.assertTrue(os.path.exists(media_folder_metadata_handler.MEDIA_METADATA_FILE))

    def test_get_tv_show_metadata(self):
        tv_show_id = 0
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        fn_tv_show_metadata = media_folder_metadata_handler.get_tv_show_metadata(media_folder_metadata, tv_show_id)
        dr_tv_show_metadata = media_folder_metadata.get("tv_shows")[tv_show_id]
        self.assertEqual(fn_tv_show_metadata, dr_tv_show_metadata)

    def test_get_tv_show_metadata_out_of_bounds(self):
        tv_show_id = 3
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        tv_show_metadata = media_folder_metadata_handler.get_tv_show_metadata(media_folder_metadata, tv_show_id)
        self.assertEqual(tv_show_metadata, None)

    def test_get_tv_show_season_metadata(self):
        tv_show_id = 2
        tv_show_season_id = 2
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        fn_tv_show_season_metadata = media_folder_metadata_handler.get_tv_show_season_metadata(media_folder_metadata,
                                                                                               tv_show_id,
                                                                                               tv_show_season_id)
        dr_tv_show_season_metadata = media_folder_metadata.get("tv_shows")[tv_show_id].get("seasons")[tv_show_season_id]
        self.assertEqual(fn_tv_show_season_metadata, dr_tv_show_season_metadata)

    def test_get_tv_show_season_metadata_out_of_bounds(self):
        tv_show_id = 2
        tv_show_season_id = 3
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        tv_show_season_metadata = media_folder_metadata_handler.get_tv_show_season_metadata(media_folder_metadata,
                                                                                            tv_show_id,
                                                                                            tv_show_season_id)
        self.assertEqual(tv_show_season_metadata, None)

    def test_get_tv_show_season_episode_metadata(self):
        tv_show_id = 2
        tv_show_season_id = 2
        tv_show_season_episode_id = 0
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
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
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        tv_show_season_episode_metadata = media_folder_metadata_handler.get_tv_show_season_episode_metadata(
            media_folder_metadata,
            tv_show_id,
            tv_show_season_id,
            tv_show_season_episode_id)
        self.assertEqual(tv_show_season_episode_metadata, None)

    def test_load_metadata_from_file(self):
        media_folder_metadata = media_folder_metadata_handler.load_metadata_from_file()
        self.assertEqual(type(media_folder_metadata), dict)

    def test_get_tv_show_name_list(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        tv_show_name_list = media_folder_metadata_handler.get_tv_show_name_list(media_folder_metadata)
        self.assertEqual(len(tv_show_name_list), 3)

    def test_get_tv_show_season_name_list(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        tv_show_season_name_list = media_folder_metadata_handler.get_tv_show_season_name_list(media_folder_metadata, 0)
        self.assertEqual(len(tv_show_season_name_list), 2)

    def test_get_tv_show_season_episode_name_list(self):
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        tv_show_season_episode_name_list = media_folder_metadata_handler.get_tv_show_season_episode_name_list(
            media_folder_metadata, 0, 0)
        self.assertEqual(len(tv_show_season_episode_name_list), 2)


class TestEpisodeInfo(TestCase):
    test_base_tv_show_id = 0
    test_base_tv_show_season_id = 0
    test_base_tv_show_season_episode_id = 0
    current_episode = media_folder_metadata_handler.EpisodeInfo(test_base_tv_show_id, test_base_tv_show_season_id,
                                                                test_base_tv_show_season_episode_id)

    def reset(self):
        self.current_episode = media_folder_metadata_handler.EpisodeInfo(self.test_base_tv_show_id,
                                                                         self.test_base_tv_show_season_id,
                                                                         self.test_base_tv_show_season_episode_id)

    def test_init(self):
        self.assertNotEqual(self.current_episode.media_metadata, None)

    def test_is_valid(self):
        self.assertTrue(self.current_episode.is_valid())

    def test_is_not_valid(self):
        self.current_episode.tv_show_id = 4
        self.assertFalse(self.current_episode.is_valid())
        self.current_episode.tv_show_id = self.test_base_tv_show_id

    def test_get_url(self):
        current_episode_url = self.current_episode.get_url()
        self.assertTrue(current_episode_url)
        self.assertEqual(type(current_episode_url), str)
        self.assertTrue(self.current_episode.SERVER_URL_TV_SHOWS in current_episode_url)
        self.assertTrue(".mp4" in current_episode_url)
        self.assertFalse(self.current_episode.MEDIA_FOLDER_PATH in current_episode_url)

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
