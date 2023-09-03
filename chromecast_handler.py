import threading
import time
from enum import Enum

import pychromecast

CHROMECAST_DEVICE_BED_ROOM_STR = ["Master Bedroom TV"]
CHROMECAST_DEVICE_LIVING_ROOM_STR = "Family Room TV"


class CommandList(Enum):
    CMD_DEVICE_WAIT = 0
    CMD_PLAY = 1
    CMD_PAUSE = 2
    CMD_STOP = 3
    CMD_RESTART = 4
    CMD_SKIP = 5
    CMD_PLAY_NEXT = 6
    CMD_PLAY_PREV = 7


class PlayerState(Enum):
    STATE_WAITING = 0
    STATE_NEW_EPISODE_START = 1
    STATE_NEW_EPISODE_BUFFERING = 2
    STATE_EPISODE_PLAYING = 3
    STATE_EPISODE_PAUSED = 4
    STATE_EPISODE_BUFFERING = 5


class MyMediaDevice:
    DEFAULT_MEDIA_TYPE = "video/mp4"
    media_start_time = None
    player_state = None
    initialized = False
    current_url = ""
    current_episode_info = None
    last_time_check = 0
    last_state = None
    media_player_active = False
    cmd_data_dict = {}
    ID_STR = ""
    episode_info = None
    browser = None
    my_last_player_state = 0

    # new_episode_started = False

    def __init__(self, cast_device_id_str, cast_device, browser):
        # threading.Thread.__init__(self)
        self.ID_STR = cast_device_id_str
        self.cast_device = cast_device
        self.media_controller = cast_device.media_controller
        self.browser = browser
        self.my_last_player_state = PlayerState.STATE_WAITING
        # self.browser = browser

        self.cmd_data_dict[CommandList.CMD_DEVICE_WAIT] = self.cast_device.wait
        self.cmd_data_dict[CommandList.CMD_PLAY] = self.media_controller.play
        self.cmd_data_dict[CommandList.CMD_PAUSE] = self.media_controller.pause
        self.cmd_data_dict[CommandList.CMD_STOP] = self.media_controller.stop
        self.cmd_data_dict[CommandList.CMD_RESTART] = self.media_controller.rewind
        self.cmd_data_dict[CommandList.CMD_SKIP] = self.media_controller.skip
        self.cmd_data_dict[CommandList.CMD_PLAY_NEXT] = self.media_controller.queue_next
        self.cmd_data_dict[CommandList.CMD_PLAY_PREV] = self.media_controller.queue_prev

        self.interpret_enum_cmd(CommandList.CMD_DEVICE_WAIT)
        self.initialized = True

    def __del__(self):
        self.initialized = False
        if self.browser:
            self.browser.stop_discovery()

    def play_episode(self, current_episode_info, media_server_url):
        self.current_episode_info = current_episode_info
        url = self.current_episode_info.get_url(media_server_url)
        print(f"PLAYING URL {url}")
        # self.current_url = url
        self.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE)
        self.media_controller.block_until_active()
        self.my_last_player_state = PlayerState.STATE_NEW_EPISODE_START
        # self.interpret_enum_cmd(CommandList.CMD_PLAY)

    def append_queue_url(self, url):
        self.cast_device.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE, enqueue=True)

    def seek(self):
        self.media_controller.seek()

    def stop_scanner(self):
        self.initialized = False

    def interpret_enum_cmd(self, cmd_enum):
        print(f"PROCESSING CMD FOR {self.ID_STR}")
        if cmd := self.cmd_data_dict.get(cmd_enum):
            cmd()

    def update_player(self, media_server_url):
        # if self.cast_device.media_controller:
        #     print(self.cast_device.media_controller.status.player_state)
        # else:
        #     print("___________________NO MEDIA_CONTROLLER_______________")
        if self.initialized and self.cast_device and self.cast_device.media_controller:
            current_device_timestamp = self.cast_device.media_controller.status.adjusted_current_time
            # Check if the player state changed
            if self.player_state != self.cast_device.media_controller.status.player_state:
                self.player_state = self.cast_device.media_controller.status.player_state
                if not self.last_state:
                    self.last_state = self.player_state
                print(f"\nDEVICE: {self.ID_STR}, NEW PLAYER STATE: {self.player_state}")

                # If we have a media object than we can auto increment to the next episode
                if self.current_episode_info:
                    # If we went into IDLE after playing
                    if self.player_state == "IDLE":
                        if self.last_state == "PLAYING" and self.my_last_player_state == PlayerState.STATE_EPISODE_PLAYING:
                            # print("IN PAUSE")
                            self.current_episode_info.increment_next_episode()
                            print(f"Adding next episode: {current_device_timestamp}")
                            # self.play_url(self.current_episode_info.get_url())
                            self.play_episode(self.current_episode_info, media_server_url)
                        # else:
                        # self.new_episode_started = False
                        # print("SENDING PAUSE")
                        # self.interpret_enum_cmd(CommandList.CMD_PAUSE)
                        print(f"LAST PLAYER STATE {self.last_state}")
                    # If we started playing, print the current media url
                    if self.player_state == "PLAYING":
                        # self.media_player_active = True
                        self.my_last_player_state = PlayerState.STATE_EPISODE_PLAYING
                        print(
                            f"DEVICE: {self.ID_STR}, NOW PLAYING: {self.current_episode_info.get_url(media_server_url)}")
                    if self.player_state == "PAUSED":
                        self.my_last_player_state = PlayerState.STATE_EPISODE_PAUSED
                    if self.player_state == "BUFFERING":
                        if self.my_last_player_state == PlayerState.STATE_NEW_EPISODE_START:
                            self.my_last_player_state = PlayerState.STATE_NEW_EPISODE_BUFFERING
                        else:
                            self.my_last_player_state = PlayerState.STATE_EPISODE_BUFFERING
                else:
                    print("NO CURRENT EPISODE INFO")
                self.last_state = self.player_state
            # Update every 5 seconds
            if current_device_timestamp - self.last_time_check > 5:
                print("----- STATUS UPDATE -----")
                print(self.cast_device.media_controller)
                # print(self.cast_device.media_controller.status.season)
                print(self.cast_device.media_controller.status)
                # print(self.cast_device.media_controller.status.is_active_input)
                # print(f"Play Time: {current_device_timestamp}")
                self.last_time_check = current_device_timestamp


