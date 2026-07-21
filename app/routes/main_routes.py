import json
import queue

from enum import Enum
import traceback

from flask import request, render_template, Blueprint
from werkzeug.utils import secure_filename

import app.utils.backend_handler as backend_handler
import app.utils.common
from app.utils.chromecast_handler import CommandList
from app.database.db_getter import DBHandler
from app.utils.common import ContentType, SystemMode
from app.utils import config_file_handler
from app.utils import content_transfer

main_bp = Blueprint("main", __name__)

# Backlog (Phase 2+): route split, content_transfer harden, Chromecast UUID ids,
# editor low-storage guards, richer scan progress polling.

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', "mp4"}


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


media_controller_button_dict = {
    "rewind": {"icon": "bi-rewind-fill", "id": f"{CommandList.CMD_REWIND.name}_media_button"},
    "rewind_15": {"icon": "bi-rewind-circle", "id": f"{CommandList.CMD_REWIND_15.name}_media_button"},
    "play": {"icon": "bi-play-fill", "id": f"{CommandList.CMD_PLAY.name}_media_button"},
    "pause": {"icon": "bi-pause-fill", "id": f"{CommandList.CMD_PAUSE.name}_media_button"},
    "skip_15": {"icon": "bi-fast-forward-circle", "id": f"{CommandList.CMD_SKIP_15.name}_media_button"},
    "skip": {"icon": "bi-fast-forward-fill", "id": f"{CommandList.CMD_SKIP.name}_media_button"},
    "stop": {"icon": "bi-stop-fill", "id": f"{CommandList.CMD_STOP.name}_media_button"}
}
media_types = [
    ContentType.RAW.name,
    ContentType.TV.name,
    ContentType.MOVIE.name,
    ContentType.BOOK.name
]

system_mode = SystemMode.CLIENT

if config_file_handler.load_json_file_content().get("mode") == SystemMode.SERVER.name:
    system_mode = SystemMode.SERVER

bh = backend_handler.BackEndHandler()
bh.start()
error_log = queue.Queue()


def build_main_content():
    # system_data = backend_handler.get_system_data()
    try:
        return render_template("index.html", homepage_url=APIEndpoints.MAIN.value,
                               button_dict=media_controller_button_dict, system_mode=system_mode.name)
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
        return str(traceback.print_exc())


