"""SERVER clone-manifest page and CLIENT sync trigger."""
import traceback

from flask import render_template, request

from app.database.db_getter import DBHandler
from app.routes.shared import APIEndpoints, bh, main_bp, system_mode
from app.utils import clone_manifest, content_transfer
from app.utils.common import SystemMode


def _server_only():
    if system_mode != SystemMode.SERVER:
        return {"error": "not a server"}, 404
    return None


def _open_catalog():
    db_connection = DBHandler()
    db_connection.open()
    try:
        return clone_manifest.catalog_from_db(db_connection)
    finally:
        db_connection.close()


@main_bp.route(APIEndpoints.CLONE.value, methods=["GET"])
def clone_page():
    blocked = _server_only()
    if blocked:
        return blocked
    return render_template(
        "clone.html",
        homepage_url=APIEndpoints.MAIN.value,
        system_mode=system_mode.name,
    )


@main_bp.route(APIEndpoints.CLONE_CLIENTS.value, methods=["GET"])
def clone_clients():
    blocked = _server_only()
    if blocked:
        return blocked
    rows = []
    for manifest in clone_manifest.list_clients():
        rows.append(
            {
                "client_id": manifest.get("client_id"),
                "display_name": manifest.get("display_name"),
                "last_seen": manifest.get("last_seen"),
                "updated_at": manifest.get("updated_at"),
                "active": manifest.get("active"),
            }
        )
    return {"clients": rows}, 200


@main_bp.route(APIEndpoints.CLONE_CATALOG.value, methods=["GET"])
def clone_catalog():
    blocked = _server_only()
    if blocked:
        return blocked
    try:
        catalog = _open_catalog()
    except Exception as e:
        print(traceback.print_exc())
        return {"error": str(e)}, 500
    return clone_manifest.server_tree(catalog), 200


@main_bp.route("/clone/clients/<client_id>", methods=["GET", "POST"])
def clone_client(client_id):
    blocked = _server_only()
    if blocked:
        return blocked
    client_id = clone_manifest.safe_client_id(client_id)
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        manifest = clone_manifest.save_selection(
            client_id,
            body.get("selections") or [],
            body.get("exclude") or [],
            body.get("remove") or [],
        )
        return {"manifest": manifest}, 200
    manifest = clone_manifest.load_manifest(client_id)
    if not manifest:
        return {"error": "unknown client"}, 404
    try:
        catalog = _open_catalog()
    except Exception as e:
        print(traceback.print_exc())
        return {"error": str(e)}, 500
    return {
        "manifest": manifest,
        "active": clone_manifest.is_active(manifest.get("last_seen")),
        "client_tree": clone_manifest.client_tree(catalog, manifest.get("inventory")),
    }, 200


@main_bp.route(APIEndpoints.REQUEST_CLONE_PLAN.value, methods=["POST"])
def request_clone_plan():
    data = {"error_code": 401}
    body = request.get_json(silent=True) or {}
    if body.get("server_token") != content_transfer.get_handshake_response():
        data["error"] = "unauthorized"
        return data, 401
    if system_mode != SystemMode.SERVER:
        data["error"] = "not a server"
        data["error_code"] = 400
        return data, 400
    client_id = clone_manifest.safe_client_id(body.get("client_id"))
    manifest = clone_manifest.load_manifest(client_id) or clone_manifest.empty_manifest(client_id)
    try:
        catalog = _open_catalog()
        plan = clone_manifest.build_clone_plan(manifest, catalog)
    except Exception as e:
        print(traceback.print_exc())
        data["error"] = str(e)
        data["error_code"] = 500
        return data, 500
    data.update(plan)
    data["error_code"] = 200
    data.pop("error", None)
    return data, 200


@main_bp.route(APIEndpoints.CLIENT_INVENTORY.value, methods=["POST"])
def client_inventory():
    data = {"error_code": 401}
    body = request.get_json(silent=True) or {}
    if body.get("server_token") != content_transfer.get_handshake_response():
        data["error"] = "unauthorized"
        return data, 401
    if system_mode != SystemMode.SERVER:
        data["error"] = "not a server"
        data["error_code"] = 400
        return data, 400
    manifest = clone_manifest.store_inventory(
        body.get("client_id"),
        body.get("inventory") or [],
        body.get("removed") or [],
    )
    data["error_code"] = 200
    data["manifest"] = manifest
    return data, 200


@main_bp.route(APIEndpoints.SYNC_MEDIA.value, methods=["POST"])
def sync_media():
    if system_mode != SystemMode.CLIENT:
        return {"error": "not available"}, 404
    return bh.start_client_sync(), 200
