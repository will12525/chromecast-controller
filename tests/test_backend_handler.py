from unittest import TestCase

from backend_handler import BackEndHandler
from chromecast_handler import CommandList


class TestBackEndHandler(TestCase):
    SERVER_URL_TV_SHOWS = "http://192.168.1.200:8000/tv_shows/"
    MEDIA_FOLDER_PATH = "/media/hdd1/plex_media/tv_shows/"
    MEDIA_METADATA_FILE = "tv_show_metadata.json"
    # CHROMECAST_ID = "Family Room TV"

    CHROMECAST_ID = "Master Bedroom TV"

    def setUp(self):
        self.backend_handler = BackEndHandler()


class TestBackEndFunctionCalls(TestBackEndHandler):
    test_base_media_id = 0

    def reset_backend_handler_episode(self):
        self.backend_handler.set_episode(self.test_base_media_id, self.test_base_media_id, self.test_base_media_id)

    def test_init(self):
        self.assertTrue(self.backend_handler.startup_sha)
        self.assertTrue(self.backend_handler.chromecast_handler)
        self.assertTrue(self.backend_handler.media_folder_metadata_handler)

    def test_get_startup_sha(self):
        startup_sha = self.backend_handler.get_startup_sha()
        self.assertTrue(startup_sha)
        self.assertEqual(type(startup_sha), str)

    def test_start(self):
        # Test thread startup?
        pass

    def test_get_chromecast_scan_list(self):
        chromecast_scan_list = self.backend_handler.get_chromecast_scan_list()
        self.assertEqual(type(chromecast_scan_list), list)

    def test_get_chromecast_connected_device_list(self):
        self.test_connect_chromecast()
        connected_devices_list = self.backend_handler.get_chromecast_connected_device_list()
        self.assertEqual(type(connected_devices_list), list)

    def test_send_chromecast_cmd(self):
        self.test_play_episode()
        self.backend_handler.send_chromecast_cmd(CommandList.CMD_PAUSE)
        # Need to get way to check current state
        pass

    def test_connect_chromecast(self):
        self.backend_handler.connect_chromecast(self.CHROMECAST_ID)
        connected_devices_list = self.backend_handler.get_chromecast_connected_device_list()
        self.assertTrue(self.CHROMECAST_ID in connected_devices_list)

    def test_disconnect_chromecast(self):
        self.test_connect_chromecast()
        self.backend_handler.disconnect_chromecast(self.CHROMECAST_ID)
        connected_devices_list = self.backend_handler.get_chromecast_connected_device_list()

        self.assertEqual(type(connected_devices_list), list)
        self.assertEqual(connected_devices_list, [])

    def test_set_episode(self):
        tv_show_id = 0
        tv_show_season_id = 1
        tv_show_season_episode_id = 2

        self.assertTrue(self.backend_handler.set_episode(tv_show_id, tv_show_season_id, tv_show_season_episode_id))
        self.assertEqual(self.backend_handler.media_folder_metadata_handler.tv_show_id, tv_show_id)
        self.assertEqual(self.backend_handler.media_folder_metadata_handler.tv_show_season_id, tv_show_season_id)
        self.assertEqual(self.backend_handler.media_folder_metadata_handler.tv_show_season_episode_id,
                         tv_show_season_episode_id)
        self.reset_backend_handler_episode()

    def test_get_episode_url(self):
        self.reset_backend_handler_episode()

        episode_url = self.backend_handler.get_episode_url()
        self.assertTrue(episode_url)
        self.assertEqual(type(episode_url), str)

    def test_play_episode(self):
        self.backend_handler.connect_chromecast(self.CHROMECAST_ID)
        connected_devices_list = self.backend_handler.get_chromecast_connected_device_list()
        print(connected_devices_list)
        self.assertTrue(self.CHROMECAST_ID in connected_devices_list)

        self.backend_handler.play_episode()

    def test_get_tv_show_name_list(self):
        tv_show_count = 3

        self.reset_backend_handler_episode()

        tv_show_name_list = self.backend_handler.get_tv_show_name_list()
        self.assertTrue(tv_show_name_list)
        self.assertEqual(type(tv_show_name_list), list)
        self.assertEqual(len(tv_show_name_list), tv_show_count)

    def test_get_tv_show_season_name_list(self):
        tv_show_id = 0
        tv_show_season_count = 2

        self.reset_backend_handler_episode()

        tv_show_season_name_list = self.backend_handler.get_tv_show_season_name_list(tv_show_id)
        self.assertTrue(tv_show_season_name_list)
        self.assertEqual(type(tv_show_season_name_list), list)
        self.assertEqual(len(tv_show_season_name_list), tv_show_season_count)

    def test_get_tv_show_season_episode_name_list(self):
        tv_show_id = 0
        tv_show_season_id = 1
        tv_show_season_episode_name_count = 3

        self.reset_backend_handler_episode()

        tv_show_season_episode_name_list = self.backend_handler.get_tv_show_season_episode_name_list(tv_show_id,
                                                                                                     tv_show_season_id)

        self.assertTrue(tv_show_season_episode_name_list)
        self.assertEqual(type(tv_show_season_episode_name_list), list)
        self.assertEqual(len(tv_show_season_episode_name_list), tv_show_season_episode_name_count)

    def test_get_tv_show_metadata(self):
        tv_show_id = 0
        tv_show_season_count = 2
        tv_show_season_episode_count = 5

        self.reset_backend_handler_episode()

        tv_show_metadata = self.backend_handler.get_tv_show_metadata(tv_show_id)

        self.assertEqual(type(tv_show_metadata), dict)
        self.assertEqual(tv_show_metadata.get("season_count"), tv_show_season_count)
        self.assertEqual(tv_show_metadata.get("episode_count"), tv_show_season_episode_count)

    def test_get_tv_show_season_metadata(self):
        tv_show_id = 0
        tv_show_season_id = 1
        tv_show_season_episode_count = 3

        self.reset_backend_handler_episode()

        tv_show_season_metadata = self.backend_handler.get_tv_show_season_metadata(tv_show_id, tv_show_season_id)

        self.assertEqual(type(tv_show_season_metadata), dict)
        self.assertEqual(tv_show_season_metadata.get("episode_count"), tv_show_season_episode_count)
        self.assertTrue(tv_show_season_metadata.get("episodes"))
        self.assertEqual(len(tv_show_season_metadata.get("episodes")), tv_show_season_episode_count)

    def test_get_tv_show_season_episode_metadata(self):
        tv_show_id = 0
        tv_show_season_id = 1
        tv_show_season_episode_id = 1

        self.reset_backend_handler_episode()

        tv_show_season_episode_metadata = self.backend_handler.get_tv_show_season_episode_metadata(tv_show_id,
                                                                                                   tv_show_season_id,
                                                                                                   tv_show_season_episode_id)

        self.assertEqual(type(tv_show_season_episode_metadata), dict)
        self.assertTrue(tv_show_season_episode_metadata.get("id"))
        self.assertEqual(type(tv_show_season_episode_metadata.get("id")), int)
        self.assertEqual(type(tv_show_season_episode_metadata.get("name")), str)
        self.assertEqual(type(tv_show_season_episode_metadata.get("path")), str)
