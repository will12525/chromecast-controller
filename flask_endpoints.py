import json
import os
import pathlib
import queue

from enum import Enum, auto
import traceback

import requests
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename

import backend_handler
from chromecast_handler import CommandList
from database_handler.db_getter import DatabaseHandlerV2
from database_handler.common_objects import ContentType
import config_file_handler
from database_handler.db_setter import DBCreatorV2

# TODO: UI
# TODO: Notify user when media scan completes
# TODO: All content containers shall be playable
# TODO: The user shall have the ability to quickly play a random content

# TODO: Application split
# TODO: Create server client connections
# TODO: Enable db content sharing
# TODO: Enable media_content distribution
# TODO: Isolate editor from player
# TODO: Remove editor from client

# TODO: PLAYER
# TODO: Make local media player: https://www.tutorialspoint.com/opencv_python/opencv_python_play_video_file.htm
# TODO: Prevent additional scans from occurring while scan in progress

# TODO: EDITOR
# TODO: Enable user to view remaining storage space
# TODO: Prevent media additions if space is low

# TODO: TAGS
# TODO: UI: DB: Enable user to search by media_title

# TODO: Cleanup
# TODO: Convert all js functions calls embedded in html to event listeners in app.js
# TODO: Convert chromecast name strings to IDs and use IDs to refer to chromecasts
# TODO: The chromecast select menu shall never contain chromecasts that no longer exist

HANDSHAKE_SECRET = "Hello world!"
HANDSHAKE_RESPONSE = "LEONARD IS THE COOLEST DINOSAUR"


class SystemMode(Enum):
    SERVER = auto()
    CLIENT = auto()


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
    MEDIA_SHARE = "/media_share"
    SERVER_CONNECT = "/server_connect"
    REQUEST_CONTENT = "/request_content"


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', "mp4"}

app = Flask(__name__)
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True
app.config['SEND_FILE_MAX_AGE'] = 0  # Disable caching to force compression
app.config['COMPRESSOR_MIMETYPES'] = ['video/mp4']

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
setup_thread = bh.start()

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


@app.route(APIEndpoints.EDITOR_VALIDATE_TXT_FILE.value, methods=['POST'])
def editor_validate_txt_file():
    data = {"error": {"message": "File valid"}}
    if json_request := request.get_json():
        if json_request.get("file_name"):
            try:
                if errors := backend_handler.editor_validate_txt_file(json_request):
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
        if json_request.get("file_name") and json_request.get("media_type") and json_request.get("splitter_content"):
            try:
                backend_handler.editor_save_file(json_request.get('file_name'), json_request)
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
                data = bh.get_editor_metadata(selected_txt_file=editor_txt_file_name)
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
        if json_request.get("file_name") and json_request.get("media_type"):
            try:
                errors = bh.editor_process_txt_file(json_request)
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


@app.route(APIEndpoints.EDITOR_PROCESSOR_METADATA.value, methods=['POST'])
def editor_processor_get_metadata():
    data = {}
    try:
        data = bh.editor_get_process_metadata()
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
    with DatabaseHandlerV2() as db_getter_connection:
        media_metadata["tag_list"] = db_getter_connection.get_all_tags()
    return media_metadata, 200


@app.route("/add_new_tag", methods=["POST"])
def add_new_tag():
    media_metadata = {}
    if json_request := request.get_json():
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
        if json_request.get("tag_title") and json_request.get("content_id"):
            with DBCreatorV2() as db_connection:
                json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
                db_connection.add_tag_to_content(json_request)
            with DatabaseHandlerV2() as db_connection:
                media_metadata.update(db_connection.query_content_tags(json_request.get("content_id")))
            media_metadata["tag_title"] = json_request.get("tag_title")
        elif json_request.get("tag_title") and json_request.get("container_id"):
            with DBCreatorV2() as db_connection:
                json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
                db_connection.add_tag_to_container(json_request)
            with DatabaseHandlerV2() as db_connection:
                media_metadata.update(db_connection.query_container_tags(json_request.get("container_id")))
            media_metadata["tag_title"] = json_request.get("tag_title")
    return media_metadata, 200


@app.route("/remove_tag_from_content", methods=["POST"])
def remove_tag_from_content():
    media_metadata = {}
    if json_request := request.get_json():
        if json_request.get("tag_title") and json_request.get("content_id"):
            with DBCreatorV2() as db_connection:
                json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
                db_connection.remove_tag_from_content(json_request)
            with DatabaseHandlerV2() as db_connection:
                media_metadata.update(db_connection.query_content_tags(json_request.get("content_id")))
            media_metadata["tag_title"] = json_request.get("tag_title")
        elif json_request.get("tag_title") and json_request.get("container_id"):
            with DBCreatorV2() as db_connection:
                json_request["user_tags_id"] = db_connection.get_tag_id(json_request)
                db_connection.remove_tag_from_container(json_request)
            with DatabaseHandlerV2() as db_connection:
                media_metadata.update(db_connection.query_container_tags(json_request.get("container_id")))
            media_metadata["tag_title"] = json_request.get("tag_title")
    return media_metadata, 200


