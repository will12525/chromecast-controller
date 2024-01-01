from unittest import TestCase

from pychromecast.controllers.media import MediaStatus

from chromecast_handler import ChromecastHandler
from database_handler import common_objects


class TestChromecastHandler(TestCase):
    CHROMECAST_ID = "Test Cast"

    def setUp(self):
        self.chromecast_handler = ChromecastHandler()


class TestChromecastScanning(TestChromecastHandler):

    def test_get_scan_list(self):
        scan_list = self.chromecast_handler.get_scan_list()
        self.assertEqual(type(scan_list), list)

    def test_scan_for_chromecasts(self):
        self.chromecast_handler.scan_for_chromecasts()
        scan_list = self.chromecast_handler.get_scan_list()
        self.assertTrue(scan_list)
        print(scan_list)


class TestChromecastConnection(TestChromecastHandler):

    def test_get_chromecast_device_id(self):
        self.test_connect_to_chromecast()
        self.assertEqual(type(self.chromecast_handler.get_chromecast_id()), str)

    def test_connect_to_chromecast(self):
        self.chromecast_handler.connect_chromecast(self.CHROMECAST_ID)
        self.assertTrue(self.chromecast_handler.media_controller)
        self.assertEqual(self.chromecast_handler.get_chromecast_id(), self.CHROMECAST_ID)

    def test_disconnect_from_chromecast(self):
        self.test_connect_to_chromecast()
        self.chromecast_handler.disconnect_chromecast()
        self.assertFalse(self.chromecast_handler.get_media_controller())

    def test_get_chromecast_device(self):
        self.chromecast_handler.scan_for_chromecasts()
        chromecast_scan_list = self.chromecast_handler.get_scan_list()
        self.assertTrue(chromecast_scan_list)
        self.chromecast_handler.connect_chromecast(self.CHROMECAST_ID)

        # Random failure count: 1
        self.assertTrue(self.chromecast_handler.media_controller)
        self.assertEqual(self.chromecast_handler.get_chromecast_id(), self.CHROMECAST_ID)


# class TestChromecastCommands(TestChromecastHandler):
# Requires Visual acknowledgement
# def test_play_from_media_drive(self):
#     self.chromecast_handler.connect_chromecast(self.CHROMECAST_ID)
#     chromecast_id = self.chromecast_handler.get_chromecast_id()
#     self.assertTrue(self.CHROMECAST_ID == chromecast_id)
#
#     self.chromecast_handler.play_from_media_drive(MediaFolderMetadataHandler(
#         self.MEDIA_METADATA_FILE, self.MEDIA_FOLDER_PATH), self.SERVER_URL_TV_SHOWS)
#     print(self.chromecast_handler.get_media_controller().media_folder_metadata_handler.get_url(
#         self.SERVER_URL_TV_SHOWS))

# def test_get_current_playing_episode_info(self):
#     self.test_play_from_media_drive()
#     episode_info = self.chromecast_handler.get_current_playing_episode_info()
#
#     self.assertTrue(episode_info)
#     self.assertEqual(type(episode_info), dict)
#
#     self.assertTrue(episode_info.get("name"))
#
#     pass

# def test_get_current_timestamp(self):
#     self.test_get_current_playing_episode_info()
#     while not (current_media_runtime := self.chromecast_handler.get_media_current_time()):
#         pass
#     print(current_media_runtime)
#
# def test_get_current_status(self):
#     self.test_get_current_playing_episode_info()
#
# def test_send_command(self):
#     self.test_play_from_media_drive()
#     self.chromecast_handler.send_command(CommandList.CMD_PAUSE)
#     # Need to get way to check current state
#     pass
#
# def test_run(self):
#     # Test thread startup?
#     pass


class TestMyMediaDevice(TestCase):
    CHROMECAST_ID = "Test Cast"

    chromecast_handler = None
    media_controller = None

    def setUp(self):
        self.chromecast_handler = ChromecastHandler()
        self.chromecast_handler.connect_chromecast(self.CHROMECAST_ID)
        self.media_controller = self.chromecast_handler.get_media_controller()


# Integration test with Chromecast networked device
class TestMediaPlayer(TestMyMediaDevice):

    # def test_play_episode(self):
    #     # self.media_controller.play_episode(MediaFolderMetadataHandler(
    #     #     self.MEDIA_METADATA_FILE, self.MEDIA_FOLDER_PATH), self.SERVER_URL_TV_SHOWS)
    #     while not self.media_controller.get_current_media_status():
    #         pass
    #     self.assertTrue(self.media_controller.get_current_media_status())

    def test_play_next_episode(self):
        compare_value = {'id': 2, 'tv_show_id': 1, 'season_id': 1, 'media_directory_id': 1, 'media_title': 'mysterious',
                         'path': '\\Vampire\\Season 1\\Vampire - s01e002.mp4', 'media_type': 5,
                         'media_directory_path': '../media_folder_sample', 'new_media_directory_path': None,
                         'media_directory_url': 'http://192.168.1.200:8000/tv_shows/', 'playlist_id': 1,
                         'playlist_title': 'Vampire', 'season_index': 1, 'season_title': 'Season 1',
                         'tv_show_title': 'Vampire', 'title': 'Vampire Season 1 mysterious', 'metadataType': 0}

        media_status = MediaStatus()
        media_status.media_metadata = {common_objects.PLAYLIST_ID_COLUMN: 1, common_objects.ID_COLUMN: 1}
        self.media_controller.status = media_status
        next_media_metadata = self.media_controller.play_next_episode()
        # print(next_media_metadata)

        assert compare_value == next_media_metadata

    def test_play_next_episode_no_playlist(self):
        media_status = MediaStatus()
        media_status.media_metadata = {common_objects.ID_COLUMN: 1}
        self.media_controller.status = media_status
        next_media_metadata = self.media_controller.play_next_episode()
        # print(next_media_metadata)
        assert not next_media_metadata

    def test_play_previous_episode(self):
        compare_value = {'id': 1, 'tv_show_id': 1, 'season_id': 1, 'media_directory_id': 1, 'media_title': 'sparkle',
                         'path': '\\Vampire\\Season 1\\Vampire - s01e001.mp4', 'media_type': 5,
                         'media_directory_path': '../media_folder_sample', 'new_media_directory_path': None,
                         'media_directory_url': 'http://192.168.1.200:8000/tv_shows/', 'playlist_id': 1,
                         'playlist_title': 'Vampire', 'season_index': 1, 'season_title': 'Season 1',
                         'tv_show_title': 'Vampire', 'title': 'Vampire Season 1 sparkle', 'metadataType': 0}

        media_status = MediaStatus()
        media_status.media_metadata = {common_objects.PLAYLIST_ID_COLUMN: 1, common_objects.ID_COLUMN: 2}
        self.media_controller.status = media_status
        next_media_metadata = self.media_controller.play_previous_episode()
        assert compare_value == next_media_metadata

    def test_play_url(self):
        pass

    # def test_get_media_current_time(self):
    #     self.test_play_episode()
    #     while not self.media_controller.get_media_current_time():
    #         pass
    #
    #     self.assertTrue(self.media_controller.get_media_current_time())
    #
    # def test_get_media_current_duration(self):
    #     self.test_play_episode()
    #     while not self.media_controller.get_media_current_duration():
    #         pass
    #
    #     self.assertTrue(self.media_controller.get_media_current_duration())

    def test_append_queue_url(self):
        pass

    def test_seek(self):
        pass

    def test_interpret_enum_cmd(self):
        pass

    def test_get_current_media_status(self):
        pass

    def test_new_media_status(self):
        pass

    def test_update_player(self):
        pass
