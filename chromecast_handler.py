import logging
import threading
import time
from enum import Enum, auto

import pychromecast

from media_folder_metadata_handler import MediaFolderMetadataHandler

CHROMECAST_DEVICE_BED_ROOM_STR = ["Master Bedroom TV"]
CHROMECAST_DEVICE_LIVING_ROOM_STR = "Family Room TV"


class CommandList(Enum):
    CMD_REWIND = auto()
    CMD_REWIND_15 = auto()
    CMD_PLAY = auto()
    CMD_PAUSE = auto()
    CMD_SKIP_15 = auto()
    CMD_SKIP = auto()
    CMD_STOP = auto()

    CMD_PLAY_NEXT = auto()
    CMD_PLAY_PREV = auto()


class PlayerState(Enum):
    STATE_WAITING = auto()
    STATE_NEW_EPISODE_START = auto()
    STATE_NEW_EPISODE_BUFFERING = auto()
    STATE_EPISODE_PLAYING = auto()
    STATE_EPISODE_PAUSED = auto()
    STATE_EPISODE_BUFFERING = auto()


class MyMediaDevice:
    DEFAULT_MEDIA_TYPE = "video/mp4"
    media_folder_metadata_handler = None
    last_time_check = 0
    last_state = None
    cmd_data_dict = {}
    my_last_player_state = 0

    status = None

    def __init__(self, media_controller):
        self.media_controller = media_controller
        self.my_last_player_state = PlayerState.STATE_WAITING

        self.cmd_data_dict[CommandList.CMD_REWIND] = self.media_controller.rewind
        self.cmd_data_dict[CommandList.CMD_REWIND_15] = self.rewind_15
        self.cmd_data_dict[CommandList.CMD_PLAY] = self.media_controller.play
        self.cmd_data_dict[CommandList.CMD_PAUSE] = self.media_controller.pause
        self.cmd_data_dict[CommandList.CMD_SKIP_15] = self.skip_15
        self.cmd_data_dict[CommandList.CMD_SKIP] = self.media_controller.skip
        self.cmd_data_dict[CommandList.CMD_STOP] = self.media_controller.stop

        self.cmd_data_dict[CommandList.CMD_PLAY_NEXT] = self.media_controller.queue_next
        self.cmd_data_dict[CommandList.CMD_PLAY_PREV] = self.media_controller.queue_prev

        self.media_controller.register_status_listener(self)

    def __del__(self):
        self.media_controller = None

    def play_episode(self, media_folder_metadata_handler, media_server_url):
        self.media_folder_metadata_handler = media_folder_metadata_handler
        self.play_url(media_server_url)

    def play_next_episode(self, media_server_url):
        if self.media_folder_metadata_handler:
            self.media_folder_metadata_handler.increment_next_episode()
            self.play_url(media_server_url)

    def play_url(self, media_server_url):
        url = self.media_folder_metadata_handler.get_url(media_server_url)
        print(f"PLAYING URL {url}")
        self.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE,
                                         title=self.media_folder_metadata_handler.get_title())
        self.media_controller.block_until_active()
        self.my_last_player_state = PlayerState.STATE_NEW_EPISODE_START

    def get_media_current_time(self):
        if self.status:
            return self.status.adjusted_current_time

    def get_media_current_duration(self):
        if self.status:
            return self.status.duration

    def get_media_current_title(self):
        if self.status:
            return self.status.title

    def get_media_controller_metadata(self):
        if self.status:
            return {
                "media_runtime": self.get_media_current_time(),
                "media_duration": self.get_media_current_duration(),
                "media_title": self.get_media_current_title()
            }

    def append_queue_url(self, url):
        self.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE, enqueue=True)

    def seek(self, position):
        self.media_controller.seek(position)

    def interpret_enum_cmd(self, cmd_enum):
        if cmd := self.cmd_data_dict.get(cmd_enum):
            cmd()

    def get_current_media_status(self):
        return self.status

    def rewind_15(self):
        if self.status:
            self.seek(self.status.adjusted_current_time - 15)

    def skip_15(self):
        if self.status:
            self.seek(self.status.adjusted_current_time + 15)

    def new_media_status(self, status):
        self.status = status
        print("----- STATUS LISTENER UPDATE -----")
        message = ""
        message += f'Status: {status}'
        if self.media_folder_metadata_handler:
            message += f'\n{self.media_folder_metadata_handler.get_title()}'

        # print(message)
        logging.info(message)

    def update_player(self, media_server_url):
        current_timestamp = time.time()
        if self.media_controller:
            player_state = self.media_controller.status.player_state
            current_device_timestamp = self.media_controller.status.adjusted_current_time
            if not self.last_state:
                self.last_state = player_state

            # If we have a media object than we can auto increment to the next episode
            if self.media_folder_metadata_handler:
                # If we went into IDLE after playing
                if player_state == "IDLE":
                    if self.last_state == "PLAYING" and self.my_last_player_state == PlayerState.STATE_EPISODE_PLAYING:
                        self.play_next_episode(media_server_url)
                # If we started playing, print the current media url
                if player_state == "PLAYING":
                    self.my_last_player_state = PlayerState.STATE_EPISODE_PLAYING
                if player_state == "PAUSED":
                    self.my_last_player_state = PlayerState.STATE_EPISODE_PAUSED
                if player_state == "BUFFERING":
                    if self.my_last_player_state == PlayerState.STATE_NEW_EPISODE_START:
                        self.my_last_player_state = PlayerState.STATE_NEW_EPISODE_BUFFERING
                    else:
                        self.my_last_player_state = PlayerState.STATE_EPISODE_BUFFERING

            self.last_state = player_state
            # Update every 5 seconds
            if current_timestamp - self.last_time_check > 5:
                print("\n----- STATUS UPDATE -----")
                self.status = self.media_controller.status
                current_runtime = 0
                # current_runtime = self.media_controller.status.

                print(f"\n{current_runtime}")
                print(type(player_state))

                print(f"CURRENT PLAYER STATE: {player_state}")
                print(self.media_controller.status)
                self.last_time_check = current_timestamp


