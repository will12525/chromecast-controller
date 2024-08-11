import json
import queue

from enum import Enum
import traceback
from flask import Flask, request, render_template, jsonify

# jsonify, redirect, current_app, render_template
import backend_handler as bh
from chromecast_handler import CommandList
from database_handler import common_objects
from database_handler.db_getter import DatabaseHandlerV2
from database_handler.common_objects import ContentType
from werkzeug.utils import secure_filename

from database_handler.db_setter import DBCreatorV2


# TODO: Update media grid to dynamically update rather than page reload
# TODO: Update all js function references to event listeners on js side
# TODO: Add monitoring of storage space
# TODO: Prevent media additions if space is low
# TODO: Add notification when media scan completes
# TODO: Prevent additional scans from occurring while scan in progress
# TODO: Update chromecast menu auto populate to remove missing chromecasts
# TODO: Convert chromecast name strings to id values and use ID values to refer to chromecasts
# TODO: Make local media player: https://www.tutorialspoint.com/opencv_python/opencv_python_play_video_file.htm

# TODO: Add play button to all media content
# TODO: Add random play button
# TODO:

class APIEndpoints(Enum):
    MAIN = "/"
    QUERY_DB = "/query_db"
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
    "rewind": {"icon": "bi-rewind-fill", "id": f"{CommandList.CMD_REWIND.name}_media_button"},
    "rewind_15": {"icon": "bi-rewind-circle", "id": f"{CommandList.CMD_REWIND_15.name}_media_button"},
    "play": {"icon": "bi-play-fill", "id": f"{CommandList.CMD_PLAY.name}_media_button"},
    "pause": {"icon": "bi-pause-fill", "id": f"{CommandList.CMD_PAUSE.name}_media_button"},
    "skip_15": {"icon": "bi-fast-forward-circle", "id": f"{CommandList.CMD_SKIP_15.name}_media_button"},
    "skip": {"icon": "bi-fast-forward-fill", "id": f"{CommandList.CMD_SKIP.name}_media_button"},
    "stop": {"icon": "bi-stop-fill", "id": f"{CommandList.CMD_STOP.name}_media_button"}
}
media_types = {
    ContentType.TV.name: ContentType.TV.value,
    ContentType.MOVIE.name: ContentType.MOVIE.value,
    ContentType.BOOK.name: ContentType.BOOK.value
}

backend_handler = bh.BackEndHandler()
setup_thread = backend_handler.start()

error_log = queue.Queue()


def build_main_content(request_args):
    # system_data = backend_handler.get_system_data()
    with DatabaseHandlerV2() as db_getter_connection:
        tag_list = db_getter_connection.get_all_tags()

    try:
        return render_template("index.html", homepage_url=APIEndpoints.MAIN.value,
                               button_dict=media_controller_button_dict, tag_list=tag_list)
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
        return str(traceback.print_exc())


