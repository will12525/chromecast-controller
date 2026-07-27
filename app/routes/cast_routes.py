"""Chromecast discovery, connection, and transport controls."""
from flask import request

from app.routes.shared import APIEndpoints, bh, main_bp
from app.utils.chromecast_handler import CommandList


@main_bp.route(APIEndpoints.GET_CHROMECAST_CONTROLS.value, methods=["GET"])
def get_chromecast_controls():
    data = {"chromecast_controls": {i.name: i.value for i in CommandList}}
    return data, 200


@main_bp.route(APIEndpoints.SET_CURRENT_MEDIA_RUNTIME.value, methods=["POST"])
def set_current_media_runtime():
    data = {}
    if json_request := request.get_json():
        if new_media_time := json_request.get("new_media_time"):
            bh.seek_media_time(new_media_time)
    return data, 200


@main_bp.route(APIEndpoints.GET_CURRENT_MEDIA_RUNTIME.value, methods=["GET"])
def get_current_media_runtime():
    data = {}
    if media_metadata := bh.get_chromecast_media_controller_metadata():
        data = media_metadata
    return data, 200


@main_bp.route(APIEndpoints.CONNECT_CHROMECAST.value, methods=["POST"])
def connect_chromecast():
    data = {}
    if json_request := request.get_json():
        if chromecast_id := json_request.get("chromecast_id"):
            if bh.connect_chromecast(chromecast_id):
                data = {
                    "chromecast_id": bh.get_chromecast_device_id() or chromecast_id,
                    "chromecast_name": bh.get_chromecast_device_name(),
                }
    return data, 200


@main_bp.route(APIEndpoints.GET_CHROMECAST_LIST.value, methods=["POST"])
def get_chromecast_list():
    # scanned_devices: [{uuid, name}, ...] — connect with uuid, display name
    data = {
        "scanned_devices": bh.get_chromecast_scan_list(),
        "connected_device": bh.get_chromecast_device_name() or bh.get_chromecast_device_id(),
        "connected_device_id": bh.get_chromecast_device_id(),
    }
    return data, 200


@main_bp.route(APIEndpoints.DISCONNECT_CHROMECAST.value, methods=["POST"])
def disconnect_chromecast():
    data = {}
    bh.disconnect_chromecast()
    return data, 200


@main_bp.route(APIEndpoints.CHROMECAST_COMMAND.value, methods=["POST"])
def chromecast_command():
    data = {}
    if json_request := request.get_json():
        if chromecast_cmd_id := json_request.get("chromecast_cmd_id"):
            bh.send_chromecast_cmd(CommandList(chromecast_cmd_id))
    return data, 200


@main_bp.route(APIEndpoints.CONNECT_LOCAL_PLAYER.value, methods=["POST"])
def connect_local_player():
    """Switch UI to local HTML5 playback (disconnect Chromecast if connected)."""
    bh.disconnect_chromecast()
    return {"player": "local", "chromecast_id": None}, 200
