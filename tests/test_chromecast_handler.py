from unittest import TestCase

from chromecast_handler import ChromecastHandler, CommandList
from media_folder_metadata_handler import MediaFolderMetadataHandler


class TestChromecastHandler(TestCase):
    SERVER_URL_TV_SHOWS = "http://192.168.1.200:8000/tv_shows/"
    MEDIA_FOLDER_PATH = "/media/hdd1/plex_media/tv_shows/"
    MEDIA_METADATA_FILE = "tv_show_metadata.json"
    # CHROMECAST_ID = "Family Room TV"

    CHROMECAST_ID = "Master Bedroom TV"

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


class TestChromecastCommands(TestChromecastHandler):
    # Requires Visual acknowledgement
    def test_play_from_media_drive(self):
        self.chromecast_handler.connect_chromecast(self.CHROMECAST_ID)
        chromecast_id = self.chromecast_handler.get_chromecast_id()
        self.assertTrue(self.CHROMECAST_ID == chromecast_id)

        self.chromecast_handler.play_from_media_drive(MediaFolderMetadataHandler(
            self.MEDIA_METADATA_FILE, self.MEDIA_FOLDER_PATH), self.SERVER_URL_TV_SHOWS)
        pass

    def test_send_command(self):
        self.test_play_from_media_drive()
        self.chromecast_handler.send_command(CommandList.CMD_PAUSE)
        # Need to get way to check current state
        pass

    def test_run(self):
        # Test thread startup?
        pass
