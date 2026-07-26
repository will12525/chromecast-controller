"""Editor (SERVER) routes: MP4 splitter UI and job control."""
import json
import traceback

from flask import request, render_template

import app.utils.backend_handler as backend_handler
from app.routes.shared import (
    APIEndpoints,
    bh,
    main_bp,
    media_controller_button_dict,
    media_types,
)


@main_bp.route(APIEndpoints.EDITOR.value)
def editor():
    try:
        return render_template(
            "editor.html",
            homepage_url=APIEndpoints.MAIN.value,
            button_dict=media_controller_button_dict,
            editor_metadata=bh.get_editor_metadata(),
            media_types=media_types,
        )
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


@main_bp.route(APIEndpoints.EDITOR_VALIDATE_TXT_FILE.value, methods=["POST"])
def editor_validate_txt_file():
    data = {"error": {"message": "File valid"}}
    if json_request := request.get_json():
        if json_request.get("file_name") and json_request.get("media_type"):
            try:
                if errors := backend_handler.editor_validate_txt_file(
                    json_request.get("file_name"), json_request.get("media_type")
                ):
                    data = {"process_log": errors}
            except Exception as e:
                print("Exception class: ", e.__class__)
                print(f"ERROR: {e}")
                print(traceback.print_exc())
                print(json.dumps(json_request, indent=4))
    return data, 200


@main_bp.route(APIEndpoints.EDITOR_SAVE_TXT_FILE.value, methods=["POST"])
def editor_save_txt_file():
    data = {"error": {"message": "File saved"}}
    if json_request := request.get_json():
        if (
            json_request.get("file_name")
            and json_request.get("media_type")
            and json_request.get("splitter_content")
        ):
            try:
                backend_handler.editor_save_file(json_request.get("file_name"), json_request)
            except Exception as e:
                print("Exception class: ", e.__class__)
                print(f"ERROR: {e}")
                print(traceback.print_exc())
                print(json.dumps(json_request, indent=4))
    return data, 200


@main_bp.route(APIEndpoints.EDITOR_LOAD_TXT_FILE.value, methods=["POST"])
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


@main_bp.route(APIEndpoints.DELETE_TXT_FILE.value, methods=["POST"])
def editor_delete_txt_file():
    data = {}
    if json_request := request.get_json():
        try:
            backend_handler.delete_splitter_file(json_request.get("file_name"))
            data = bh.get_editor_metadata()
        except Exception as e:
            print("Exception class: ", e.__class__)
            print(f"ERROR: {e}")
            print(traceback.print_exc())
            print(json.dumps(json_request, indent=4))
    return data, 200


@main_bp.route(APIEndpoints.EDITOR_PROCESS_TXT_FILE.value, methods=["POST"])
def editor_process_txt_file():
    data = {}
    if json_request := request.get_json():
        if json_request.get("file_name") and json_request.get("media_type"):
            try:
                errors = bh.editor_process_txt_file(
                    json_request.get("media_type"), json_request.get("file_name")
                )
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


@main_bp.route(APIEndpoints.EDITOR_PROCESSOR_METADATA.value, methods=["POST"])
def editor_processor_get_metadata():
    data = {}
    try:
        data = bh.editor_get_process_metadata()
    except Exception as e:
        print("Exception class: ", e.__class__)
        print(f"ERROR: {e}")
        print(traceback.print_exc())
    return data, 200