@app.route(APIEndpoints.GET_MEDIA_CONTENT_TYPES.value, methods=['GET'])
def get_media_content_types():
    data = {}
    if system_mode == SystemMode.SERVER:
        data["editor"] = APIEndpoints.EDITOR.value
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
            bh.seek_media_time(new_media_time)
    return data, 200


@app.route(APIEndpoints.GET_CURRENT_MEDIA_RUNTIME.value, methods=['GET'])
def get_current_media_runtime():
    data = {}
    if media_metadata := bh.get_chromecast_media_controller_metadata():
        data = media_metadata
    return data, 200


@app.route(APIEndpoints.CONNECT_CHROMECAST.value, methods=['POST'])
def connect_chromecast():
    data = {}
    if json_request := request.get_json():
        if chromecast_id := json_request.get("chromecast_id"):
            if bh.connect_chromecast(chromecast_id):
                data = {'chromecast_id': chromecast_id}
    return data, 200


@app.route(APIEndpoints.GET_CHROMECAST_LIST.value, methods=['POST'])
def get_chromecast_list():
    data = {
        "scanned_devices": bh.get_chromecast_scan_list(),
        "connected_device": bh.get_chromecast_device_id()
    }
    return data, 200


@app.route(APIEndpoints.DISCONNECT_CHROMECAST.value, methods=['POST'])
def disconnect_chromecast():
    data = {}
    bh.disconnect_chromecast()
    return data, 200


@app.route(APIEndpoints.CHROMECAST_COMMAND.value, methods=['POST'])
def chromecast_command():
    data = {}
    if json_request := request.get_json():
        if chromecast_cmd_id := json_request.get("chromecast_cmd_id"):
            bh.send_chromecast_cmd(CommandList(chromecast_cmd_id))
    return data, 200


@app.route(APIEndpoints.PLAY_MEDIA.value, methods=['POST'])
def play_media():
    data = {}
    if json_request := request.get_json():
        if json_request.get("content_id"):
            if not bh.play_media_on_chromecast(json_request):
                with DatabaseHandlerV2() as db_connection:
                    media_metadata = db_connection.get_content_info(json_request.get("content_id"))
                data["local_play_url"] = media_metadata.get("url")
        else:
            print(f"Media ID not provided: {json_request}")
    return data, 200


@app.route(APIEndpoints.UPDATE_MEDIA_METADATA.value, methods=['POST'])
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
        data = {"free_space": backend_handler.get_free_disk_space()}
        return data, 200
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def server_request(url, json_data):
    response = requests.post(url, json=json_data)
    try:
        return response.json()
    except requests.JSONDecodeError as e:
        print(e)


def query_server():
    print("Server scan triggered")
    if system_mode == SystemMode.CLIENT and not bh.transfer_in_progress:
        print("Starting server scan")
        bh.transfer_in_progress = True
        if server_url := config_file_handler.load_json_file_content().get("server_url"):
            print(f"Searching for server at: {server_url}")
            search_response_data = server_request(f"{server_url}/server_connect", {"message": HANDSHAKE_SECRET})
            print(f"Server response: {search_response_data}")
            if search_response_data and search_response_data.get("message") == HANDSHAKE_RESPONSE:
                path_request_response_data = server_request(f"{server_url}/media_share",
                                                            {"message": HANDSHAKE_RESPONSE})
                print(f"Server secret: {path_request_response_data}")
                for content_src in reversed(path_request_response_data.get("content_srcs")):
                    print(f"Server content: {content_src}")
                    with DatabaseHandlerV2() as db_connection:
                        if not db_connection.check_if_content_src_exists(content_src.get("content_src")):
                            try:
                                output_file = backend_handler.build_tv_show_output_path(content_src.get("content_src"))
                                print(f"Expected save path: {output_file}")
                                if output_file:
                                    print(f"Requesting: {content_src}")
                                    # '54 Lincoln Backyard Timelapse - s2024e234.mp4'
                                    response = requests.post(f"{server_url}/request_content",
                                                             json={
                                                                 "message": HANDSHAKE_RESPONSE,
                                                                 "id": content_src.get("id")
                                                             })
                                    print(response)
                                    response.raise_for_status()  # Raise an exception for error responses
                                    print(f"Saving content: {output_file}")
                                    with open(output_file, 'wb') as f:
                                        f.write(response.content)
                                    print('File downloaded successfully!')
                            except (requests.exceptions.RequestException, FileExistsError, Exception) as e:
                                print(f'Error downloading file: {e} ')
        print("Server scan complete")
        bh.transfer_in_progress = False


