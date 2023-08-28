import time
import os
import traceback
import threading
from enum import Enum
import pychromecast
import git

# provide list of shows
# provide list of seasons
# provide list of episodes
OFFSET = -1
TV_SHOW_ID = 2
TV_SHOW_ID_OFFSET = OFFSET
TV_SHOW_SEASON_ID = 1
TV_SHOW_SEASON_ID_OFFSET = OFFSET
TV_SHOW_SEASON_EPISODE_ID = 4
TV_SHOW_SEASON_EPISODE_ID_OFFSET = OFFSET


CHROMECAST_DEVICE_BED_ROOM_STR = ["Master Bedroom TV"]
CHROMECAST_DEVICE_LIVING_ROOM_STR = "Family Room TV"

SERVER_URL = "http://192.168.1.200:8000/"
SERVER_URL_TV_SHOWS = SERVER_URL + "tv_shows/"

repo = git.Repo(search_parent_directories=True)
startup_sha = repo.head.object.hexsha


def get_dir_list(dir_path):
    if os.path.exists(dir_path):
        unsorted_dir_path_list = os.listdir(dir_path)
        sorted_dir_path_list = sorted(unsorted_dir_path_list)
        return sorted_dir_path_list


class EpisodeInfo:
    tv_show_id = 0
    tv_show_season_id = 0
    tv_show_season_episode_id = 0

    def __init__(self, tv_show_id=0, tv_show_season_id=0, tv_show_season_episode_id=0):
        self.media_url_builder = MediaURLBuilder()
        self.tv_show_id = tv_show_id
        self.tv_show_season_id = tv_show_season_id
        self.tv_show_season_episode_id = tv_show_season_episode_id

    def is_valid(self):
        return self.media_url_builder.valid_tv_show_season_episode_id(self.tv_show_id, self.tv_show_season_id,
                                                                      self.tv_show_season_episode_id)

    def get_url(self):
        return self.media_url_builder.get_tv_show_season_episode_url(self.tv_show_id, self.tv_show_season_id,
                                                                     self.tv_show_season_episode_id)

    def increment_episode(self):
        new_tv_show_season_id = self.tv_show_season_id + 1
        new_tv_show_season_episode_id = self.tv_show_season_episode_id + 1

        if self.media_url_builder.valid_tv_show_season_episode_id(self.tv_show_id, self.tv_show_season_id,
                                                                  new_tv_show_season_episode_id):
            self.tv_show_season_episode_id = new_tv_show_season_episode_id
        elif self.media_url_builder.valid_tv_show_season_id(self.tv_show_id, new_tv_show_season_episode_id):
            self.tv_show_season_id = new_tv_show_season_id
            self.tv_show_season_episode_id = 0
        else:
            self.tv_show_season_id = 0
            self.tv_show_season_episode_id = 0

        return self.is_valid()


