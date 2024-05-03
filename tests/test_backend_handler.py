import json
import shutil
import os
import time
from unittest import TestCase
import pathlib

import backend_handler as bh
import config_file_handler
from database_handler import common_objects
from database_handler.common_objects import ContentType
from database_handler.database_handler import DatabaseHandler
from database_handler.create_database import DBCreator
import __init__


class TestBackEndHandler(TestCase):
    CHROMECAST_ID = "Test Cast"
    image_folder_path = "../images"

    def setUp(self):
        __init__.patch_extract_subclip(self)
        __init__.patch_get_file_hash(self)
        __init__.patch_get_ffmpeg_metadata(self)
        self.backend_handler = bh.BackEndHandler()
        setup_thread = self.backend_handler.start()
        while setup_thread.is_alive():
            time.sleep(.01)
        if os.path.exists(self.image_folder_path):
            shutil.rmtree(self.image_folder_path)
            os.mkdir(self.image_folder_path)


class TestSetupDB(TestCase):
    DB_PATH = "media_metadata.db"

    def setUp(self):
        __init__.patch_get_file_hash(self)
        __init__.patch_get_ffmpeg_metadata(self)
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)

    def test_setup_db(self):
        assert not os.path.exists(self.DB_PATH)
        bh.setup_db()
        assert os.path.exists(self.DB_PATH)

    def test_setup_db_contents(self):
        media_folders = config_file_handler.load_js_file().get("media_folders")
        assert not os.path.exists(self.DB_PATH)
        bh.setup_db()
        with DBCreator() as db_connection:
            media_metadata = db_connection.get_all_media_directory_info()

        assert len(media_folders) == len(media_metadata)
        assert type(media_folders) is list
        assert type(media_metadata) is list

        for i in range(len(media_folders)):
            assert type(media_folders[i]) is dict
            assert type(media_metadata[i]) is dict
            assert media_folders[i].get(common_objects.MEDIA_TYPE_COLUMN) == media_metadata[i].get(
                common_objects.MEDIA_TYPE_COLUMN)
            assert media_folders[i].get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN) == media_metadata[i].get(
                common_objects.MEDIA_DIRECTORY_PATH_COLUMN)
            assert media_folders[i].get(common_objects.MEDIA_DIRECTORY_URL_COLUMN) == media_metadata[i].get(
                common_objects.MEDIA_DIRECTORY_URL_COLUMN)


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

    def test_build_tv_show_output_path(self):
        expected_str = "\Test file name\Test file name - s1e5.mp4"
        show_title = "Test file name"
        file_name_str = f"{show_title} - s1e5.mp4"
        output_path = bh.build_tv_show_output_path(file_name_str)
        assert expected_str in str(output_path)
        assert str(output_path).count(show_title) == 2
        assert file_name_str in str(output_path)
        assert str(output_path).count(file_name_str) == 1

    def test_editor_validate_txt_file(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36.txt",
            'media_type': ContentType.TV.value
        }
        raw_folder = config_file_handler.load_js_file().get('editor_raw_folder')
        error_log = bh.editor_validate_txt_file(raw_folder, editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert not error_log

    def test_editor_validate_broken_txt_file(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_invalid.txt",
            'media_type': ContentType.TV.value
        }
        raw_folder = config_file_handler.load_js_file().get('editor_raw_folder')
        error_log = bh.editor_validate_txt_file(raw_folder, editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert error_log
        assert len(error_log) == 5

    def test_editor_validate_movie_txt_file(self):
        editor_metadata = {
            'txt_file_name': "movie.txt",
            "media_type": ContentType.MOVIE.value
        }
        raw_folder = config_file_handler.load_js_file().get('editor_raw_folder')
        error_log = bh.editor_validate_txt_file(raw_folder, editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert not error_log

    def test_editor_process_movie_txt_file(self):
        __init__.patch_extract_subclip(self)
        json_request = {
            'txt_file_name': "movie.txt",
            "media_type": ContentType.MOVIE.value
        }
        raw_folder = config_file_handler.load_js_file().get('editor_raw_folder')
        with DatabaseHandler() as db_connection:
            media_metadata = db_connection.get_media_folder_path_from_type(json_request.get("media_type"))
        output_path = pathlib.Path(media_metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN)).resolve()
        errors = self.backend_handler.editor_process_txt_file(raw_folder, json_request, output_path)
        print(json.dumps(errors, indent=4))
        assert not errors

    def test_editor_process_tv_txt_file(self):
        __init__.patch_extract_subclip(self)

        json_request = {
            'txt_file_name': "2024-01-31_16-32-36.txt",
            "media_type": ContentType.TV.value
        }
        raw_folder = config_file_handler.load_js_file().get('editor_raw_folder')
        with DatabaseHandler() as db_connection:
            media_metadata = db_connection.get_media_folder_path_from_type(json_request.get("media_type"))
        output_path = pathlib.Path(media_metadata.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN)).resolve()
        errors = self.backend_handler.editor_process_txt_file(raw_folder, json_request, output_path)
        print(json.dumps(errors, indent=4))
        assert not errors

    def test_get_system_data(self):
        system_data = self.backend_handler.get_system_data()
        print(json.dumps(system_data, indent=4))
