import json
import shutil
import os
import time
from unittest import TestCase, mock
import pathlib

import backend_handler
import backend_handler as bh
import config_file_handler
from database_handler.common_objects import ContentType
from database_handler.db_setter import DBCreatorV2
from . import pytest_mocks


class TestBackEndHandler(TestCase):
    CHROMECAST_ID = "Bedroom"
    image_folder_path = "../images"

    def setUp(self):
        pytest_mocks.patch_update_processed_file(self)
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_get_file_hash(self)
        pytest_mocks.patch_get_ffmpeg_metadata(self)
        # pytest_mocks.patch_get_free_disk_space(self)

        self.backend_handler = bh.BackEndHandler()
        setup_thread = self.backend_handler.start()
        # setup_thread.join()
        while setup_thread.is_alive():
            time.sleep(.01)
        setup_thread.join()
        if os.path.exists(self.image_folder_path):
            shutil.rmtree(self.image_folder_path)
            os.mkdir(self.image_folder_path)


class TestSetupDB(TestCase):
    DB_PATH = "media_metadata.db"

    def setUp(self):
        pytest_mocks.patch_get_file_hash(self)
        pytest_mocks.patch_get_ffmpeg_metadata(self)
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)

    def test_setup_db(self):
        assert not os.path.exists(self.DB_PATH)
        bh.setup_db()
        assert os.path.exists(self.DB_PATH)

    def test_setup_db_contents(self):
        media_folders = config_file_handler.load_json_file_content().get("media_folders")
        assert not os.path.exists(self.DB_PATH)
        bh.setup_db()
        with DBCreatorV2() as db_connection:
            media_metadata = db_connection.get_all_content_directory_info()
        print(media_metadata)
        print(media_folders)
        assert len(media_folders) == len(media_metadata)
        assert type(media_folders) is list
        assert type(media_metadata) is list

        for i in range(len(media_folders)):
            assert type(media_folders[i]) is dict
            assert type(media_metadata[i]) is dict
            assert media_metadata[i]
            assert media_folders[i]
            assert media_folders[i].get("content_src")
            assert media_metadata[i].get("content_src")
            assert media_folders[i].get("content_url")
            assert media_metadata[i].get("content_url")

            assert media_folders[i].get("content_src") == media_metadata[i].get("content_src")
            assert media_folders[i].get("content_url") == media_metadata[i].get("content_url")