class MediaURLBuilder:
    TV_SHOW_DIR_PATH = "/media/hdd1/plex_media/tv_shows/"

    tv_shows_dir_path_list = None

    def __init__(self):
        self.tv_shows_dir_path_list = get_dir_list(self.TV_SHOW_DIR_PATH)

    def sort_season_dir_list(self, tv_show_id):
        unsorted_tv_show_season_name_list = os.listdir(self.get_tv_show_dir_path(tv_show_id))
        sorted_tv_show_season_name_dict = {}
        title_str = "n "
        for tv_show_season_name_str in unsorted_tv_show_season_name_list:
            if title_str in tv_show_season_name_str:
                try:
                    tv_show_season_name_id_str = tv_show_season_name_str[
                                                 tv_show_season_name_str.index(title_str) + len(title_str):
                                                 ]
                    tv_show_season_name_id_int = int(tv_show_season_name_id_str) + TV_SHOW_SEASON_ID_OFFSET

                    sorted_tv_show_season_name_dict[tv_show_season_name_id_int] = tv_show_season_name_str

                except ValueError:
                    print(f"ERROR: {tv_show_season_name_str}")
                except Exception:
                    print(f"ERROR READING: {unsorted_tv_show_season_name_list}")
                    print(traceback.format_exc())

        sorted_tv_show_season_name_dict_keys = list(sorted_tv_show_season_name_dict.keys())
        sorted_tv_show_season_name_dict_keys.sort()
        return [sorted_tv_show_season_name_dict[i] for i in sorted_tv_show_season_name_dict_keys]

    def get_tv_show_dir_list(self):
        return self.tv_shows_dir_path_list

    def get_tv_show_dir_name(self, tv_show_id):
        if self.valid_tv_show_id(tv_show_id):
            return self.get_tv_show_dir_list()[tv_show_id]
        return None

    def get_tv_show_dir_path(self, tv_show_id):
        return self.TV_SHOW_DIR_PATH + self.get_tv_show_dir_name(tv_show_id)

    def get_tv_show_season_dir_list(self, tv_show_id):
        return self.sort_season_dir_list(tv_show_id)

    def get_tv_show_season_dir_name(self, tv_show_id, tv_show_season_id):
        if self.valid_tv_show_season_id(tv_show_id, tv_show_season_id):
            return self.get_tv_show_season_dir_list(tv_show_id)[tv_show_season_id]

    def get_tv_show_season_dir_path(self, tv_show_id, tv_show_season_id):
        return f"{self.get_tv_show_dir_path(tv_show_id)}/" \
               f"{self.get_tv_show_season_dir_name(tv_show_id, tv_show_season_id)}"

    def get_tv_show_season_show_dir_list(self, tv_show_id, tv_show_season_id):
        return get_dir_list(self.get_tv_show_season_dir_path(tv_show_id, tv_show_season_id))

    def get_tv_show_season_show_name(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        if self.valid_tv_show_season_episode_id(tv_show_id, tv_show_season_id, tv_show_season_episode_id):
            return self.get_tv_show_season_show_dir_list(tv_show_id, tv_show_season_id)[tv_show_season_episode_id]

    def get_tv_show_season_episode_path(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        return self.get_tv_show_season_dir_path(tv_show_id, tv_show_season_id) + \
               self.get_tv_show_season_show_name(tv_show_id, tv_show_season_id, tv_show_season_episode_id)

    def get_tv_show_season_episode_url(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        return f"{SERVER_URL_TV_SHOWS}" \
               f"{self.get_tv_show_dir_name(tv_show_id)}/" \
               f"{self.get_tv_show_season_dir_name(tv_show_id, tv_show_season_id)}/" \
               f"{self.get_tv_show_season_show_name(tv_show_id, tv_show_season_id, tv_show_season_episode_id)}"

    def valid_tv_show_id(self, tv_show_id):
        return -1 < tv_show_id < len(self.get_tv_show_dir_list())

    def valid_tv_show_season_id(self, tv_show_id, tv_show_season_id):
        return self.valid_tv_show_id(tv_show_id) \
            and (-1 < tv_show_season_id < len(self.get_tv_show_season_dir_list(tv_show_id)))

    def valid_tv_show_season_episode_id(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        return self.valid_tv_show_season_id(tv_show_id, tv_show_season_id) and (
                    -1 < tv_show_season_episode_id < len(self.get_tv_show_season_show_dir_list(tv_show_id,
                                                                                               tv_show_season_id)))


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

    # def play_url(self, url):
    #     print(f"PLAYING URL {url}")
    #     self.current_url = url
    #     self.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE)
    #     self.media_controller.block_until_active()
    #     # self.interpret_enum_cmd(CommandList.CMD_PLAY)

    def play_episode(self, current_episode_info):
        self.current_episode_info = current_episode_info #EpisodeInfo(tv_show_id, tv_show_season_id, tv_show_season_episode_id)
        url = self.current_episode_info.get_url()
        print(f"PLAYING URL {url}")
        # self.current_url = url
        self.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE)
        self.media_controller.block_until_active()
        self.my_last_player_state = PlayerState.STATE_NEW_EPISODE_START
        # self.interpret_enum_cmd(CommandList.CMD_PLAY)

    def append_queue_url(self, url):
        self.cast_device.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE, enqueue=True)

    def get_url(self):
        if self.current_episode_info:
            return self.current_episode_info.get_url()
        return None

    def seek(self):
        self.media_controller.seek()

    def stop_scanner(self):
        self.initialized = False

# -------------------------------------------------------------------
    def interpret_enum_cmd(self, cmd_enum):
        print(f"PROCESSING CMD FOR {self.ID_STR}")
        if cmd := self.cmd_data_dict.get(cmd_enum):
            cmd()

# -------------------------------------------------------------------

    def update_player(self):
        if self.cast_device.media_controller:
            print(self.cast_device.media_controller.status.player_state)
        else:
            print("___________________NO MEDIA_CONTROLLER_______________")
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
                            if self.current_episode_info.increment_episode():
                                print(f"Adding next episode: {current_device_timestamp}")
                                # self.play_url(self.current_episode_info.get_url())
                                self.play_episode(self.current_episode_info)
                        # else:
                            # self.new_episode_started = False
                            # print("SENDING PAUSE")
                            # self.interpret_enum_cmd(CommandList.CMD_PAUSE)
                        print(f"LAST PLAYER STATE {self.last_state}")
                    # If we started playing, print the current media url
                    if self.player_state == "PLAYING":
                        # self.media_player_active = True
                        self.my_last_player_state = PlayerState.STATE_EPISODE_PLAYING
                        print(f"DEVICE: {self.ID_STR}, NOW PLAYING: {self.current_episode_info.get_url()}")
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
                print(self.cast_device.media_controller.status)#.get("content_id"))
                # print(self.cast_device.media_controller.status.is_active_input)
                # print(f"Play Time: {current_device_timestamp}")
                self.last_time_check = current_device_timestamp


class ChromecastHandler(threading.Thread):

    SCAN_INTERVAL = 60
    # browser = None
    connected_devices = {}
    last_scanned_devices = None
    initialized = False
    last_scan_time = 0
    browser = None

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

    def play_from_media_drive(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        current_episode_info = EpisodeInfo(tv_show_id, tv_show_season_id, tv_show_season_episode_id)
        # current_episode_url = current_episode_info.get_url()
        for key, connected_device in self.connected_devices.items():
            # connected_device.play_url(current_episode_url)
            connected_device.play_episode(current_episode_info)

        return current_episode_info.get_url()

    def send_command(self, media_device_command):
        for key, connected_device in self.connected_devices.items():
            connected_device.interpret_enum_cmd(media_device_command)

    def run(self):
        disconnect_devices = []
        while self.initialized:
            try:
                for connected_device_key in self.connected_devices:
                    my_media_device = self.connected_devices.get(connected_device_key)
                    if my_media_device:
                        my_media_device.update_player()
                    else:
                        print(f"No device found for {connected_device_key}")

                if time.time() - self.last_scan_time > self.SCAN_INTERVAL:
                    self.scan_for_chromecasts()
                    self.last_scan_time = time.time()

                time.sleep(0.1)
            except KeyboardInterrupt:
                break

    def get_startup_sha(self):
        global startup_sha
        return startup_sha


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


# if __name__ == "__main__":
#
#     selected_tv_show_id = TV_SHOW_ID
#     selected_tv_show_season_id = TV_SHOW_SEASON_ID + TV_SHOW_SEASON_ID_OFFSET
#     selected_tv_show_season_episode_id = TV_SHOW_SEASON_EPISODE_ID + TV_SHOW_SEASON_EPISODE_ID_OFFSET
#
#     url_builder = MediaURLBuilder()
#
#     tv_show_str = url_builder.get_tv_show_dir_name(selected_tv_show_id)
#     tv_show_season_str = url_builder.get_tv_show_season_dir_name(selected_tv_show_id, selected_tv_show_season_id)
#     tv_show_season_episode_str = url_builder.get_tv_show_season_show_name(selected_tv_show_id,
#                                                                           selected_tv_show_season_id,
#                                                                           selected_tv_show_season_episode_id)
#
#     print(tv_show_str)
#     print(tv_show_season_str)
#     print(tv_show_season_episode_str)
#
#     selected_episode_url = url_builder.get_tv_show_season_episode_url(selected_tv_show_id, selected_tv_show_season_id,
#                                                                       selected_tv_show_season_episode_id)
#
#     print(selected_episode_url)
#
#     chromecast_handler = ChromecastHandler()
#     chromecast_handler.start()
#
#     mc = chromecast_handler.connect_to_chromecast(CHROMECAST_DEVICE_LIVING_ROOM_STR)
#
#     mc.play_url(selected_episode_url)
#
#     thread1 = MyThread("Input_Handler", 1)
#     thread1.start()
#
#     while True:
#         try:
#             if thread1.new_user_input():
#                 mc.interpret_char_cmd(thread1.get_user_input())
#             time.sleep(0.1)
#         except KeyboardInterrupt:
#             break
#
#     thread1.stop()
#     mc.stop_scanner()
#
#     print("PROGRAM END")