@app.route(APIEndpoints.SCAN_MEDIA_DIRECTORIES.value, methods=['POST'])
def scan_media_directories():
    """
        X User triggeres media scan
        X media scan asses local files
        media scan asses free disk space
        X media scan checks for server
        media scan submits all local paths to server
        server begins distributing missing paths to client
        media client asses free disk space
        media client stores new paths in disk with free space
        media client rejects distribution if out of disk space

        :return:
    """
    data = {}
    bh.scan_media_directories()
    try:
        query_server()
    except Exception as e:
        print(e)
    bh.scan_media_directories()

    return data, 200


@app.route(APIEndpoints.SERVER_CONNECT.value, methods=['GET', 'POST'])
def server_connect():
    data = {}
    error_code = 400
    if json_request := request.get_json():
        if system_mode == SystemMode.CLIENT:
            data["error"] = "not a server"
            error_code = 400
        elif system_mode == SystemMode.SERVER and json_request.get("message", "") == HANDSHAKE_SECRET:
            print("Client encountered")
            data["message"] = HANDSHAKE_RESPONSE
            error_code = 200
        else:
            data["error"] = "System in unknown mode"
            error_code = 400

            print(json.dumps(json_request, indent=4))
        # try:
        #     print(json.dumps(backend_handler.get_system_data(), indent=4))
        # except Exception as e:
        #     print(e)
    return data, error_code


@app.route(APIEndpoints.MEDIA_SHARE.value, methods=['GET', 'POST'])
def media_share():
    data = {}
    if json_request := request.get_json():
        print("Client connected")
        if json_request.get("message") == HANDSHAKE_RESPONSE:
            with DatabaseHandlerV2() as db_connection:
                content_paths = db_connection.get_all_content_paths()
            for content_path in content_paths:
                content_path["content_src"] = pathlib.Path(content_path["content_src"]).name
            # print(content_paths)
            data["content_srcs"] = content_paths
        # print(json.dumps(json_request, indent=4))
        print(f"Sharing content {data}")
    return data, 200


@app.route(APIEndpoints.REQUEST_CONTENT.value, methods=['GET', 'POST'])
def request_content():
    data = {}
    error_code = 400
    if json_request := request.get_json():
        print(f"Content id requested: {json.dumps(json_request, indent=4)}")
        if json_request.get("message") == HANDSHAKE_RESPONSE and (content_id := json_request.get("id")):
            with DatabaseHandlerV2() as db_connection:
                content_data = db_connection.get_content_info(content_id)
            if content_path := content_data.get('path'):
                print(f"Found content path {content_path}")
                if os.path.exists(content_path):
                    try:
                        file_size = os.path.getsize(content_path)
                        if file_size > 2 * 1024 * 1024 * 1024:
                            data["error"] = 'File is too large'
                        else:
                            return send_file(content_data.get("path"), as_attachment=True, mimetype='video/mp4')
                    except FileNotFoundError:
                        data["error"] = 'File not found'
                        error_code = 404

                else:
                    data["error"] = 'File not found'
                    error_code = 404
            else:
                data["error"] = 'Content missing path'
                error_code = 404

            # return send_file(content_data.get("path"), as_attachment=True, mimetype='video/mp4')

            # response = requests.post(f"{request.url_root}media_upload",
            #                          json={"file_name": pathlib.Path(content_data.get("content_src")).name},
            #                          files={'file': open(content_data.get("path"), 'rb')})
            # try:
            #     data = response.json()
            # except requests.JSONDecodeError:
            #     data = None
            # print(data)

            # for content_path in content_paths:
            #     content_path["content_src"] = pathlib.Path(content_path["content_src"]).name
            # # print(content_paths)
            # data["content_srcs"] = content_paths
        # print(json.dumps(json_request, indent=4))
    print(data)
    return data, error_code


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
                print(filename)
                try:
                    output_path = backend_handler.build_tv_show_output_path(filename)
                    print(output_path)
                    # file.save(output_path)
                    data["message"] = "File saved"
                    data["filename"] = f"{file.filename}"
                    error_code = 200
                except (ValueError, FileExistsError) as e:
                    data["error"] = e.args[0]
    print(data)
    return data, error_code


# query_server()

if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5002)