@main_bp.route(APIEndpoints.EDITOR.value)
def editor():
    try:
        return render_template("editor.html",
                               homepage_url=APIEndpoints.MAIN.value,
                               button_dict=media_controller_button_dict,
                               editor_metadata=bh.get_editor_metadata(),
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


@main_bp.route(APIEndpoints.EDITOR_VALIDATE_TXT_FILE.value, methods=['POST'])
def editor_validate_txt_file():
    data = {"error": {"message": "File valid"}}
    if json_request := request.get_json():
        if json_request.get("file_name") and json_request.get("media_type"):
            try:
                if errors := backend_handler.editor_validate_txt_file(json_request.get("file_name"),
                                                                      json_request.get("media_type")):
                    data = {"process_log": errors}
            except Exception as e:
                print("Exception class: ", e.__class__)
                print(f"ERROR: {e}")
                print(traceback.print_exc())
                print(json.dumps(json_request, indent=4))
    return data, 200


@main_bp.route(APIEndpoints.EDITOR_SAVE_TXT_FILE.value, methods=['POST'])
def editor_save_txt_file():
    data = {"error": {"message": "File saved"}}
    if json_request := request.get_json():
        if json_request.get("file_name") and json_request.get("media_type") and json_request.get("splitter_content"):
            try:
                backend_handler.editor_save_file(json_request.get('file_name'), json_request)
            except Exception as e:
                print("Exception class: ", e.__class__)
                print(f"ERROR: {e}")
                print(traceback.print_exc())
                print(json.dumps(json_request, indent=4))
    return data, 200


@main_bp.route(APIEndpoints.EDITOR_LOAD_TXT_FILE.value, methods=['POST'])
def editor_load_txt_file():
    data = {}
    if json_request := request.get_json():
        if editor_txt_file_name := json_request.get("editor_txt_file_name"):
            try:
                data = bh.get_editor_metadata(selected_txt_file=editor_txt_file_name)
            except Exception as e:
                print("Exception class: ", e.__class__)
                print(f"ERROR: {e}")
                print(traceback.print_exc())
                print(json.dumps(json_request, indent=4))
    return data, 200


@main_bp.route(APIEndpoints.DELETE_TXT_FILE.value, methods=['POST'])
def editor_delete_txt_file():
    data = {}
    if json_request := request.get_json():
        try:
            backend_handler.delete_splitter_file(json_request.get('file_name'))
            data = bh.get_editor_metadata()
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
            print(json.dumps(json_request, indent=4))
    return data, 200


@main_bp.route(APIEndpoints.EDITOR_PROCESS_TXT_FILE.value, methods=['POST'])
def editor_process_txt_file():
    data = {}
    if json_request := request.get_json():
        if json_request.get("file_name") and json_request.get("media_type"):
            try:
                errors = bh.editor_process_txt_file(json_request.get("media_type"), json_request.get("file_name"))
                data = bh.editor_get_process_metadata()
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


@main_bp.route(APIEndpoints.EDITOR_PROCESSOR_METADATA.value, methods=['POST'])
def editor_processor_get_metadata():
    data = {}
    try:
        data = bh.editor_get_process_metadata()
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
    return data, 200


@main_bp.route(APIEndpoints.MAIN.value)
def main_index():
    return build_main_content()


@main_bp.route(APIEndpoints.TABLE.value)
def table_index():
    return build_main_content()


@main_bp.route(APIEndpoints.QUERY_DB.value, methods=["POST"])
def query_media_db():
    media_metadata = {}
    if json_request := request.get_json():
        print(json_request)
        db_connection = DBHandler()
        try:
            db_connection.open()
            media_metadata.update(
                db_connection.query_db(json_request.get("tag_list", ["tv shows"]),
                                       json_request.get("container_dict", {}),
                                       json_request.get("container_txt_search"),
                                       json_request.get("content_txt_search"))
            )
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
        finally:
            db_connection.close()

    # print(json.dumps(media_metadata, indent=4))
    return media_metadata, 200


@main_bp.route("/get_tag_list", methods=["POST"])
def get_tag_list():
    media_metadata = {}
    db_connection = DBHandler()
    db_connection.open()
    media_metadata["tag_list"] = db_connection.get_all_tags()
    db_connection.close()

    return media_metadata, 200


@main_bp.route("/add_new_tag", methods=["POST"])
def add_new_tag():
    media_metadata = {}
    error_code = 422
    if (json_request := request.get_json()) and json_request.get("tag_title"):
        db_connection = DBHandler()
        db_connection.open()
        if db_connection.insert_tag(json_request):
            error_code = 200
        media_metadata["tag_list"] = db_connection.get_all_tags()
        db_connection.close()

    return media_metadata, error_code


@main_bp.route("/add_tag_to_content", methods=["POST"])
def add_tag_to_content():
    media_metadata = {}
    error_code = 200
    if json_request := request.get_json():
        db_connection = DBHandler()
        db_connection.open()
        if json_request.get("tag_title") and json_request.get("content_id"):
            json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
            if not db_connection.add_tag_to_content(json_request):
                error_code = 422
            media_metadata.update(db_connection.query_content_tags(json_request.get("content_id")))
            media_metadata["tag_title"] = json_request.get("tag_title")
        elif json_request.get("tag_title") and json_request.get("container_id"):
            json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
            db_connection.add_tag_to_container(json_request)
            media_metadata.update(db_connection.query_container_tags(json_request.get("container_id")))
            media_metadata["tag_title"] = json_request.get("tag_title")
        db_connection.close()

    return media_metadata, error_code


@main_bp.route("/remove_tag_from_content", methods=["POST"])
def remove_tag_from_content():
    media_metadata = {}
    if json_request := request.get_json():
        db_connection = DBHandler()
        db_connection.open()
        if json_request.get("tag_title") and json_request.get("content_id"):
            json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
            db_connection.remove_tag_from_content(json_request)
            media_metadata.update(db_connection.query_content_tags(json_request.get("content_id")))
            media_metadata["tag_title"] = json_request.get("tag_title")
        elif json_request.get("tag_title") and json_request.get("container_id"):
            json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
            db_connection.remove_tag_from_container(json_request)
            media_metadata.update(db_connection.query_container_tags(json_request.get("container_id")))
            media_metadata["tag_title"] = json_request.get("tag_title")
        db_connection.close()

    return media_metadata, 200


@main_bp.route(APIEndpoints.GET_MEDIA_CONTENT_TYPES.value, methods=['GET'])
def get_media_content_types():
    data = {"table_url": APIEndpoints.TABLE.value}
    if system_mode == SystemMode.SERVER:
        data["editor"] = APIEndpoints.EDITOR.value
    return data, 200


@main_bp.route(APIEndpoints.GET_CHROMECAST_CONTROLS.value, methods=['GET'])
def get_chromecast_controls():
    data = {"chromecast_controls": {i.name: i.value for i in CommandList}}
    return data, 200


@main_bp.route(APIEndpoints.SET_CURRENT_MEDIA_RUNTIME.value, methods=['POST'])
def set_current_media_runtime():
    data = {}
    if json_request := request.get_json():
        if new_media_time := json_request.get("new_media_time"):
            bh.seek_media_time(new_media_time)
    return data, 200


@main_bp.route(APIEndpoints.GET_CURRENT_MEDIA_RUNTIME.value, methods=['GET'])
def get_current_media_runtime():
    data = {}
    if media_metadata := bh.get_chromecast_media_controller_metadata():
        data = media_metadata
    return data, 200


@main_bp.route(APIEndpoints.CONNECT_CHROMECAST.value, methods=['POST'])
def connect_chromecast():
    data = {}
    if json_request := request.get_json():
        if chromecast_id := json_request.get("chromecast_id"):
            if bh.connect_chromecast(chromecast_id):
                data = {'chromecast_id': chromecast_id}
    return data, 200


@main_bp.route(APIEndpoints.GET_CHROMECAST_LIST.value, methods=['POST'])
def get_chromecast_list():
    data = {
        "scanned_devices": bh.get_chromecast_scan_list(),
        "connected_device": bh.get_chromecast_device_id()
    }
    return data, 200


@main_bp.route(APIEndpoints.DISCONNECT_CHROMECAST.value, methods=['POST'])
def disconnect_chromecast():
    data = {}
    bh.disconnect_chromecast()
    return data, 200


@main_bp.route(APIEndpoints.CHROMECAST_COMMAND.value, methods=['POST'])
def chromecast_command():
    data = {}
    if json_request := request.get_json():
        if chromecast_cmd_id := json_request.get("chromecast_cmd_id"):
            bh.send_chromecast_cmd(CommandList(chromecast_cmd_id))
    return data, 200


def _play_response_from_metadata(media_metadata, json_request, data):
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


@main_bp.route(APIEndpoints.PLAY_MEDIA.value, methods=['POST'])
def play_media():
    data = {}
    if json_request := request.get_json():
        if json_request.get("content_id"):
            db_connection = DBHandler()
            try:
                media_metadata = bh.play_media_on_chromecast(json_request)
                if not media_metadata:
                    # Cast not connected / failed — serve local browser player
                    db_connection.open()
                    if json_request.get("parent_container_id") is None and json_request.get("tag_list"):
                        media_metadata = db_connection.get_content_info(json_request.get("content_id"))
                        data["play_mode"] = "play_random_content_with_tag"
                    else:
                        media_metadata = db_connection.get_content_info(json_request.get("content_id"))
                    if media_metadata.get("id"):
                        db_connection.update_content_play_count(media_metadata.get("id"))
                    _play_response_from_metadata(media_metadata, json_request, data)
                else:
                    # Cast succeeded — do not set local_play_url (avoids dual playback).
                    # Still return ids/title for UI and progress tracking.
                    data["id"] = media_metadata.get("id")
                    data["parent_container_id"] = json_request.get("parent_container_id")
                    data["content_title"] = media_metadata.get("content_title")
                    data["tag_list"] = json_request.get("tag_list")
                    data["last_position"] = media_metadata.get("last_position") or 0
                    data["last_duration"] = media_metadata.get("last_duration") or 0
            except Exception as e:
                print("Exception class: ", e.__class__)
                print(f"ERROR: {e}")
                print(traceback.print_exc())
            finally:
                db_connection.close()

        else:
            print(f"Media ID not provided: {json_request}")
    return data, 200


@main_bp.route("/play_random_container_content", methods=['POST'])
def play_random_container_content():
    data = {}
    if json_request := request.get_json():
        if json_request.get("parent_container_id"):
            data = bh.play_random_container_content(json_request)
        else:
            data["error_msg"] = f"Container ID not provided: {json_request}"
            print(data)
    return data, 200


@main_bp.route(APIEndpoints.GET_NEXT_MEDIA.value, methods=['POST'])
def get_next_media():
    data = {}
    media_metadata = {}
    if json_request := request.get_json():
        db_connection = DBHandler()
        try:
            db_connection.open()
            if json_request.get("content_id") and json_request.get("parent_container_id"):
                media_metadata = db_connection.get_next_content_in_container(json_request)
            elif json_request.get("play_mode") == "play_random_content_with_tag" and json_request.get("tag_list"):
                media_metadata = db_connection.get_random_content_with_tag(json_request.get("tag_list"))
                data["play_mode"] = "play_random_content_with_tag"
            else:
                print(f"content_id not provided: {json_request}")
                data["error_msg"] = f"content_id or play_mode not provided: {json_request}"
            if media_metadata:
                _play_response_from_metadata(media_metadata, json_request, data)
                if media_metadata.get("tag_list"):
                    data["tag_list"] = media_metadata.get("tag_list")
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
        finally:
            db_connection.close()
    return data, 200


@main_bp.route(APIEndpoints.UPDATE_MEDIA_METADATA.value, methods=['POST'])
def update_media_metadata():
    data = {}
    # If exception, pass to error log
    if json_request := request.get_json():
        if json_request.get("img_src"):
            print("Downloading")
            try:
                backend_handler.download_image(json_request)
            except (ValueError, Exception) as e:
                print(e)
                if len(e.args) > 0:
                    data = {"error": e.args[0]}
                    print(data)
            data["img_src"] = json_request.get('img_src')
        db_connection = DBHandler()
        db_connection.open()
        db_connection.update_metadata(json_request)
        db_connection.close()

    return data, 200


@main_bp.route(APIEndpoints.GET_MEDIA_MENU_DATA.value, methods=['POST'])
def get_media_menu_data():
    data = {}
    print(f"Not implemented: {APIEndpoints.GET_MEDIA_MENU_DATA.value}")
    return data, 200


@main_bp.route(APIEndpoints.GET_DISK_SPACE.value, methods=['GET'])
def get_disk_space():
    try:
        data = {"free_space": app.utils.common.get_free_disk_space(None)}
        return data, 200
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())