class ChromecastHandler(threading.Thread):
    SCAN_INTERVAL = 2

    chromecast_device = None
    chromecast_browser = None
    media_controller = None

    last_scanned_devices = []
    last_scan_time = 0

    media_server_url = None

    run_update = False

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        logging.basicConfig(filename='status_change.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',
                            level=logging.DEBUG)

    def __del__(self):
        print("deleting ChromecastHandler")
        self.run_update = False
        self.disconnect_chromecast()

    def get_scan_list(self):
        return self.last_scanned_devices

    def scan_for_chromecasts(self):
        services, browser = pychromecast.discovery.discover_chromecasts()
        browser.stop_discovery()
        self.last_scanned_devices = [getattr(service, "friendly_name") for service in services]

    def connect_chromecast(self, chromecast_id):
        chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[chromecast_id])
        if len(chromecasts) > 0:
            chromecast = chromecasts[0]
            if getattr(chromecast.cast_info, "friendly_name") == chromecast_id:
                chromecast.wait()
                self.chromecast_device = chromecast
                self.media_controller = MyMediaDevice(chromecast.media_controller)
                self.chromecast_browser = browser
                return True
        return False

    def disconnect_chromecast(self):
        self.chromecast_device = None
        self.media_controller = None
        if self.chromecast_browser:
            self.chromecast_browser.stop_discovery()

    def get_media_controller(self) -> MyMediaDevice:
        return self.media_controller

    def get_media_controller_metadata(self):
        if self.media_controller:
            return self.media_controller.get_media_controller_metadata()

    def get_chromecast_id(self) -> str:
        if self.chromecast_device:
            return self.chromecast_device.name

    def get_media_current_time(self):
        if self.media_controller:
            return self.media_controller.get_media_current_time()

    def get_media_current_duration(self):
        if self.media_controller:
            return self.media_controller.get_media_current_duration()

    def seek_media_time(self, media_time):
        if self.media_controller:
            self.media_controller.seek(media_time)

    def get_current_playing_episode_info(self):
        if self.media_controller:
            if self.media_controller.media_folder_metadata_handler:
                return self.media_controller.media_folder_metadata_handler.get_episode_info()

    def play_from_media_drive(self, media_folder_metadata_handler: MediaFolderMetadataHandler, media_server_url):
        if self.media_controller:
            self.media_server_url = media_server_url
            self.media_controller.play_episode(media_folder_metadata_handler, media_server_url)

    def send_command(self, media_device_command):
        if self.media_controller:
            self.media_controller.interpret_enum_cmd(media_device_command)

    def run(self):
        self.run_update = True
        # self.scan_for_chromecasts()
        while self.run_update:
            try:
                if self.media_controller:
                    self.media_controller.update_player(self.media_server_url)
                if time.time() - self.last_scan_time > self.SCAN_INTERVAL:
                    self.scan_for_chromecasts()
                    self.last_scan_time = time.time()

                time.sleep(0.1)
            except KeyboardInterrupt:
                break
