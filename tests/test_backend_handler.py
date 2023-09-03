from unittest import TestCase

from backend_handler import BackEndHandler


class TestBackEndHandler(TestCase):
    test_base_media_id = 0
    backend_handler = BackEndHandler()

    def test_init(self):
        self.assertTrue(self.backend_handler.startup_sha)
        self.assertTrue(self.backend_handler.chromecast_handler)
        self.assertTrue(self.backend_handler.media_folder_metadata_handler)

    def test_get_startup_sha(self):
        backend_handler = BackEndHandler()
        self.assertTrue(backend_handler.get_startup_sha())

    def test_start(self):
        self.fail()

    def test_get_chromecast_scan_list(self):
        self.fail()

    def test_get_chromecast_connected_device_list(self):
        self.fail()

    def test_send_chromecast_cmd(self):
        self.fail()

    def test_connect_chromecast(self):
        self.fail()

    def test_disconnect_chromecast(self):
        self.fail()

    def reset_back_handler_episode(self):
        self.backend_handler.set_episode(self.test_base_media_id, self.test_base_media_id, self.test_base_media_id)

    def test_set_episode(self):
        tv_show_id = 0
        tv_show_season_id = 1
        tv_show_season_episode_id = 2

        self.assertTrue(self.backend_handler.set_episode(tv_show_id, tv_show_season_id, tv_show_season_episode_id))
        self.assertEqual(self.backend_handler.media_folder_metadata_handler.tv_show_id, tv_show_id)
        self.assertEqual(self.backend_handler.media_folder_metadata_handler.tv_show_season_id, tv_show_season_id)
        self.assertEqual(self.backend_handler.media_folder_metadata_handler.tv_show_season_episode_id,
                         tv_show_season_episode_id)

    def test_get_episode_url(self):
        self.fail()

    def test_play_episode(self):
        self.fail()

    def test_get_tv_show_name_list(self):
        self.fail()

    def test_get_tv_show_season_name_list(self):
        self.fail()

    def test_get_tv_show_season_episode_name_list(self):
        self.fail()

    def test_get_tv_show_metadata(self):
        self.fail()

    def test_get_tv_show_season_metadata(self):
        self.fail()

    def test_get_tv_show_season_episode_metadata(self):
        self.fail()
