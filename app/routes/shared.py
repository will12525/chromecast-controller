"""Shared route state: blueprints, API paths, backend singleton, helpers."""
import traceback
from enum import Enum

from flask import Blueprint, render_template

import app.utils.backend_handler as backend_handler
from app.utils.chromecast_handler import CommandList
from app.utils.common import ContentType, SystemMode
from app.utils import config_file_handler

main_bp = Blueprint("main", __name__)

# Library UX complete. Streaming: multi-cast sessions + unified Local/Cast controls.

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4"}


class APIEndpoints(Enum):
    MAIN = "/"
    TABLE = "/table"
    QUERY_DB = "/query_db"
    EDITOR = "/editor"
    EDITOR_VALIDATE_TXT_FILE = "/validate_txt_file"
    EDITOR_SAVE_TXT_FILE = "/save_txt_file"
    EDITOR_LOAD_TXT_FILE = "/load_txt_file"
    EDITOR_PROCESS_TXT_FILE = "/process_txt_file"
    DELETE_TXT_FILE = "/delete_txt_file"
    EDITOR_PROCESSOR_METADATA = "/process_metadata"
    GET_CHROMECAST_CONTROLS = "/get_chromecast_controls"
    GET_MEDIA_CONTENT_TYPES = "/get_media_content_types"
    SET_CURRENT_MEDIA_RUNTIME = "/set_current_media_runtime"
    GET_CURRENT_MEDIA_RUNTIME = "/get_current_media_runtime"
    CONNECT_CHROMECAST = "/connect_chromecast"
    GET_CHROMECAST_LIST = "/get_chromecast_list"
    DISCONNECT_CHROMECAST = "/disconnect_chromecast"
    SET_STREAM_MODE = "/set_stream_mode"
    CHROMECAST_COMMAND = "/chromecast_command"
    PLAY_MEDIA = "/play_media"
    GET_NEXT_MEDIA = "/get_next_media"
    SCAN_MEDIA_DIRECTORIES = "/scan_media_directories"
    GET_MEDIA_MENU_DATA = "/get_media_menu_data"
    GET_DISK_SPACE = "/get_disk_space"
    UPDATE_MEDIA_METADATA = "/update_media_metadata"
    MEDIA_UPLOAD = "/media_upload"
    REQUEST_ALL_CONTENT = "/request_all_content"
    REQUEST_IMAGE = "/request_image"
    SERVER_CONNECT = "/server_connect"
    REQUEST_CONTENT = "/request_content"
    LIBRARY_HOME = "/library/home"
    PLAYBACK_PROGRESS = "/playback_progress"
    CONNECT_LOCAL_PLAYER = "/connect_local_player"
    SCAN_STATUS = "/scan_status"


media_controller_button_dict = {
    "rewind": {"icon": "bi-rewind-fill", "id": f"{CommandList.CMD_REWIND.name}_media_button"},
    "rewind_15": {"icon": "bi-rewind-circle", "id": f"{CommandList.CMD_REWIND_15.name}_media_button"},
    "play": {"icon": "bi-play-fill", "id": f"{CommandList.CMD_PLAY.name}_media_button"},
    "pause": {"icon": "bi-pause-fill", "id": f"{CommandList.CMD_PAUSE.name}_media_button"},
    "skip_15": {"icon": "bi-fast-forward-circle", "id": f"{CommandList.CMD_SKIP_15.name}_media_button"},
    "skip": {"icon": "bi-fast-forward-fill", "id": f"{CommandList.CMD_SKIP.name}_media_button"},
    "stop": {"icon": "bi-stop-fill", "id": f"{CommandList.CMD_STOP.name}_media_button"},
}

media_types = [
    ContentType.RAW.name,
    ContentType.TV.name,
    ContentType.MOVIE.name,
    ContentType.BOOK.name,
]

system_mode = SystemMode.CLIENT
if config_file_handler.load_json_file_content().get("mode") == SystemMode.SERVER.name:
    system_mode = SystemMode.SERVER

# Single backend singleton for the process (cast thread, scan flag, editor jobs)
bh = backend_handler.BackEndHandler()
bh.start()


def build_main_content():
    try:
        return render_template(
            "index.html",
            homepage_url=APIEndpoints.MAIN.value,
            button_dict=media_controller_button_dict,
            system_mode=system_mode.name,
        )
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
        return str(traceback.print_exc())


def play_response_from_metadata(media_metadata, json_request, data):
    """Populate play API response including resume fields."""
    if not media_metadata:
        return data
    data["id"] = media_metadata.get("id")
    data["parent_container_id"] = json_request.get("parent_container_id")
    data["local_play_url"] = media_metadata.get("url")
    data["content_title"] = media_metadata.get("content_title")
    data["tag_list"] = json_request.get("tag_list")
    data["last_position"] = media_metadata.get("last_position") or 0
    data["last_duration"] = media_metadata.get("last_duration") or 0
    return data


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
