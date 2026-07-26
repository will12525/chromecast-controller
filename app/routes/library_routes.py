"""Library browse, playback, scan, tags, and page shells."""
import traceback

from flask import request
from werkzeug.utils import secure_filename

import app.utils.backend_handler as backend_handler
import app.utils.common
from app.database.db_getter import DBHandler
from app.routes.shared import (
    APIEndpoints,
    allowed_file,
    bh,
    build_main_content,
    main_bp,
    play_response_from_metadata,
    system_mode,
)
from app.utils import content_transfer
from app.utils.common import SystemMode


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
                db_connection.query_db(
                    json_request.get("tag_list", ["tv shows"]),
                    json_request.get("container_dict", {}),
                    json_request.get("container_txt_search"),
                    json_request.get("content_txt_search"),
                )
            )
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
        finally:
            db_connection.close()
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


@main_bp.route(APIEndpoints.GET_MEDIA_CONTENT_TYPES.value, methods=["GET"])
def get_media_content_types():
    data = {"table_url": APIEndpoints.TABLE.value}
    if system_mode == SystemMode.SERVER:
        data["editor"] = APIEndpoints.EDITOR.value
    return data, 200


@main_bp.route(APIEndpoints.PLAY_MEDIA.value, methods=["POST"])
def play_media():
    data = {}
    if json_request := request.get_json():
        if json_request.get("content_id"):
            db_connection = DBHandler()
            try:
                media_metadata = bh.play_media_on_chromecast(json_request)
                if not media_metadata:
                    db_connection.open()
                    if json_request.get("parent_container_id") is None and json_request.get(
                        "tag_list"
                    ):
                        media_metadata = db_connection.get_content_info(
                            json_request.get("content_id")
                        )
                        data["play_mode"] = "play_random_content_with_tag"
                    else:
                        media_metadata = db_connection.get_content_info(
                            json_request.get("content_id")
                        )
                    if media_metadata.get("id"):
                        db_connection.update_content_play_count(media_metadata.get("id"))
                    play_response_from_metadata(media_metadata, json_request, data)
                else:
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


@main_bp.route("/play_random_container_content", methods=["POST"])
def play_random_container_content():
    data = {}
    if json_request := request.get_json():
        if json_request.get("parent_container_id"):
            data = bh.play_random_container_content(json_request)
        else:
            data["error_msg"] = f"Container ID not provided: {json_request}"
            print(data)
    return data, 200


@main_bp.route(APIEndpoints.GET_NEXT_MEDIA.value, methods=["POST"])
def get_next_media():
    data = {}
    media_metadata = {}
    if json_request := request.get_json():
        db_connection = DBHandler()
        try:
            db_connection.open()
            if json_request.get("content_id") and json_request.get("parent_container_id"):
                media_metadata = db_connection.get_next_content_in_container(json_request)
            elif (
                json_request.get("play_mode") == "play_random_content_with_tag"
                and json_request.get("tag_list")
            ):
                media_metadata = db_connection.get_random_content_with_tag(
                    json_request.get("tag_list")
                )
                data["play_mode"] = "play_random_content_with_tag"
            else:
                print(f"content_id not provided: {json_request}")
                data["error_msg"] = f"content_id or play_mode not provided: {json_request}"
            if media_metadata:
                play_response_from_metadata(media_metadata, json_request, data)
                if media_metadata.get("tag_list"):
                    data["tag_list"] = media_metadata.get("tag_list")
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
        finally:
            db_connection.close()
    return data, 200


@main_bp.route(APIEndpoints.UPDATE_MEDIA_METADATA.value, methods=["POST"])
def update_media_metadata():
    data = {}
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
            data["img_src"] = json_request.get("img_src")
        db_connection = DBHandler()
        db_connection.open()
        db_connection.update_metadata(json_request)
        db_connection.close()
    return data, 200


@main_bp.route(APIEndpoints.GET_MEDIA_MENU_DATA.value, methods=["POST"])
def get_media_menu_data():
    data = {}
    print(f"Not implemented: {APIEndpoints.GET_MEDIA_MENU_DATA.value}")
    return data, 200


@main_bp.route(APIEndpoints.GET_DISK_SPACE.value, methods=["GET"])
def get_disk_space():
    try:
        data = {"free_space": app.utils.common.get_free_disk_space(None)}
        return data, 200
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())


@main_bp.route(APIEndpoints.SCAN_STATUS.value, methods=["GET"])
def scan_status():
    """Lightweight poll for scan/transfer busy state."""
    return {
        "scanning": bool(bh.media_scan_in_progress),
        "transfer_in_progress": bool(bh.transfer_in_progress),
        "status": "busy"
        if bh.media_scan_in_progress or bh.transfer_in_progress
        else "idle",
    }, 200


@main_bp.route(APIEndpoints.SCAN_MEDIA_DIRECTORIES.value, methods=["POST"])
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
        if (
            data.get("status") == "ok"
            and system_mode == SystemMode.CLIENT
            and not bh.transfer_in_progress
        ):
            print("Starting server content pull")
            bh.transfer_in_progress = True
            try:
                content_transfer.query_server()
            finally:
                bh.transfer_in_progress = False
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


@main_bp.route(APIEndpoints.LIBRARY_HOME.value, methods=["GET"])
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


@main_bp.route(APIEndpoints.PLAYBACK_PROGRESS.value, methods=["POST"])
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


@main_bp.route(APIEndpoints.MEDIA_UPLOAD.value, methods=["GET", "POST"])
def upload_file():
    data = {"error_code": 400}
    if request.method == "POST":
        print(request.files)
        if "file" not in request.files:
            data["message"] = "No file provided"
        else:
            file = request.files["file"]
            if file.filename == "":
                data["message"] = "No selected file"
                data["filename"] = f"{file.filename}"
            elif file and allowed_file(file.filename):
                filename = secure_filename(file.filename).replace("_", " ")
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
