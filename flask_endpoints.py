import json
import pathlib
import queue

from enum import Enum
import traceback
from flask import Flask, request, render_template

# jsonify, redirect, current_app, render_template
import backend_handler as bh
import config_file_handler
from chromecast_handler import CommandList
from database_handler import common_objects
from database_handler.database_handler import DatabaseHandler
from database_handler.common_objects import ContentType, MEDIA_DIRECTORY_PATH_COLUMN
from database_handler.create_database import DBCreator
from werkzeug.utils import secure_filename


# TODO: Update media grid to dynamically update rather than page reload
# TODO: Update all js function references to event listeners on js side
# TODO: Add monitoring of storage space
# TODO: Prevent media additions if space is low
# TODO: Add notification when media scan completes
# TODO: Prevent additional scans from occurring while scan in progress
# TODO: Update chromecast menu auto populate to remove missing chromecasts
# TODO: Convert chromecast name strings to id values and use ID values to refer to chromecasts
# TODO: Make local media player: https://www.tutorialspoint.com/opencv_python/opencv_python_play_video_file.htm


class APIEndpoints(Enum):
    MAIN = "/"
    EDITOR = "/editor"
    EDITOR_VALIDATE_TXT_FILE = "/validate_txt_file"
    EDITOR_SAVE_TXT_FILE = "/save_txt_file"
    EDITOR_LOAD_TXT_FILE = "/load_txt_file"
    EDITOR_PROCESS_TXT_FILE = "/process_txt_file"
    EDITOR_PROCESSOR_METADATA = "/process_metadata"
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
    GET_DISK_SPACE = "/get_disk_space"
    UPDATE_MEDIA_METADATA = "/update_media_metadata"
    MEDIA_UPLOAD = "/media_upload"


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', "mp4"}

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
media_types = {
    ContentType.TV.name: ContentType.TV.value,
    ContentType.MOVIE.name: ContentType.MOVIE.value
}

backend_handler = bh.BackEndHandler()
setup_thread = backend_handler.start()

error_log = queue.Queue()

raw_folder = config_file_handler.load_js_file().get('editor_raw_folder')
raw_folder_url = config_file_handler.load_js_file().get('editor_raw_url')


def build_main_content(request_args):
    content_type = request_args.get(key="content_type", default=ContentType.TV.value, type=int)
    content_id = request_args.get(key=common_objects.MEDIA_ID_COLUMN, default=None, type=int)
    # When run using flask, the default type of ContentType isn't applied
    if len(ContentType) > content_type:
        content_type = ContentType(content_type)

    data = {}
    if content_type == ContentType.TV_SHOW:
        data[common_objects.TV_SHOW_ID_COLUMN] = content_id
    elif content_type == ContentType.SEASON:
        data[common_objects.SEASON_ID_COLUMN] = content_id
    else:
        pass

    system_data = backend_handler.get_system_data()

    try:
        with DatabaseHandler() as db_connection:
            media_metadata = db_connection.get_media_content(content_type, params_dict=data)
        return render_template("index.html", homepage_url=APIEndpoints.MAIN.value,
                               button_dict=media_controller_button_dict, media_metadata=media_metadata,
                               system_data=system_data)
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
        return str(traceback.print_exc())


@app.route(APIEndpoints.EDITOR.value)
def editor():
    try:
        return render_template("editor.html",
                               homepage_url="/",
                               button_dict=media_controller_button_dict,
                               editor_metadata=backend_handler.get_editor_metadata(raw_folder),
                               media_types=media_types)
    except Exception as e:
        error_str = str(traceback.print_exc())
        if len(e.args) > 0:
            data = {"error": e.args[0]}
            error_str = f"{error_str}\n{data}"
            print(data)
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
        return str(error_str)


@app.route(APIEndpoints.EDITOR_VALIDATE_TXT_FILE.value, methods=['POST'])
def editor_validate_txt_file():
    data = {"error": {"message": "File valid"}}
    if json_request := request.get_json():
        if json_request.get("txt_file_media_type"):
            json_request["media_type"] = media_types.get(json_request.get("txt_file_media_type"))
        try:
            errors = bh.editor_validate_txt_file(raw_folder, json_request)
            if errors:
                data = {"process_log": errors}
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
            print(json.dumps(json_request, indent=4))
    return data, 200


@app.route(APIEndpoints.EDITOR_SAVE_TXT_FILE.value, methods=['POST'])
def editor_save_txt_file():
    data = {"error": {"message": "File saved"}}
    if json_request := request.get_json():
        try:
            bh.editor_save_txt_file(raw_folder, json_request)
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
            print(json.dumps(json_request, indent=4))
    return data, 200