@main_bp.route(APIEndpoints.SCAN_MEDIA_DIRECTORIES.value, methods=['POST'])
def scan_media_directories():
    """
    Trigger a media directory scan. Concurrent scans return status=busy.
    CLIENT mode may also pull missing content from the server after a successful scan.
    """
    data = {"status": "ok", "message": "Scan complete"}
    try:
        result = bh.scan_media_directories()
        if isinstance(result, dict):
            data.update(result)
        print("Server scan triggered:", data.get("status"))
        if data.get("status") == "ok" and system_mode == SystemMode.CLIENT and not bh.transfer_in_progress:
            print("Starting server content pull")
            bh.transfer_in_progress = True
            try:
                content_transfer.query_server()
            finally:
                bh.transfer_in_progress = False
            # Rescan after transfer so newly pulled files appear in the catalog
            result = bh.scan_media_directories()
            if isinstance(result, dict):
                data.update(result)
                if data.get("status") == "ok":
                    data["message"] = "Scan complete (synced from server)"
    except Exception as e:
        print(e)
        data = {"status": "error", "message": str(e)}
    http_status = 200 if data.get("status") in ("ok", "busy") else 500
    return data, http_status


@main_bp.route(APIEndpoints.LIBRARY_HOME.value, methods=['GET'])
def library_home():
    data = {
        "continue_watching": [],
        "recently_added": [],
        "recently_played": [],
        "libraries": [],
    }
    db_connection = DBHandler()
    try:
        db_connection.open()
        data = db_connection.get_library_home(limit=20)
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
        data["error"] = str(e)
    finally:
        db_connection.close()
    return data, 200


