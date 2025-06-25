import logging
import threading
import time
import os
from enum import Enum, auto
import pychromecast

from app.database.db_getter import DBHandler


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

    def play_episode_from_sql(self, content_data):
        db_connection = DBHandler()
        db_connection.open()
        media_metadata = db_connection.get_content_info(content_data.get("content_id"))
        db_connection.close()

        media_metadata["parent_container_id"] = content_data["parent_container_id"]

        if media_metadata:
            self.play_media_info(media_metadata)
            return media_metadata

    def play_random_container_content(self, json_request):
        db_connection = DBHandler()
        db_connection.open()
        media_metadata = db_connection.get_random_content_in_container(json_request)
        db_connection.close()

        if media_metadata:
            self.play_media_info(media_metadata)
            return media_metadata

    def play_next_episode(self):
        media_info = None
        if self.status and (media_metadata := self.status.media_metadata):
            current_media_data = {"content_id": media_metadata.get("id"),
                                  "parent_container_id": media_metadata.get("parent_container_id")}
            db_connection = DBHandler()
            db_connection.open()
            media_info = db_connection.get_next_content_in_container(current_media_data)
            db_connection.close()

        if media_info:
            self.play_media_info(media_info)
            return media_info

    def play_previous_episode(self):
        media_info = None
        if self.status and (media_metadata := self.status.media_metadata):
            current_media_data = {"content_id": media_metadata.get("id"),
                                  "parent_container_id": media_metadata.get("parent_container_id")}
            db_connection = DBHandler()
            db_connection.open()
            media_info = db_connection.get_previous_content_in_container(current_media_data)
            db_connection.close()

        if media_info:
            self.play_media_info(media_info)
            return media_info

    def play_media_info(self, media_metadata):
        if media_metadata:
            self.media_controller.play_media(media_metadata.get("url"), self.DEFAULT_MEDIA_TYPE,
                                             title=media_metadata.get("content_src"),
                                             metadata=media_metadata)
            self.media_controller.block_until_active()

            db_connection = DBHandler()
            db_connection.open()
            db_connection.update_content_play_count(media_metadata.get("id"))
            db_connection.close()

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

    def play_from_sql(self, content_data):
        if self.media_controller:
            self.media_controller.play_episode_from_sql(content_data)
            return True
        return False

    def play_random_container_content(self, json_request):
        if self.media_controller:
            return self.media_controller.play_random_container_content(json_request)

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