@app.route(APIEndpoints.EDITOR_LOAD_TXT_FILE.value, methods=['POST'])
def editor_load_txt_file():
    data = {}
    if json_request := request.get_json():
        if editor_txt_file_name := json_request.get("editor_txt_file_name"):
            try:
                data = backend_handler.get_editor_metadata(raw_folder, selected_txt_file=editor_txt_file_name,
                                                           raw_url=raw_folder_url)
            except Exception as e:
                print("Exception class: ", e.__class__)
                print(f"ERROR: {e}")
                print(traceback.print_exc())
                print(json.dumps(json_request, indent=4))
    return data, 200


@app.route(APIEndpoints.EDITOR_PROCESS_TXT_FILE.value, methods=['POST'])
def editor_process_txt_file():
    data = {}
    if json_request := request.get_json():
        if json_request.get("txt_file_media_type"):
            json_request["media_type"] = media_types.get(json_request.get("txt_file_media_type"))
            try:
                with DatabaseHandler() as db_connection:
                    media_metadata = db_connection.get_media_folder_path_from_type(json_request["media_type"])
                output_path = pathlib.Path(media_metadata.get(MEDIA_DIRECTORY_PATH_COLUMN)).resolve()
                errors = backend_handler.editor_process_txt_file(raw_folder, json_request, output_path)
                data = backend_handler.editor_get_process_metadata()
                data["process_log"].extend(errors)
                if not errors:
                    data["process_log"].append({"message": "Success!"})
            except Exception as e:
                print("Exception class: ", e.__class__)
                print(f"ERROR: {e}")
                print(traceback.print_exc())
                print(json.dumps(json_request, indent=4))
    print(json.dumps(data, indent=4))
    return data, 200


@app.route(APIEndpoints.EDITOR_PROCESSOR_METADATA.value, methods=['GET'])
def editor_processor_get_metadata():
    data = {}
    try:
        data = backend_handler.editor_get_process_metadata()
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
    return data, 200


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
        if json_request.get(common_objects.MEDIA_ID_COLUMN, None):
            if not backend_handler.play_media_on_chromecast(json_request):
                with DatabaseHandler() as db_connection:
                    media_info = db_connection.get_media_content(content_type=ContentType.MEDIA,
                                                                 params_dict=json_request)
                data[
                    "local_play_url"] = f"{media_info.get(common_objects.MEDIA_DIRECTORY_URL_COLUMN)}{media_info.get(common_objects.PATH_COLUMN)}"
        else:
            print(f"Media ID not provided: {json_request}")
    return data, 200


@app.route(APIEndpoints.SCAN_MEDIA_DIRECTORIES.value, methods=['POST'])
def scan_media_directories():
    data = {}
    backend_handler.scan_media_directories()
    return data, 200


@app.route(APIEndpoints.UPDATE_MEDIA_METADATA.value, methods=['POST'])
def update_media_metadata():
    data = {}
    # If exception, pass to error log
    if json_request := request.get_json():
        if json_request.get(common_objects.IMAGE_URL):
            try:
                bh.download_image(json_request)
            except ValueError as e:
                if len(e.args) > 0:
                    data = {"error": e.args[0]}
                    print(data)
            print(f"{common_objects.IMAGE_URL}: {json_request.get(common_objects.IMAGE_URL)}")
        with DatabaseHandler() as db_connection:
            db_connection.update_media_metadata(json_request)
    return data, 200


@app.route(APIEndpoints.GET_MEDIA_MENU_DATA.value, methods=['POST'])
def get_media_menu_data():
    data = {}
    print(f"Not implemented: {APIEndpoints.GET_MEDIA_MENU_DATA.value}")
    return data, 200


@app.route(APIEndpoints.GET_DISK_SPACE.value, methods=['GET'])
def get_disk_space():
    try:
        data = {"free_space": bh.get_free_disk_space(raw_folder)}
        return data, 200
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route(APIEndpoints.MEDIA_UPLOAD.value, methods=['GET', 'POST'])
def upload_file():
    data = {}
    if request.method == 'POST':
        print(request.files)
        # check if the post request has the file part
        if 'file' not in request.files:
            data["message"] = "No file provided"
            return data, 200
        file = request.files['file']
        if file.filename == '':
            data["message"] = "No selected file"
            data["filename"] = f"{file.filename}"
            return data, 200
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename).replace('_', ' ')
            try:
                output_path = bh.build_tv_show_output_path(filename)
                print(output_path)
                file.save(output_path)
                data["message"] = "File saved"
            except (ValueError, FileExistsError) as e:
                data["error"] = e.args[0]
    print(data)
    return data, 200


if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5002)
