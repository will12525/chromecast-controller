import logging
import threading
import time
import os
from enum import Enum, auto
from database_handler.database_handler import DatabaseHandler

import pychromecast


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


class MyMediaDevice:
    DEFAULT_MEDIA_TYPE = "video/mp4"
    cmd_data_dict = {}

    status = None

    def __init__(self, media_controller):
        self.media_controller = media_controller

        self.cmd_data_dict[CommandList.CMD_REWIND] = self.rewind
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

    def play_episode_from_sql(self, media_id, playlist_id=None):
        db_handler = DatabaseHandler()
        if db_handler:
            media_info = db_handler.get_media_metadata(media_id)
            if playlist_id:
                media_info["user_selected_playlist_id"] = playlist_id
            if media_info:
                self.play_media_info(media_info)

    def play_increment_episode(self, db_function):
        if self.status:
            if media_metadata := self.status.media_metadata:
                if playlist_id := media_metadata.get("user_selected_playlist_id",
                                                     media_metadata.get("playlist_id", None)):
                    if media_info := db_function(media_metadata.get("id"), playlist_id):
                        self.play_media_info(media_info)

    def play_next_episode(self):
        if db_handler := DatabaseHandler():
            self.play_increment_episode(db_handler.get_next_media_metadata)

    def play_previous_episode(self):
        if db_handler := DatabaseHandler():
            self.play_increment_episode(db_handler.get_previous_media_metadata)

    def play_media_info(self, media_info=None):
        if media_info:
            media_url = f"{media_info.get('media_folder_url')}{media_info.get('path')}"
            media_title = media_info.get('title')
            if season_title := media_info.get('season_title'):
                media_title = f"{season_title} {media_title}"
            if tv_show_title := media_info.get('tv_show_title'):
                media_title = f"{tv_show_title} {media_title}"

            self.media_controller.play_media(media_url, self.DEFAULT_MEDIA_TYPE, title=media_title, metadata=media_info)
            self.media_controller.block_until_active()

    def get_media_controller_metadata(self):
        if self.status:
            return {
                "media_runtime": self.status.adjusted_current_time,
                "media_duration": self.status.duration,
                "media_title": self.status.title
            }

    def append_queue_url(self, url):
        pass
        # self.media_controller.play_media(url, self.DEFAULT_MEDIA_TYPE, enqueue=True)

    def seek(self, position):
        self.media_controller.seek(position)

    def interpret_enum_cmd(self, cmd_enum):
        if cmd := self.cmd_data_dict.get(cmd_enum):
            cmd()

    def rewind(self):
        if self.status and self.status.adjusted_current_time <= 30:
            self.play_previous_episode()
        else:
            self.media_controller.rewind()

    def rewind_15(self):
        if self.status:
            self.seek(self.status.adjusted_current_time - 15)

    def skip_15(self):
        if self.status:
            self.seek(self.status.adjusted_current_time + 15)

    def new_media_status(self, status):
        self.status = status

        if self.media_controller.status.player_state == "IDLE" and self.media_controller.status.idle_reason == "FINISHED":
            self.play_next_episode()


class ChromecastHandler(threading.Thread):
    SCAN_INTERVAL = 10

    chromecast_device = None
    chromecast_browser = None
    media_controller = None

    last_scanned_devices = []
    last_scan_time = 0

    run_update = False

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        logging.basicConfig(filename='status_change.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',
                            level=logging.DEBUG)

    def __del__(self):
        self.run_update = False
        self.disconnect_chromecast()
        if self.chromecast_browser:
            self.chromecast_browser.stop_discovery()

    def get_scan_list(self):
        return self.last_scanned_devices

    def scan_for_chromecasts(self):
        services, browser = pychromecast.discovery.discover_chromecasts()
        if not self.chromecast_browser:
            self.chromecast_browser = browser
        else:
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
                if not self.chromecast_browser:
                    self.chromecast_browser = browser
                return True
        return False

    def disconnect_chromecast(self):
        self.chromecast_device = None
        self.media_controller = None

    def get_media_controller(self) -> MyMediaDevice:
        return self.media_controller

    def get_media_controller_metadata(self):
        if self.media_controller:
            return self.media_controller.get_media_controller_metadata()

    def get_chromecast_id(self) -> str:
        if self.chromecast_device:
            return self.chromecast_device.name

    def seek_media_time(self, media_time):
        if self.media_controller:
            self.media_controller.seek(media_time)

    def play_from_sql(self, media_id, playlist_id=None):
        if self.media_controller:
            self.media_controller.play_episode_from_sql(media_id, playlist_id)

    def send_command(self, media_device_command):
        if self.media_controller:
            self.media_controller.interpret_enum_cmd(media_device_command)

    def check_chromecast_alive(self):
        if self.chromecast_device:
            device_ip = self.chromecast_device.socket_client.host
            response = os.system(f"ping -c 1 -w2 {device_ip} > /dev/null 2>&1")
            if 0 != response:
                self.disconnect_chromecast()

    def run(self):
        self.run_update = True
        self.scan_for_chromecasts()
        while self.run_update:
            try:
                if time.time() - self.last_scan_time > self.SCAN_INTERVAL:
                    self.check_chromecast_alive()
                    self.scan_for_chromecasts()
                    self.last_scan_time = time.time()

                time.sleep(0.1)
            except KeyboardInterrupt:
                break