class TestBackEndFunctionCalls(TestBackEndHandler):
    def test_init(self):
        self.assertTrue(self.backend_handler.startup_sha)
        self.assertTrue(self.backend_handler.chromecast_handler)
        # self.assertTrue(self.backend_handler.media_folder_metadata_handler)

    def test_disk_space(self):
        media_folders = config_file_handler.load_json_file_content().get("media_folders")
        print(media_folders)
        remaining_space = backend_handler.get_free_disk_space(dir_path=media_folders[0].get("content_src"))
        percent_filled = backend_handler.get_free_disk_space_percent(media_folders[0].get("content_src"))
        print(percent_filled)
        print(remaining_space)
        assert remaining_space > 66.7
        assert remaining_space < 77

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

    def test_image_download_already_local_file(self):
        # Add test for each content type
        json_request = {'container_id': None, 'content_id': 17, 'img_src': 'http://192.168.1.175:8000/images/3.jpg',
                        'description': 'World!'}
        bh.download_image(json_request)
        print(json.dumps(json_request, indent=4))
        assert json_request.get("img_src") == "/media_folder_movie/Vampire_2/Vampire (2020).mp4.jpg"

        bh.download_image(json_request)

    def test_image_download_media(self):
        # Add test for each content type
        json_request = {'container_id': None, 'content_id': 17, 'img_src': 'http://192.168.1.175:8000/images/3.jpg',
                        'description': 'World!'}
        bh.download_image(json_request)
        print(json.dumps(json_request, indent=4))
        assert json_request.get("img_src") == "/media_folder_movie/Vampire_2/Vampire (2020).mp4.jpg"

    def test_image_download_season(self):
        # Add test for each content type
        json_request = {'container_id': 1, 'content_id': None, 'img_src': 'http://192.168.1.175:8000/images/3.jpg',
                        'description': 'World!'}
        bh.download_image(json_request)
        print(json.dumps(json_request, indent=4))
        assert json_request.get("img_src") == "/editor_raw_files/Hilda/Season 4.jpg"

    def test_image_download_movie(self):
        # Add test for each content type
        json_request = {'container_id': None, 'content_id': 13, 'img_src': 'http://192.168.1.175:8000/images/3.jpg',
                        'description': 'World!'}
        bh.download_image(json_request)
        print(json.dumps(json_request, indent=4))
        assert json_request.get("img_src") == "/media_folder_modify/output/Sparkles/Sparkles - s2e3.mp4.jpg"

    def test_image_download_tv_show(self):
        # Add test for each content type
        json_request = {'container_id': 2, 'content_id': None, 'img_src': 'http://192.168.1.175:8000/images/3.jpg',
                        'description': 'World!'}
        bh.download_image(json_request)
        print(json.dumps(json_request, indent=4))
        assert json_request.get("img_src") == "/editor_raw_files/Hilda/Hilda.jpg"

    # def test_image_download_playlist(self):
    #     # Add test for each content type
    #     json_request = {'content_type': ContentType.PLAYLIST.value, 'id': 1,
    #                     'image_url': 'http://192.168.1.175:8000/images/3.jpg',
    #                     'description': 'World!!'}
    #     bh.download_image(json_request)
    #     print(json.dumps(json_request, indent=4))
    #     assert json_request.get("image_url") == f"{json_request.get('content_type')}_{json_request.get('id')}.jpg"
    #     json_request = {'content_type': ContentType.PLAYLIST.value, 'id': 1,
    #                     'image_url': 'http://192.168.1.175:8000/images/3.jpg',
    #                     'description': 'World!!'}
    #
    #     self.assertRaises(ValueError, bh.download_image, json_request)

    def test_build_tv_show_output_path(self):
        expected_str = "/Test file name/Test file name - s1e5.mp4"
        file_name_str = "Test file name - s1e5.mp4"
        output_path = bh.build_tv_show_output_path(file_name_str)
        print(output_path)
        print(expected_str)
        assert expected_str in output_path

    def test_get_system_data(self):
        system_data = backend_handler.get_system_data()
        print(json.dumps(system_data, indent=4))

    def test_get_editor_metadata(self):
        editor_metadata = self.backend_handler.get_editor_metadata()
        print(json.dumps(editor_metadata, indent=4))
        assert "txt_file_list" in editor_metadata
        assert type(editor_metadata.get("txt_file_list")) is list
        assert len(editor_metadata.get("txt_file_list")) == 14
        for txt_file in editor_metadata.get("txt_file_list"):
            assert len(txt_file) == 2
            assert "file_name" in txt_file
            assert type(txt_file.get("file_name")) is str
            assert "processed" in txt_file
            assert type(txt_file.get("processed")) is bool

        assert "selected_txt_file_title" in editor_metadata
        assert type(editor_metadata.get("selected_txt_file_title")) is str
        assert editor_metadata.get("selected_txt_file_title") == "2024-01-31_16-32-32.json"

        assert "selected_editor_file_content" in editor_metadata
        assert type(editor_metadata.get("selected_editor_file_content")) is dict
        selected_editor_file_content = editor_metadata.get("selected_editor_file_content")
        assert "splitter_content" in selected_editor_file_content
        assert type(selected_editor_file_content.get("splitter_content")) is list
        assert "media_type" in selected_editor_file_content
        assert type(selected_editor_file_content.get("media_type")) is str
        assert selected_editor_file_content.get("media_type") == ContentType.TV.name
        assert "file_name" in selected_editor_file_content
        assert type(selected_editor_file_content.get("file_name")) is str
        assert selected_editor_file_content.get("file_name") == "2024-01-31_16-32-32.json"
        assert "playlist_title" in selected_editor_file_content
        assert type(selected_editor_file_content.get("playlist_title")) is str
        assert selected_editor_file_content.get("playlist_title") == "Leonard 2"

        assert "editor_process_metadata" in editor_metadata
        assert type(editor_metadata.get("editor_process_metadata")) is dict
        editor_process_metadata = editor_metadata.get("editor_process_metadata")
        assert "process_name" in editor_process_metadata
        assert type(editor_process_metadata.get("process_name")) is str
        assert editor_process_metadata.get("process_name") == "Split queue empty"
        assert "process_end_time" in editor_process_metadata
        assert type(editor_process_metadata.get("process_end_time")) is str
        assert "percent_complete" in editor_process_metadata
        assert type(editor_process_metadata.get("percent_complete")) is int
        assert editor_process_metadata.get("percent_complete") == 0
        assert "process_queue_size" in editor_process_metadata
        assert type(editor_process_metadata.get("process_queue_size")) is int
        assert editor_process_metadata.get("process_queue_size") == 0
        assert "process_log" in editor_process_metadata
        assert type(editor_process_metadata.get("process_log")) is list
        assert not editor_process_metadata.get("process_log")
        assert "process_queue" in editor_process_metadata
        assert type(editor_process_metadata.get("process_queue")) is list
        assert not editor_process_metadata.get("process_queue")

        assert "local_play_url" in editor_metadata
        assert type(editor_metadata.get("local_play_url")) is str

        assert "storage" in editor_metadata
        assert type(editor_metadata.get("storage")) is list
        for storage in editor_metadata.get("storage"):
            assert "free_space" in storage
            assert type(storage.get("free_space")) is int
            assert "percent_used" in storage
            assert type(storage.get("percent_used")) is int
            assert "path" in storage
            assert type(storage.get("path")) is str