@main_bp.route(APIEndpoints.PLAYBACK_PROGRESS.value, methods=['POST'])
def playback_progress():
    data = {"status": "ok"}
    if json_request := request.get_json():
        content_id = json_request.get("content_id")
        position = json_request.get("position")
        duration = json_request.get("duration")
        if content_id is None or position is None:
            return {"status": "error", "message": "content_id and position required"}, 400
        db_connection = DBHandler()
        try:
            db_connection.open()
            if not db_connection.update_playback_progress(content_id, position, duration):
                data = {"status": "error", "message": "invalid progress"}
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
            data = {"status": "error", "message": str(e)}
        finally:
            db_connection.close()
    else:
        return {"status": "error", "message": "JSON body required"}, 400
    return data, 200


@main_bp.route(APIEndpoints.CONNECT_LOCAL_PLAYER.value, methods=['POST'])
def connect_local_player():
    """Switch UI to local HTML5 playback (disconnect Chromecast if connected)."""
    bh.disconnect_chromecast()
    return {"player": "local", "chromecast_id": None}, 200


@main_bp.route(APIEndpoints.SERVER_CONNECT.value, methods=['GET', 'POST'])
def server_connect():
    data = {"error_code": 400}
    if json_request := request.get_json():
        content_transfer.new_client_connection(system_mode, json_request.get("server_token", ""), data)
    return data, data["error_code"]


