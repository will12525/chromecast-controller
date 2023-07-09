import time
import pychromecast
import os
import traceback
import threading
from pychromecast.controllers.receiver import CastStatus
from enum import Enum

# ssh into server
# CAST MEDIA
# cd /home/willow/workspace/cast_media_server
# python3 main.py

# START SERVER
# cd /media/hdd1/plex_media
#./start_chromacst_video_access_server

# UPDATE main.py WITH THIS FILE
# scp main.py willow@192.168.1.200:/home/willow/workspace/cast_media_server/

# View live journal
# sudo journalctl -u media_folder_python.service -f

# SCP the files
# scp -r templates/ main.py flask_main.py willow@192.168.1.200:/home/willow/workspace/chromecast_flask_app

# systemctl
#  sudo systemctl status media_folder_python.service
#  sudo systemctl start media_folder_python.service

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


# tv_show_dir_path = "/media/hdd1/plex_media/tv_shows/"
# unsorted_tv_shows_dir_path_list = os.listdir(tv_show_dir_path)
# tv_shows_dir_path_list = sorted(unsorted_tv_shows_dir_path_list)
# print(f"Sorted list len: {len(tv_shows_dir_path_list)}, list: {tv_shows_dir_path_list}")

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
        return self.media_url_builder.get_tv_show_season_episode_url(self.tv_show_id, self.tv_show_season_id, self.tv_show_season_episode_id)

    def increment_episode(self):
        new_tv_show_season_id = self.tv_show_season_id + 1
        new_tv_show_season_episode_id = self.tv_show_season_episode_id + 1

        if self.media_url_builder.valid_tv_show_season_episode_id(self.tv_show_id, self.tv_show_season_id, new_tv_show_season_episode_id):
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
        return f"{self.get_tv_show_dir_path(tv_show_id)}/{self.get_tv_show_season_dir_name(tv_show_id, tv_show_season_id)}"

    def get_tv_show_season_show_dir_list(self, tv_show_id, tv_show_season_id):
        return get_dir_list(self.get_tv_show_season_dir_path(tv_show_id, tv_show_season_id))

    def get_tv_show_season_show_name(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        if self.valid_tv_show_season_episode_id(tv_show_id, tv_show_season_id, tv_show_season_episode_id):
            return self.get_tv_show_season_show_dir_list(tv_show_id, tv_show_season_id)[tv_show_season_episode_id]

    def get_tv_show_season_episode_path(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        return self.get_tv_show_season_dir_path(tv_show_id, tv_show_season_id) + \
               self.get_tv_show_season_show_name(tv_show_id, tv_show_season_id, tv_show_season_episode_id)

    def get_tv_show_season_episode_url(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        return f"{SERVER_URL_TV_SHOWS}{self.get_tv_show_dir_name(tv_show_id)}/{self.get_tv_show_season_dir_name(tv_show_id, tv_show_season_id)}/{self.get_tv_show_season_show_name(tv_show_id, tv_show_season_id, tv_show_season_episode_id)}"

    def valid_tv_show_id(self, tv_show_id):
        return -1 < tv_show_id < len(self.get_tv_show_dir_list())

    def valid_tv_show_season_id(self, tv_show_id, tv_show_season_id):
        return self.valid_tv_show_id(tv_show_id) and (-1 < tv_show_season_id < len(self.get_tv_show_season_dir_list(tv_show_id)))

    def valid_tv_show_season_episode_id(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        return self.valid_tv_show_season_id(tv_show_id, tv_show_season_id) and (
                    -1 < tv_show_season_episode_id < len(self.get_tv_show_season_show_dir_list(tv_show_id, tv_show_season_id)))


class CommandList(Enum):
    CMD_DEVICE_WAIT = 0
    CMD_PLAY = 1
    CMD_PAUSE = 2
    CMD_STOP = 3
    CMD_RESTART = 4
    CMD_SKIP = 5
    CMD_PLAY_NEXT = 6
    CMD_PLAY_PREV = 7

# class MyMediaDevice(threading.Thread):
class MyMediaDevice:


    DEFAULT_MEDIA_TYPE = "video/mp4"
    media_start_time = None
    player_state = None
    initialized = False
    current_url = ""
    current_media = None
    last_time_check = 0
    last_state = None

# New Stuff


    cmd_data_dict = {}
    ID_STR = ""

    def __init__(self, cast_device_id_str, cast_device):
        # threading.Thread.__init__(self)
        self.ID_STR = cast_device_id_str
        self.cast_device = cast_device
        self.media_controller = cast_device.media_controller
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
        # self.browser.stop_discovery()

    def play_url(self, url):
        print(f"PLAYING URL {url}")
        self.current_url = url
        self.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE)
        self.media_controller.block_until_active()
        self.interpret_enum_cmd(CommandList.CMD_PLAY)

    def play_media_drive(self, current_media):
        # self.current_media = EpisodeInfo(tv_show_id, tv_show_season_id, tv_show_season_episode_id)
        self.current_media = current_media
        self.play_url(current_media.get_url())

    # def play_media_drive_id(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
    #     current_media = EpisodeInfo(tv_show_id, tv_show_season_id, tv_show_season_episode_id)
    #     # self.current_media = current_media
    #     self.play_url(current_media.get_url())

    # def enqueue_media_drive(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
    #     self.current_media = EpisodeInfo(tv_show_id, tv_show_season_id, tv_show_season_episode_id)
    #     self.append_queue_url(self.current_media.get_url())

    def append_queue_url(self, url):
        self.cast_device.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE, enqueue=True)

    def get_url(self):
        if self.current_media:
            return self.current_media.get_url()
        return self.current_url

    def seek(self):
        self.media_controller.seek()

    def stop_scanner(self):
        self.initialized = False

# -------------------------------------------------------------------
    def interpret_enum_cmd(self, cmd_enum):
        if cmd := self.cmd_data_dict.get(cmd_enum):
            cmd()

# -------------------------------------------------------------------

    def interpret_char_cmd(self, user_input: int):
        print(f"Provided input: {user_input}")
        #
        # if user_input == 1:
        #     self.device_wait()
        # elif user_input == 2:
        #     pass
        #     # self.play_url(
        #     #     SERVER_URL_TV_SHOWS + url_builder.get_tv_show_season_episode_url(selected_tv_show_id,
        #     #                                                                      selected_tv_show_season_id,
        #     #                                                                      selected_tv_show_season_episode_id))
        # elif user_input == 3:
        #     self.play()
        # elif user_input == 4:
        #     self.pause()
        # elif user_input == 5:
        #     self.stop()
        # elif user_input == 6:
        #     self.interpret_enum_cmd(self.CommandList.CMD_RESTART)
        # elif user_input == 7:
        #     self.skip()
        # elif user_input == 8:
        #     self.seek()
        # elif user_input == 9:
        #     self.interpret_enum_cmd(self.CommandList.CMD_PLAY_NEXT)
        # elif user_input == 10:
        #     self.interpret_enum_cmd(self.CommandList.CMD_PLAY_PREV)
        # elif user_input == 11:
        #     self.block_until_active()
        # elif user_input == 12:
        #     self.interpret_enum_cmd(self.CommandList.CMD_PLAY_NEXT)

    def update_player(self):
        if self.initialized and self.cast_device and self.cast_device.media_controller:
            current_device_timestamp = self.cast_device.media_controller.status.adjusted_current_time
            # Check if the player state changed
            if self.player_state != self.cast_device.media_controller.status.player_state:
                self.player_state = self.cast_device.media_controller.status.player_state
                if not self.last_state:
                    self.last_state = self.player_state
                print("NEW PLAYER STATE:", self.player_state)

                # If we have a media object than we can auto increment to the next episode
                if self.current_media:
                    # If we went into IDLE after playing
                    if self.player_state == "IDLE" and self.last_state != "PAUSED":
                        if self.current_media.increment_episode():
                            print(f"Adding next episode: {current_device_timestamp}")
                            self.play_url(self.current_media.get_url())
                    # If we started playing, print the current media url
                    if self.player_state == "PLAYING":
                        print(f"NOW PLAYING: {self.current_media.get_url()}")

                self.last_state = self.player_state
            # Update every 5 seconds
            if current_device_timestamp - self.last_time_check > 5:
                # print(self.cast_device.media_controller)
                # print(self.cast_device.media_controller.status.season)
                print(self.cast_device.media_controller.status)
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

    def __init__(self):
        threading.Thread.__init__(self)
        self.initialized = True

    def __del__(self):
        print("deleting ChromecastHandler")
        self.initialized = False
        if self.browser:
            self.browser.stop_discovery()

    def get_scan_list(self):
        return self.last_scanned_devices

    def scan_for_chromecasts(self) -> [str]:
        services, browser = pychromecast.discovery.discover_chromecasts()
        pychromecast.discovery.stop_discovery(browser)
        for service in services:
            print(type(service))
            print(service)
            print(service)

        self.last_scanned_devices = [getattr(service, "friendly_name") for service in services]
        return self.last_scanned_devices

    def connect_to_chromecast(self, chromecast_id_str) -> MyMediaDevice:
        chromecasts, new_browser = pychromecast.get_listed_chromecasts(friendly_names=[chromecast_id_str])
        # if not self.browser:
        self.browser = new_browser

        if len(chromecasts) > 0:
            chromecast = chromecasts[0]
            if getattr(chromecast.cast_info, "friendly_name") == chromecast_id_str:
                self.connected_devices[chromecast_id_str] = MyMediaDevice(chromecast_id_str, chromecast)

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
        current_media = EpisodeInfo(tv_show_id, tv_show_season_id, tv_show_season_episode_id)
        for key, connected_device in self.connected_devices.items():
            connected_device.play_media_drive(current_media)

        return current_media.get_url()

    def send_command(self, media_device_command):
        for key, connected_device in self.connected_devices.items():
            connected_device.interpret_enum_cmd(media_device_command)

    def run(self):
        while self.initialized:
            try:
                for connected_device in self.connected_devices:
                    self.connected_devices.get(connected_device).update_player()

                if time.time() - self.last_scan_time > self.SCAN_INTERVAL:
                    self.scan_for_chromecasts()
                    self.last_scan_time = time.time()

                time.sleep(0.1)
            except KeyboardInterrupt:
                break


# Getting user input for __main__
class MyThread(threading.Thread):

    new_input = False
    user_input = None
    check_user_input = False

    def __init__(self, thread_name, thread_ID):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.thread_ID = thread_ID
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


if __name__ == "__main__":

    selected_tv_show_id = TV_SHOW_ID
    selected_tv_show_season_id = TV_SHOW_SEASON_ID + TV_SHOW_SEASON_ID_OFFSET
    selected_tv_show_season_episode_id = TV_SHOW_SEASON_EPISODE_ID + TV_SHOW_SEASON_EPISODE_ID_OFFSET

    url_builder = MediaURLBuilder()

    tv_show_str = url_builder.get_tv_show_dir_name(selected_tv_show_id)
    tv_show_season_str = url_builder.get_tv_show_season_dir_name(selected_tv_show_id, selected_tv_show_season_id)
    tv_show_season_episode_str = url_builder.get_tv_show_season_show_name(selected_tv_show_id, selected_tv_show_season_id, selected_tv_show_season_episode_id)

    print(tv_show_str)
    print(tv_show_season_str)
    print(tv_show_season_episode_str)

    selected_episode_url = url_builder.get_tv_show_season_episode_url(selected_tv_show_id, selected_tv_show_season_id, selected_tv_show_season_episode_id)

    print(selected_episode_url)

    chromecast_handler = ChromecastHandler()
    chromecast_handler.start()

    mc = chromecast_handler.connect_to_chromecast(CHROMECAST_DEVICE_LIVING_ROOM_STR)

    mc.play_url(selected_episode_url)

    thread1 = MyThread("Input_Handler", 1)
    thread1.start()

    while True:
        try:
            if thread1.new_user_input():
                mc.interpret_char_cmd(thread1.get_user_input())
            time.sleep(0.1)
        except KeyboardInterrupt:
            break

    thread1.stop()
    mc.stop_scanner()

    print("PROGRAM END")


