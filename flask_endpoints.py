from enum import Enum
import traceback
from flask import Flask, request, render_template

import config_file_handler
# jsonify, redirect, current_app, render_template
from backend_handler import BackEndHandler
from chromecast_handler import CommandList
from database_handler.database_handler import DatabaseHandler, ContentType
from database_handler.create_database import DBCreator


# TODO: Add to DB: Add media title from ffmpeg extraction
# TODO: Add to DB: Track if media was previously watched
# TODO: Update DB: Remove media that no longer exists
# TODO: Update DB: Use md5sum to track files
# TODO: Update media grid to dynamically update rather than page reload
# TODO: Extract default values to json config file <- in progress
# TODO: Update all js function references to eventlisteneres on js side
# TODO: Add notification when media scan completes
# TODO: Update chromecast menu auto populate to remove missing chromecasts
# TODO: Convert chromecast name strings to id values and use ID values to refer to chromecasts

class APIEndpoints(Enum):
    MAIN = "/"
    GET_CHROMECAST_CONTROLS = "/get_chromecast_controls"
    GET_MEDIA_CONTENT_TYPES = "/get_media_content_types"
    SET_CURRENT_MEDIA_RUNTIME = "/set_current_media_runtime"
    GET_CURRENT_MEDIA_RUNTIME = "/get_current_media_runtime"
    CONNECT_CHROMECAST = "/connect_chromecast"
    GET_CHROMECAST_LIST = "/get_chromecast_list"
    DISCONNECT_CHROMECAST = "/disconnect_chromecast"
    CHROMECAST_COMMAND = "/chromecast_command"
    PLAY_MEDIA = "/play_media"
    SCAN_MEDIA_DIRECTORIES = "/scan_media_directories"
    GET_MEDIA_MENU_DATA = "/get_media_menu_data"


app = Flask(__name__)
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

media_controller_button_dict = {
    "rewind": {"icon": "fa-backward", "id": f"{CommandList.CMD_REWIND.name}_media_button"},
    "rewind_15": {"icon": "fa-rotate-left", "id": f"{CommandList.CMD_REWIND_15.name}_media_button"},
    "play": {"icon": "fa-play", "id": f"{CommandList.CMD_PLAY.name}_media_button"},
    "pause": {"icon": "fa-pause", "id": f"{CommandList.CMD_PAUSE.name}_media_button"},
    "skip_15": {"icon": "fa-rotate-right", "id": f"{CommandList.CMD_SKIP_15.name}_media_button"},
    "skip": {"icon": "fa-forward", "id": f"{CommandList.CMD_SKIP.name}_media_button"},
    "stop": {"icon": "fa-stop", "id": f"{CommandList.CMD_STOP.name}_media_button"}
}

backend_handler = BackEndHandler()
backend_handler.start()

if db_creator := DBCreator():
    for media_folder_info in config_file_handler.load_js_file():
        db_creator.setup_media_directory(media_folder_info)


def build_main_content(request_args):
    media_metadata = {}
    content_id = None
    content_type = ContentType.TV.value
    content_id_str = request_args.get('media_id', None)
    content_type_value = request_args.get("content_type", None)
    if content_type_value:
        try:
            content_type = int(content_type_value)
        except Exception as e:
            print(e)
            print("Content_type error")
    if content_id_str:
        try:
            content_id = int(content_id_str)
        except ValueError as e:
            print(e)

    try:
        if db_handler := DatabaseHandler():
            media_metadata = db_handler.get_media_content(content_type, content_id)
        return render_template("index.html", homepage_url="/", sha=backend_handler.get_startup_sha(),
                               button_dict=media_controller_button_dict, media_metadata=media_metadata)
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
        return str(traceback.print_exc())


@app.route(APIEndpoints.MAIN.value)
def main_index():
    return build_main_content(request.args)


@app.route(APIEndpoints.GET_MEDIA_CONTENT_TYPES.value, methods=['GET'])
def get_media_content_types():
    data = {i.name: i.value for i in ContentType}
    return data, 200


@app.route(APIEndpoints.GET_CHROMECAST_CONTROLS.value, methods=['GET'])
def get_chromecast_controls():
    data = {"chromecast_controls": {i.name: i.value for i in CommandList}}
    return data, 200


@app.route(APIEndpoints.SET_CURRENT_MEDIA_RUNTIME.value, methods=['POST'])
def set_current_media_runtime():
    data = {}
    if json_request := request.get_json():
        if new_media_time := json_request.get("new_media_time"):
            backend_handler.seek_media_time(new_media_time)
    return data, 200


@app.route(APIEndpoints.GET_CURRENT_MEDIA_RUNTIME.value, methods=['GET'])
def get_current_media_runtime():
    data = {}
    if media_metadata := backend_handler.get_chromecast_media_controller_metadata():
        data = media_metadata
    return data, 200


@app.route(APIEndpoints.CONNECT_CHROMECAST.value, methods=['POST'])
def connect_chromecast():
    data = {}
    if json_request := request.get_json():
        if chromecast_id := json_request.get("chromecast_id"):
            if backend_handler.connect_chromecast(chromecast_id):
                data = {'chromecast_id': chromecast_id}
    return data, 200


@app.route(APIEndpoints.GET_CHROMECAST_LIST.value, methods=['POST'])
def get_chromecast_list():
    data = {
        "scanned_devices": backend_handler.get_chromecast_scan_list(),
        "connected_device": backend_handler.get_chromecast_device_id()
    }
    return data, 200


@app.route(APIEndpoints.DISCONNECT_CHROMECAST.value, methods=['POST'])
def disconnect_chromecast():
    data = {}
    backend_handler.disconnect_chromecast()
    return data, 200


@app.route(APIEndpoints.CHROMECAST_COMMAND.value, methods=['POST'])
def chromecast_command():
    data = {}
    if json_request := request.get_json():
        if chromecast_cmd_id := json_request.get("chromecast_cmd_id"):
            backend_handler.send_chromecast_cmd(CommandList(chromecast_cmd_id))
    return data, 200


@app.route(APIEndpoints.PLAY_MEDIA.value, methods=['POST'])
def play_media():
    data = {}
    if json_request := request.get_json():
        if media_id := json_request.get("media_id", 0):
            playlist_id = json_request.get("playlist_id", None)
            backend_handler.play_media_on_chromecast(media_id, playlist_id)
    return data, 200


@app.route(APIEndpoints.SCAN_MEDIA_DIRECTORIES.value, methods=['POST'])
def scan_media_directories():
    data = {}
    db_creator = DBCreator()
    if db_creator:
        db_creator.scan_all_media_directories()
    return data, 200


@app.route(APIEndpoints.GET_MEDIA_MENU_DATA.value, methods=['POST'])
def get_media_menu_data():
    data = {}
    db_creator = DBCreator()
    if db_creator:
        pass
    return data, 200


if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5002)
