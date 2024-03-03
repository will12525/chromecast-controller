import pathlib
from unittest import TestCase

from backend_handler import BackEndHandler


class TestBackEndHandler(TestCase):
    CHROMECAST_ID = "Test Cast"

    def setUp(self):
        self.backend_handler = BackEndHandler()


class TestBackEndFunctionCalls(TestBackEndHandler):
    def test_init(self):
        self.assertTrue(self.backend_handler.startup_sha)
        self.assertTrue(self.backend_handler.chromecast_handler)
        # self.assertTrue(self.backend_handler.media_folder_metadata_handler)

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

    # def test_get_chromecast_connected_device_list(self):
    #     self.test_connect_chromecast()
    #     connected_devices_list = self.backend_handler.get_chromecast_connected_device_list()
    #     self.assertEqual(type(connected_devices_list), list)

    def test_send_chromecast_cmd(self):
        # self.test_play_episode()
        # self.backend_handler.send_chromecast_cmd(CommandList.CMD_PAUSE)
        # Need to get way to check current state
        pass

    def test_connect_chromecast(self):
        self.backend_handler.connect_chromecast(self.CHROMECAST_ID)
        self.assertEqual(self.CHROMECAST_ID, self.backend_handler.get_chromecast_device_id())

    def test_disconnect_chromecast(self):
        self.test_connect_chromecast()
        self.backend_handler.disconnect_chromecast()
        connected_device_id = self.backend_handler.get_chromecast_device_id()

        self.assertFalse(connected_device_id)

    # def test_set_episode(self):
    #     media_id = MediaID(0, 1, 2)
    #
    #     self.assertTrue(self.backend_handler.set_media_id(media_id))
    #     self.assertEqual(self.backend_handler.media_folder_metadata_handler.media_id.tv_show_id, media_id.tv_show_id)
    #     self.assertEqual(self.backend_handler.media_folder_metadata_handler.media_id.tv_show_season_id,
    #                      media_id.tv_show_season_id)
    #     self.assertEqual(self.backend_handler.media_folder_metadata_handler.media_id.tv_show_season_episode_id,
    #                      media_id.tv_show_season_episode_id)

    # def test_get_episode_url(self):
    #     episode_url = self.backend_handler.get_episode_url()
    #     self.assertTrue(episode_url)
    #     self.assertEqual(type(episode_url), str)

    # def test_play_media(self):
    #     self.test_connect_chromecast()
    #     # self.backend_handler.connect_chromecast(self.CHROMECAST_ID)
    #     # connected_devices_list = self.backend_handler.get_chromecast_connected_device_list()
    #     # print(connected_devices_list)
    #     # self.assertTrue(self.CHROMECAST_ID in connected_devices_list)
    #
    #     self.backend_handler.play_media()

    # def test_get_tv_show_name_list(self):
    #     tv_show_count = 3
    #
    #     tv_show_name_list = self.backend_handler.get_tv_show_name_list()
    #     self.assertTrue(tv_show_name_list)
    #     self.assertEqual(type(tv_show_name_list), list)
    #     self.assertEqual(len(tv_show_name_list), tv_show_count)

    # def test_get_tv_show_season_name_list(self):
    #     tv_show_season_count = 2
    #
    #     tv_show_season_name_list = self.backend_handler.get_tv_show_season_name_list()
    #     self.assertTrue(tv_show_season_name_list)
    #     self.assertEqual(type(tv_show_season_name_list), list)
    #     self.assertEqual(len(tv_show_season_name_list), tv_show_season_count)

    # def test_get_tv_show_season_episode_name_list(self):
    #     media_id = MediaID(0, 1, 0)
    #     tv_show_season_episode_name_count = 3
    #
    #     self.backend_handler.set_media_id(media_id)
    #
    #     tv_show_season_episode_name_list = self.backend_handler.get_tv_show_season_episode_name_list()
    #
    #     self.assertTrue(tv_show_season_episode_name_list)
    #     self.assertEqual(type(tv_show_season_episode_name_list), list)
    #     self.assertEqual(len(tv_show_season_episode_name_list), tv_show_season_episode_name_count)

    # def test_get_tv_show_metadata(self):
    #     media_id = MediaID(0, 0, 0)
    #
    #     self.backend_handler.set_media_id(media_id)
    #
    #     tv_show_metadata = self.backend_handler.get_tv_show_metadata(media_id)
    #     self.assertTrue(tv_show_metadata)


class TestEditor(TestBackEndHandler):
    OUTPUT_PATH = "../media_folder_modify/output"

    def test_editor_process_txt_file_error_invalid_file(self):
        editor_metadata = {
            'txt_file_name': "2024hi-01-31_16-32-36"
        }
        error_code = self.backend_handler.editor_process_txt_file(editor_metadata, self.OUTPUT_PATH)
        print(f"ERROR: {error_code}")
        assert error_code == 1

    def test_editor_process_txt_file_error_missing_mp4(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_no_mp4"
        }
        error_code = self.backend_handler.editor_process_txt_file(editor_metadata, self.OUTPUT_PATH)
        print(f"ERROR: {error_code}")
        assert error_code == 2

    def test_editor_process_txt_file_error_empty_file(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_empty"
        }
        error_code = self.backend_handler.editor_process_txt_file(editor_metadata, self.OUTPUT_PATH)
        print(f"ERROR: {error_code}")
        assert error_code == 3

    def test_editor_process_txt_file_error_invalid_file_content(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_invalid"
        }
        error_code = self.backend_handler.editor_process_txt_file(editor_metadata, self.OUTPUT_PATH)
        print(f"ERROR: {error_code}")
        assert error_code == 4

    def test_editor_process_txt_file(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36"
        }
        error_code = self.backend_handler.editor_process_txt_file(editor_metadata,
                                                                  pathlib.Path(self.OUTPUT_PATH).resolve())
        print(f"ERROR: {error_code}")

    def test_editor_cmd_list(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36"
        }
        error_code = self.backend_handler.editor_process_txt_file(editor_metadata,
                                                                  pathlib.Path(self.OUTPUT_PATH).resolve())
        print(f"ERROR: {error_code}")