class ChromecastHandler(threading.Thread):
    SCAN_INTERVAL = 60
    # browser = None
    connected_devices = {}
    last_scanned_devices = []
    initialized = False
    last_scan_time = 0
    browser = None
    media_server_url = None

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.initialized = True

    def __del__(self):
        print("deleting ChromecastHandler")
        self.initialized = False
        # if self.browser:
        #     self.browser.stop_discovery()

    def get_scan_list(self):
        return self.last_scanned_devices

    def scan_for_chromecasts(self):
        print("-------------- SCAN --------------")
        services, browser = pychromecast.discovery.discover_chromecasts()
        browser.stop_discovery()
        for service in services:
            print(type(service))
            print(service)
            print(service)

        self.last_scanned_devices = [getattr(service, "friendly_name") for service in services]

    def connect_to_chromecast(self, chromecast_id_str) -> MyMediaDevice:
        chromecasts, new_browser = pychromecast.get_listed_chromecasts(friendly_names=[chromecast_id_str])
        # if not self.browser:
        # self.browser = new_browser

        if len(chromecasts) > 0:
            chromecast = chromecasts[0]
            if getattr(chromecast.cast_info, "friendly_name") == chromecast_id_str:
                connected_device_key_list = list(self.connected_devices.keys())
                for key in connected_device_key_list:
                    self.disconnect_from_chromecast(key)
                self.connected_devices[chromecast_id_str] = MyMediaDevice(chromecast_id_str, chromecast, new_browser)

        self.initialized = True

        return self.get_chromecast_device(chromecast_id_str)

    def disconnect_from_chromecast(self, chromecast_id_str):
        self.connected_devices.pop(chromecast_id_str)

    def get_chromecast_device(self, chromecast_id) -> MyMediaDevice:
        if len(self.connected_devices) > 0:
            return self.connected_devices.get(chromecast_id)

    def get_connected_devices_list_str(self):
        return [connected_device.ID_STR for key, connected_device in self.connected_devices.items()]

    def play_from_media_drive(self, current_episode_info, media_server_url):
        self.media_server_url = media_server_url
        # current_episode_url = current_episode_info.get_url()
        for key, connected_device in self.connected_devices.items():
            # connected_device.play_url(current_episode_url)
            connected_device.play_episode(current_episode_info, self.media_server_url)

    def send_command(self, media_device_command):
        for key, connected_device in self.connected_devices.items():
            connected_device.interpret_enum_cmd(media_device_command)

    def run(self):
        while self.initialized:
            try:
                for connected_device_key in self.connected_devices:
                    my_media_device = self.connected_devices.get(connected_device_key)
                    if my_media_device:
                        my_media_device.update_player(self.media_server_url)
                    else:
                        print(f"No device found for {connected_device_key}")

                if time.time() - self.last_scan_time > self.SCAN_INTERVAL:
                    self.scan_for_chromecasts()
                    self.last_scan_time = time.time()

                time.sleep(0.1)
            except KeyboardInterrupt:
                break


# HANDLES USER INPUT
# Getting user input for __main__
class MyThread(threading.Thread):
    new_input = False
    user_input = None
    check_user_input = False
    thread_name = None
    thread_id = None

    def __init__(self, thread_name, thread_id):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.thread_id = thread_id
        self.check_user_input = True
        # helper function to execute the threads

    def stop(self):
        self.check_user_input = False

    def new_user_input(self):
        return self.new_input

    def get_user_input(self) -> int:
        self.new_input = False
        return self.user_input

    def run(self):
        while self.check_user_input:
            try:
                user_input = int(input("Enter command: "))
                self.user_input = user_input
                self.new_input = True

            except KeyboardInterrupt:
                break
            except ValueError:
                break
