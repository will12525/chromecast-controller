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

    def test_get_connected_devices_list_str(self):
        self.test_connect_to_chromecast()
        connected_devices_list = self.chromecast_handler.get_connected_devices_list_str()
        self.assertEqual(type(connected_devices_list), list)

    def test_connect_to_chromecast(self):
        self.chromecast_handler.connect_to_chromecast(self.CHROMECAST_ID)
        connected_devices_list = self.chromecast_handler.get_connected_devices_list_str()
        self.assertTrue(self.CHROMECAST_ID in connected_devices_list)

    def test_disconnect_from_chromecast(self):
        self.test_connect_to_chromecast()
        self.chromecast_handler.disconnect_from_chromecast(self.CHROMECAST_ID)
        connected_devices = self.chromecast_handler.get_connected_devices_list_str()
        self.assertEqual(len(connected_devices), 0)

    def test_get_chromecast_device(self):
        self.chromecast_handler.scan_for_chromecasts()
        chromecast_scan_list = self.chromecast_handler.get_scan_list()
        self.assertTrue(chromecast_scan_list)
        self.chromecast_handler.connect_to_chromecast(self.CHROMECAST_ID)
        connected_devices_list = self.chromecast_handler.get_connected_devices_list_str()

        self.assertTrue(connected_devices_list)
        self.assertEqual(len(connected_devices_list), 1)
        chromecast_device = self.chromecast_handler.get_chromecast_device(self.CHROMECAST_ID)
        self.assertEqual(chromecast_device.ID_STR, self.CHROMECAST_ID)


class TestChromecastCommands(TestChromecastHandler):
    # Requires Visual acknowledgement
    def test_play_from_media_drive(self):
        self.chromecast_handler.connect_to_chromecast(self.CHROMECAST_ID)
        connected_devices_list = self.chromecast_handler.get_connected_devices_list_str()
        self.assertTrue(self.CHROMECAST_ID in connected_devices_list)

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