@main_bp.route(APIEndpoints.REQUEST_ALL_CONTENT.value, methods=['GET', 'POST'])
def request_all_content():
    data = {"error_code": 200}
    if json_request := request.get_json():
        try:
            content_transfer.request_all_content(json_request.get("server_token", ""), data)
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
    return data, data["error_code"]


@main_bp.route(APIEndpoints.REQUEST_IMAGE.value, methods=['GET', 'POST'])
def request_image():
    data = {"error_code": 200}
    if json_request := request.get_json():
        try:
            if request_response := content_transfer.request_image(json_request, data):
                return request_response
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
    return data, data["error_code"]


@main_bp.route(APIEndpoints.REQUEST_CONTENT.value, methods=['GET', 'POST'])
def request_content():
    data = {"error_code": 400}
    if json_request := request.get_json():
        try:
            if request_response := content_transfer.request_content(json_request, data):
                return request_response
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
    print(data)
    return data, data["error_code"]


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main_bp.route(APIEndpoints.MEDIA_UPLOAD.value, methods=['GET', 'POST'])
def upload_file():
    data = {"error_code": 400}
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
                print(filename)
                try:
                    output_path = app.utils.common.build_tv_show_output_path(filename)
                    print(output_path)
                    file.save(output_path)
                    data["message"] = "File saved"
                    data["filename"] = f"{file.filename}"
                    data["error_code"] = 200
                except (ValueError, FileExistsError) as e:
                    data["error"] = e.args[0]
    print(data)
    return data, data["error_code"]

# content_transfer.query_server()
