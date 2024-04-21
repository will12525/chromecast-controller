import json
import shutil
import os
from unittest import TestCase

import backend_handler as bh
from database_handler.common_objects import ContentType


class TestBackEndHandler(TestCase):
    CHROMECAST_ID = "Test Cast"
    image_folder_path = "../images"

    def setUp(self):
        self.backend_handler = bh.BackEndHandler()
        self.backend_handler.start()
        if os.path.exists(self.image_folder_path):
            shutil.rmtree(self.image_folder_path)
            os.mkdir(self.image_folder_path)


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

    def test_image_download(self):
        # Add test for each content type
        json_request = {'content_type': 4, 'id': 1, 'image_url': 'http://192.168.1.201:8000/images/3.jpg',
                        'description': 'World!!'}
        bh.download_image(json_request)

    def test_image_download_media(self):
        # Add test for each content type
        json_request = {'content_type': ContentType.MEDIA.value, 'id': 1,
                        'image_url': 'http://192.168.1.201:8000/images/3.jpg',
                        'description': 'World!!'}
        bh.download_image(json_request)
        print(json.dumps(json_request, indent=4))
        assert json_request.get("image_url") == f"{json_request.get('content_type')}_{json_request.get('id')}.jpg"

    def test_image_download_season(self):
        # Add test for each content type
        json_request = {'content_type': ContentType.SEASON.value, 'id': 1,
                        'image_url': 'http://192.168.1.201:8000/images/3.jpg',
                        'description': 'World!!'}
        bh.download_image(json_request)
        assert json_request.get("image_url") == f"{json_request.get('content_type')}_{json_request.get('id')}.jpg"

    def test_image_download_tv_show(self):
        # Add test for each content type
        json_request = {'content_type': ContentType.TV_SHOW.value, 'id': 1,
                        'image_url': 'http://192.168.1.201:8000/images/3.jpg',
                        'description': 'World!!'}
        bh.download_image(json_request)
        assert json_request.get("image_url") == f"{json_request.get('content_type')}_{json_request.get('id')}.jpg"

    def test_image_download_playlist(self):
        # Add test for each content type
        json_request = {'content_type': ContentType.PLAYLIST.value, 'id': 1,
                        'image_url': 'http://192.168.1.201:8000/images/3.jpg',
                        'description': 'World!!'}
        bh.download_image(json_request)
        assert json_request.get("image_url") == f"{json_request.get('content_type')}_{json_request.get('id')}.jpg"
        json_request = {'content_type': ContentType.PLAYLIST.value, 'id': 1,
                        'image_url': 'http://192.168.1.201:8000/images/3.jpg',
                        'description': 'World!!'}

        self.assertRaises(ValueError, bh.download_image, json_request)