class TestBackEndEditorValidateTextFile(TestBackEndHandler):

    def test_editor_validate_txt_file(self):
        editor_metadata = {
            'file_name': "2024-01-31_16-32-36.json",
            'media_type': ContentType.TV.name
        }
        error_log = bh.editor_validate_txt_file(editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert not error_log

    def test_editor_validate_broken_txt_file(self):
        editor_metadata = {
            'file_name': "2024-01-31_16-32-36_invalid.json",
            'media_type': ContentType.TV.name
        }
        error_log = bh.editor_validate_txt_file(editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert error_log
        assert len(error_log) == 3
        assert type(error_log[0]) is dict

        error = error_log[0]
        assert "Values less than 0" == error.get("message")
        assert "13:-3" == error.get("value")
        assert 0 == error.get("hour")
        assert 13 == error.get("minute")
        assert -3 == error.get("second")

        error = error_log[1]
        assert "End time >= start time" == error.get("message")

        error = error_log[2]
        assert "Errors occurred while parsing line" == error.get("message")

    def test_editor_validate_movie_txt_file(self):
        editor_metadata = {
            'file_name': "movie.json",
            'media_type': ContentType.MOVIE.name
        }
        error_log = bh.editor_validate_txt_file(editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert not error_log

    def test_editor_validate_tv_json_file(self):
        editor_metadata = {
            'file_name': "2024-01-31_16-32-32.json",
            'media_type': ContentType.TV.name
        }
        error_log = bh.editor_validate_txt_file(editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert not error_log

    def test_editor_validate_movie_json_file(self):
        editor_metadata = {
            'file_name': "movie.json",
            'media_type': ContentType.MOVIE.name
        }
        error_log = bh.editor_validate_txt_file(editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert not error_log

    def test_editor_validate_raw_json_file(self):
        editor_metadata = {
            'file_name': "Hilda/Hilda - s4e8.json",
            'media_type': ContentType.RAW.name
        }
        error_log = bh.editor_validate_txt_file(editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert not error_log

    def test_editor_validate_book_json_file(self):
        editor_metadata = {
            'file_name': "book.json",
            'media_type': ContentType.BOOK.name
        }
        error_log = bh.editor_validate_txt_file(editor_metadata)
        print(json.dumps(error_log, indent=4))
        assert not error_log


class TestBackEndEditorProcessTextFile(TestBackEndHandler):

    def test_editor_process_system_out_of_space(self):
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)
        expected_output = [
            {
                "message": "System out of space"
            }
        ]
        json_request = {
            'file_name': "Pocoyo/2022-05-13_16-56-51.json",
            "media_type": ContentType.TV.name
        }
        with mock.patch('backend_handler.DISK_SPACE_USE_LIMIT', 100):
            errors = self.backend_handler.editor_process_txt_file(json_request.get("media_type"), json_request.get("file_name"))
        print(json.dumps(errors, indent=4))
        assert errors == expected_output

    def test_editor_process_tv_txt_file(self):
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)

        json_request = {
            'file_name': "2024-01-31_16-32-36.json",
            "media_type": ContentType.TV.name
        }
        raw_folder = config_file_handler.load_json_file_content().get('editor_raw_folder')
        with DBCreatorV2() as db_connection:
            media_folder_path = db_connection.get_all_content_directory_info()[0]
        output_path = pathlib.Path(media_folder_path.get("content_src")).resolve()
        errors = self.backend_handler.editor_process_txt_file(json_request.get("media_type"),
                                                              json_request.get("file_name"))
        print(json.dumps(errors, indent=4))
        assert not errors

    def test_editor_process_tv_json_file(self):
        file_name = "2024-01-31_16-32-32.json"
        media_type = ContentType.TV.name
        errors = self.backend_handler.editor_process_txt_file(media_type, file_name)
        print(json.dumps(errors, indent=4))
        assert not errors

    def test_editor_process_movie_json_file(self):
        file_name = "movie.json"
        media_type = ContentType.MOVIE.name
        errors = self.backend_handler.editor_process_txt_file(media_type, file_name)
        print(json.dumps(errors, indent=4))
        assert not errors

    def test_editor_process_raw_json_file(self):
        file_name = "Hilda/Hilda - s4e8.json"
        media_type = ContentType.RAW.name
        errors = self.backend_handler.editor_process_txt_file(media_type, file_name)

        print(json.dumps(errors, indent=4))
        assert not errors

    def test_editor_process_book_json_file(self):
        file_name = "book.json",
        media_type = ContentType.BOOK.name
        errors = self.backend_handler.editor_process_txt_file(media_type, file_name)

        print(json.dumps(errors, indent=4))
        assert not errors
