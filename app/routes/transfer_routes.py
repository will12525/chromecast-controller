"""CLIENT/SERVER content transfer endpoints."""
import traceback

from flask import request

from app.routes.shared import APIEndpoints, main_bp, system_mode
from app.utils import content_transfer


@main_bp.route(APIEndpoints.SERVER_CONNECT.value, methods=["GET", "POST"])
def server_connect():
    data = {"error_code": 400}
    if json_request := request.get_json():
        content_transfer.new_client_connection(
            system_mode, json_request.get("server_token", ""), data
        )
    return data, data["error_code"]


@main_bp.route(APIEndpoints.REQUEST_ALL_CONTENT.value, methods=["GET", "POST"])
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


@main_bp.route(APIEndpoints.REQUEST_IMAGE.value, methods=["GET", "POST"])
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


@main_bp.route(APIEndpoints.REQUEST_CONTENT.value, methods=["GET", "POST"])
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
