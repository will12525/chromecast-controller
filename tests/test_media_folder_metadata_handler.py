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
        fn_tv_show_season_episode_metadata = media_folder_metadata_handler.get_tv_show_season_episode_metadata(media_folder_metadata,
                                                                                               tv_show_id,
                                                                                               tv_show_season_id,
                                                                                                               tv_show_season_episode_id)
        dr_tv_show_season_episode_metadata = media_folder_metadata.get("tv_shows")[tv_show_id].get("seasons")[tv_show_season_id].get("episodes")[tv_show_season_episode_id]
        self.assertEqual(fn_tv_show_season_episode_metadata, dr_tv_show_season_episode_metadata)

    def test_get_tv_show_season_episode_metadata_out_of_bounds(self):
        tv_show_id = 2
        tv_show_season_id = 2
        tv_show_season_episode_id = 1
        media_folder_metadata = media_folder_metadata_handler.generate_tv_show_list(media_folder_sample_path)
        tv_show_season_episode_metadata =  media_folder_metadata_handler.get_tv_show_season_episode_metadata(media_folder_metadata,
                                                                                               tv_show_id,
                                                                                               tv_show_season_id,
                                                                                                               tv_show_season_episode_id)
        self.assertEqual(tv_show_season_episode_metadata, None)


    def test_load_metadata_from_file(self):
        media_folder_metadata = media_folder_metadata_handler.load_metadata_from_file()
        self.assertEqual(type(media_folder_metadata), dict)

