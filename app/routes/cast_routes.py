"""Chromecast discovery, connection, multi-device stream mode, and transport controls."""
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
                state = bh.get_chromecast_stream_state()
                data = {
                    "chromecast_id": bh.get_chromecast_device_id() or chromecast_id,
                    "chromecast_name": bh.get_chromecast_device_name(),
                    "connected_devices": state.get("connected_devices", []),
                    "stream_mode": state.get("stream_mode"),
                    "active_device_id": state.get("active_device_id"),
                }
    return data, 200


@main_bp.route(APIEndpoints.GET_CHROMECAST_LIST.value, methods=["POST"])
def get_chromecast_list():
    # Full multi-device snapshot + legacy single-device fields.
    # get_scan_list ensures CastBrowser is running and may one-shot scan if empty.
    scanned = bh.get_chromecast_scan_list()
    if not scanned:
        # Explicit refresh path for cold UI open before background thread settles
        bh.chromecast.scan_for_chromecasts()
        scanned = bh.get_chromecast_scan_list()
    state = bh.get_chromecast_stream_state()
    state["scanned_devices"] = scanned
    if state.get("stream_mode") == "local" and not state.get("connected_devices"):
        state["connected_device"] = state.get("connected_device") or "Local"
    return state, 200


@main_bp.route(APIEndpoints.DISCONNECT_CHROMECAST.value, methods=["POST"])
def disconnect_chromecast():
    chromecast_id = None
    if json_request := request.get_json(silent=True):
        chromecast_id = json_request.get("chromecast_id")
    bh.disconnect_chromecast(chromecast_id)
    state = bh.get_chromecast_stream_state()
    return {
        "ok": True,
        "connected_devices": state.get("connected_devices", []),
        "stream_mode": state.get("stream_mode"),
        "connected_device": state.get("connected_device") or "Local",
        "connected_device_id": state.get("connected_device_id"),
    }, 200


@main_bp.route(APIEndpoints.SET_STREAM_MODE.value, methods=["POST"])
def set_stream_mode():
    data = {"ok": False}
    if json_request := request.get_json():
        mode = json_request.get("mode") or "local"
        chromecast_id = json_request.get("chromecast_id")
        ok = bh.set_stream_mode(mode, chromecast_id)
        state = bh.get_chromecast_stream_state()
        data = {
            "ok": ok,
            "stream_mode": state.get("stream_mode"),
            "active_device_id": state.get("active_device_id"),
            "connected_devices": state.get("connected_devices", []),
            "connected_device": state.get("connected_device") or "Local",
            "connected_device_id": state.get("connected_device_id"),
        }
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
    """Switch stream mode to local HTML5 (keeps cast sessions idle unless disconnected)."""
    bh.set_stream_mode("local")
    return {
        "player": "local",
        "chromecast_id": None,
        "stream_mode": "local",
        "connected_device": "Local",
    }, 200