@app.route(APIEndpoints.EDITOR.value)
def editor():
    try:
        return render_template("editor.html",
                               homepage_url=APIEndpoints.MAIN.value,
                               button_dict=media_controller_button_dict,
                               editor_metadata=backend_handler.get_editor_metadata(),
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
        try:
            errors = bh.editor_validate_txt_file(json_request.get('txt_file_name'),
                                                 common_objects.ContentType[json_request.get('media_type')].value)
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
            bh.editor_save_txt_file(json_request.get('txt_file_name'), json_request.get('txt_file_content'))
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
                data = backend_handler.get_editor_metadata(selected_txt_file=editor_txt_file_name)
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
        if json_request.get("media_type"):
            try:
                errors = backend_handler.editor_process_txt_file(json_request, common_objects.ContentType[
                    json_request.get('media_type')].value)
                data = backend_handler.editor_get_process_metadata()
                if errors:
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


@app.route(APIEndpoints.QUERY_DB.value, methods=["POST"])
def query_media_db():
    media_metadata = {}
    if json_request := request.get_json():
        print(json_request)
        with DatabaseHandlerV2() as db_getter_connection:
            media_metadata.update(
                db_getter_connection.query_content(
                    json_request.get("tag_list", ["tv shows"]),
                    json_request.get("container_dict", {}),
                )
            )
    # print(json.dumps(media_metadata, indent=4))
    return media_metadata, 200


@app.route("/get_tag_list", methods=["POST"])
def get_tag_list():
    media_metadata = {}
    if json_request := request.get_json():
        print(json_request)
        with DatabaseHandlerV2() as db_getter_connection:
            media_metadata["tag_list"] = db_getter_connection.get_all_tags()
    # print(json.dumps(media_metadata, indent=4))
    return media_metadata, 200


@app.route("/add_new_tag", methods=["POST"])
def add_new_tag():
    media_metadata = {}
    if json_request := request.get_json():
        print(json_request)
        if json_request.get("tag_title"):
            with DBCreatorV2() as db_connection:
                db_connection.insert_tag(json_request)
            with DatabaseHandlerV2() as db_getter_connection:
                media_metadata["tag_list"] = db_getter_connection.get_all_tags()
    return media_metadata, 200


@app.route("/add_tag_to_content", methods=["POST"])
def add_tag_to_content():
    media_metadata = {}
    if json_request := request.get_json():
        print(json_request)
        if json_request.get("tag_title") and json_request.get("content_id"):
            with DBCreatorV2() as db_connection:
                json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
                db_connection.add_tag_to_content(json_request)
            media_metadata["tag_title"] = json_request.get("tag_title")
    return media_metadata, 200


@app.route("/remove_tag_from_content", methods=["POST"])
def remove_tag_from_content():
    media_metadata = {}
    if json_request := request.get_json():
        print(json_request)
        if json_request.get("tag_title") and json_request.get("content_id"):
            with DBCreatorV2() as db_connection:
                json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
                db_connection.remove_tag_from_content(json_request)
            media_metadata["tag_title"] = json_request.get("tag_title")
    return media_metadata, 200


@app.route("/add_tag_to_container", methods=["POST"])
def add_tag_to_container():
    media_metadata = {}
    if json_request := request.get_json():
        print(json_request)
        if json_request.get("tag_title") and json_request.get("container_id"):
            with DBCreatorV2() as db_connection:
                json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
                db_connection.add_tag_to_container(json_request)
            media_metadata["tag_title"] = json_request.get("tag_title")
    return media_metadata, 200


@app.route("/remove_tag_from_container", methods=["POST"])
def remove_tag_from_container():
    media_metadata = {}
    if json_request := request.get_json():
        print(json_request)
        if json_request.get("tag_title") and json_request.get("container_id"):
            with DBCreatorV2() as db_connection:
                json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
                db_connection.remove_tag_from_container(json_request)
            media_metadata["tag_title"] = json_request.get("tag_title")
    return media_metadata, 200


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
        if json_request.get("content_id"):
            if not backend_handler.play_media_on_chromecast(json_request):
                with DatabaseHandlerV2() as db_connection:
                    media_metadata = db_connection.get_content_info(json_request.get("content_id"))
                data["local_play_url"] = media_metadata.get("url")
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
        if json_request.get("img_src"):
            print("Downloading")
            try:
                bh.download_image(json_request)
            except (ValueError, Exception) as e:
                print(e)
                if len(e.args) > 0:
                    data = {"error": e.args[0]}
                    print(data)
            data["img_src"] = json_request.get('img_src')
        with DatabaseHandlerV2() as db_connection:
            db_connection.update_metadata(json_request)
    return data, 200


@app.route(APIEndpoints.GET_MEDIA_MENU_DATA.value, methods=['POST'])
def get_media_menu_data():
    data = {}
    print(f"Not implemented: {APIEndpoints.GET_MEDIA_MENU_DATA.value}")
    return data, 200


@app.route(APIEndpoints.GET_DISK_SPACE.value, methods=['GET'])
def get_disk_space():
    try:
        data = {"free_space": bh.get_free_disk_space()}
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
    error_code = 400
    if request.method == 'POST':
        print(request.files)
        # check if the post request has the file part
        if 'file' not in request.files:
            data["message"] = "No file provided"
        else:
            file = request.files['file']
            if file.filename == '':
                data["message"] = "No selected file"
                data["filename"] = f"{file.filename}"
            elif file and allowed_file(file.filename):
                filename = secure_filename(file.filename).replace('_', ' ')
                try:
                    output_path = bh.build_tv_show_output_path(filename)
                    file.save(output_path)
                    data["message"] = "File saved"
                    data["filename"] = f"{file.filename}"
                    error_code = 200
                except (ValueError, FileExistsError) as e:
                    data["error"] = e.args[0]
    print(data)
    return data, error_code


if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5002)
