"""
CLIENT/SERVER media sync helpers.

Hardening (Phase 2):
- No interactive input() on download failures (safe for headless/CI)
- Request timeouts and null-safe list handling
- Handshake tokens from config/env with LAN defaults
- Clear error_code on auth failure for server endpoints
"""
import os
import pathlib

import requests
from flask import send_file

from app.utils.common import SystemMode, get_file_hash, build_tv_show_output_path, get_gb
from app.utils.config_file_handler import load_json_file_content
from app.database.db_getter import DBHandler

# Default LAN handshake (override via config or env — do not rely on secrecy alone)
_DEFAULT_HANDSHAKE_SECRET = "Hello world!"
_DEFAULT_HANDSHAKE_RESPONSE = "LEONARD IS THE COOLEST DINOSAUR"

# Back-compat module-level names (tests / older callers)
HANDSHAKE_SECRET = _DEFAULT_HANDSHAKE_SECRET
HANDSHAKE_RESPONSE = _DEFAULT_HANDSHAKE_RESPONSE

# GB
FILE_SIZE_LIMIT = 2
# Seconds — avoid hanging client scan on a dead server
REQUEST_TIMEOUT = 30


def _load_transfer_config():
    """Resolve handshake tokens from env, then config.json, then defaults."""
    cfg = {}
    try:
        cfg = load_json_file_content() or {}
    except Exception as e:
        print(f"content_transfer: config load failed: {e}")
    secret = (
        os.environ.get("TRANSFER_HANDSHAKE_SECRET")
        or cfg.get("transfer_handshake_secret")
        or _DEFAULT_HANDSHAKE_SECRET
    )
    response = (
        os.environ.get("TRANSFER_HANDSHAKE_RESPONSE")
        or cfg.get("transfer_handshake_response")
        or _DEFAULT_HANDSHAKE_RESPONSE
    )
    return secret, response


def get_handshake_secret():
    secret, _ = _load_transfer_config()
    return secret


def get_handshake_response():
    _, response = _load_transfer_config()
    return response


def server_request(url, json_data, timeout=REQUEST_TIMEOUT):
    """POST JSON to server; return parsed body or None on failure."""
    try:
        response = requests.post(url, json=json_data, timeout=timeout)
        response.raise_for_status()
        if not response.content:
            return {}
        return response.json()
    except (requests.JSONDecodeError, requests.RequestException, Exception) as e:
        print(f"content_transfer server_request error ({url}): {e}")
        return None


def find_existing_img_dir(img_src, media_directory_info):
    if not img_src:
        return None
    for media_directory in media_directory_info or []:
        output_file = pathlib.Path(
            f"{media_directory.get('content_src')}{img_src}"
        ).resolve()
        if output_file.parent.exists():
            return output_file
    return None


def find_existing_img_path(img_src, media_directory_info):
    if not img_src:
        return None
    for media_directory in media_directory_info or []:
        output_file = pathlib.Path(
            f"{media_directory.get('content_src')}{img_src}"
        ).resolve()
        if output_file.exists():
            return output_file
    return None


def _path_is_under_media_roots(path, media_directory_info):
    """Reject writes outside configured media roots (path traversal guard)."""
    try:
        resolved = pathlib.Path(path).resolve()
    except Exception:
        return False
    for media_directory in media_directory_info or []:
        root = media_directory.get("content_src")
        if not root:
            continue
        try:
            root_path = pathlib.Path(root).resolve()
            resolved.relative_to(root_path)
            return True
        except ValueError:
            continue
    return False


class ServerConnection:
    def __init__(self, base_url):
        self.base_url = (base_url or "").rstrip("/")
        self.server_token = None
        self.content_srcs = None
        self.img_srcs = None
        self.last_error = None
        self.client_id = None
        self.manifest = None

    def connect(self, client_id=None, display_name=None):
        if not self.base_url:
            self.last_error = "server_url missing from config"
            print(f"content_transfer: {self.last_error}")
            return False
        secret = get_handshake_secret()
        payload = {"server_token": secret}
        self.client_id = client_id
        if client_id:
            payload["client_id"] = client_id
            payload["display_name"] = display_name or client_id
        search_response_data = server_request(
            f"{self.base_url}/server_connect", payload
        )
        if search_response_data and search_response_data.get("server_token"):
            self.server_token = search_response_data.get("server_token")
            self.manifest = search_response_data.get("manifest")
            self.last_error = None
            return True
        self.last_error = f"handshake failed: {search_response_data}"
        print(f"content_transfer: {self.last_error}")
        return False

    def fetch_clone_plan(self):
        if not self.connected():
            self.last_error = "not connected"
            return None
        data = server_request(
            f"{self.base_url}/request_clone_plan",
            {"server_token": self.server_token, "client_id": self.client_id},
        )
        if not data or data.get("error_code") != 200:
            self.last_error = f"clone plan rejected: {data}"
            return None
        return {
            "download": data.get("download") or [],
            "covers": data.get("covers") or [],
            "delete": data.get("delete") or [],
        }

    def report_inventory(self, client_id, inventory, removed=None):
        if not self.connected():
            self.last_error = "not connected"
            return False
        data = server_request(
            f"{self.base_url}/client_inventory",
            {
                "server_token": self.server_token,
                "client_id": client_id,
                "inventory": inventory or [],
                "removed": removed or [],
            },
        )
        if not data or data.get("error_code") != 200:
            self.last_error = f"inventory rejected: {data}"
            return False
        return True

    def connected(self):
        return self.server_token is not None

    def request_server_content(self):
        if not self.connected():
            self.last_error = "not connected"
            return False
        path_request_response_data = server_request(
            f"{self.base_url}/request_all_content",
            {"server_token": self.server_token},
        )
        if not path_request_response_data:
            self.last_error = "request_all_content failed"
            self.content_srcs = []
            self.img_srcs = []
            return False
        if path_request_response_data.get("error_code") == 200:
            self.content_srcs = path_request_response_data.get("content_srcs") or []
            self.img_srcs = path_request_response_data.get("img_srcs") or []
            return True
        self.last_error = f"request_all_content rejected: {path_request_response_data}"
        self.content_srcs = []
        self.img_srcs = []
        print(f"content_transfer: {self.last_error}")
        return False

    def check_for_missing_content(self):
        if not self.content_srcs:
            return
        db_connection = DBHandler()
        db_connection.open()
        try:
            for content_src in self.content_srcs:
                if not content_src:
                    continue
                if not db_connection.check_if_content_src_exists(content_src):
                    content_src["transfer"] = True
        finally:
            db_connection.close()

    def request_missing_content(self):
        if not self.content_srcs:
            return
        for content_src in self.content_srcs:
            if not content_src or not content_src.get("transfer"):
                continue
            try:
                content_src_path = pathlib.Path(content_src.get("content_src") or "").name
                if not content_src_path:
                    print(f"content_transfer: skip empty content_src {content_src}")
                    continue
                output_path = build_tv_show_output_path(content_src_path)
                if not output_path:
                    print(f"content_transfer: no output path for {content_src_path}")
                    continue
                output_file = pathlib.Path(output_path)
                print(f"{content_src} -> {output_file}")
                self.request_file(content_src, output_file, "request_content")
            except FileExistsError as e:
                print(f"ERROR: downloading file: {e}")
            except Exception as e:
                print(f"ERROR: downloading file (unexpected): {e}")

    def process_img_files(self):
        if not self.img_srcs:
            return
        db_connection = DBHandler()
        db_connection.open()
        try:
            media_directory_info = db_connection.get_all_content_directory_info()
        finally:
            db_connection.close()

        for content_src in self.img_srcs:
            if not content_src or not media_directory_info:
                continue
            if output_file := find_existing_img_dir(
                content_src.get("img_src"), media_directory_info
            ):
                print(f"{content_src} -> {output_file}")
                self.request_file(content_src, output_file, "request_image")
            else:
                print(f"Destination Doesn't exist: {content_src}")

    def request_file(self, content_src, file_destination, server_endpoint):
        """
        Download a file from the server.

        Returns:
            bool: True if written and md5 matched (or no md5 header); False on failure.
        """
        if not self.connected():
            print("content_transfer: request_file while not connected")
            return False
        if not file_destination:
            return False

        payload = dict(content_src or {})
        payload["server_token"] = self.server_token
        dest = pathlib.Path(file_destination)
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            response = requests.post(
                f"{self.base_url}/{server_endpoint}",
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            expected_md5 = response.headers.get("md5sum")
            with open(dest, "wb") as f:
                f.write(response.content)
            if expected_md5:
                md5sum = get_file_hash(dest)
                if expected_md5 != md5sum:
                    print(
                        f"ERROR: md5 mismatch for {dest}: "
                        f"server={expected_md5} local={md5sum} — removing corrupt file"
                    )
                    _unlink_client_file(dest)
                    return False
            print(f"INFO: File downloaded successfully! {dest}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"ERROR: File request failed: {e}")
            _unlink_client_file(dest)
            return False
        except OSError as e:
            print(f"ERROR: File write failed: {e}")
            _unlink_client_file(dest)
            return False


def _unlink_client_file(path):
    """Remove a partial download. No-op unless mode is CLIENT."""
    from app.utils.clone_manifest import current_system_mode

    if current_system_mode() != SystemMode.CLIENT:
        return False
    pathlib.Path(path).unlink(missing_ok=True)
    return True


def _open_db():
    db_connection = DBHandler()
    db_connection.open()
    return db_connection


# CLIENT
def query_server():
    """Contact the server without copying files (inventory refresh)."""
    return run_client_contact(apply=False)


def run_client_contact(apply=False):
    """Handshake, optionally apply the manifest, and report inventory.

    apply=False refreshes last-seen and inventory only.
    apply=True deletes queued files and downloads missing selections.
    A failed apply leaves the caller responsible for the pending flag.
    """
    from app.utils import clone_manifest

    cfg = load_json_file_content() or {}
    server_url = cfg.get("server_url")
    if not server_url:
        print("content_transfer: server_url not set; skip query_server")
        return {"status": "error", "message": "server_url not set", "applied": False}

    client_id, display_name = clone_manifest.client_identity()
    server_connection = ServerConnection(server_url)
    if not server_connection.connect(client_id, display_name):
        return {
            "status": "skipped",
            "message": "server unreachable",
            "applied": False,
        }

    applied = False
    removed = []
    if apply:
        plan = server_connection.fetch_clone_plan()
        if plan is None:
            return {
                "status": "error",
                "message": server_connection.last_error or "clone plan failed",
                "applied": False,
            }
        applied, removed = _apply_clone_plan(server_connection, plan)
        if not applied:
            return {
                "status": "error",
                "message": server_connection.last_error or "sync did not finish",
                "applied": False,
            }

    db_connection = _open_db()
    try:
        inventory = clone_manifest.local_inventory(db_connection)
    finally:
        db_connection.close()
    if not server_connection.report_inventory(client_id, inventory, removed):
        return {
            "status": "error",
            "message": server_connection.last_error or "inventory report failed",
            "applied": applied,
        }
    if apply:
        return {"status": "ok", "message": "Sync complete", "applied": True}
    return {"status": "ok", "message": "Scan complete (inventory updated)", "applied": False}


def _apply_clone_plan(server_connection, plan):
    """Download missing files and delete queued ones. Returns (ok, removed paths)."""
    from app.utils import clone_manifest

    db_connection = _open_db()
    try:
        media_dirs = db_connection.get_all_content_directory_info()
    finally:
        db_connection.close()

    removed = []
    for rel in plan.get("delete") or []:
        dest = clone_manifest.destination_for(rel, media_dirs)
        if dest is None:
            server_connection.last_error = f"refusing delete outside media roots: {rel}"
            return False, removed
        if not dest.exists():
            removed.append(rel)
            continue
        if not clone_manifest.unlink_media_file(dest):
            server_connection.last_error = f"delete skipped: {rel}"
            return False, removed
        removed.append(rel)

    for item in plan.get("download") or []:
        rel = item.get("content_src")
        dest = clone_manifest.destination_for(rel, media_dirs)
        if dest is None:
            server_connection.last_error = f"no destination for {rel}"
            return False, removed
        if dest.exists():
            continue
        if not server_connection.request_file(
            {"content_src": rel}, dest, "request_content"
        ):
            server_connection.last_error = server_connection.last_error or f"download failed: {rel}"
            return False, removed

    for cover in plan.get("covers") or []:
        rel = cover.get("img_src")
        dest = clone_manifest.destination_for(rel, media_dirs)
        if dest is None or dest.exists():
            continue
        if not server_connection.request_file({"img_src": rel}, dest, "request_image"):
            server_connection.last_error = server_connection.last_error or f"cover failed: {rel}"
            return False, removed
    return True, removed


# SERVER
def new_client_connection(system_mode, server_token, data, client_id=None, display_name=None):
    if system_mode == SystemMode.CLIENT:
        data["error"] = "not a server"
        data["error_code"] = 400
    elif system_mode == SystemMode.SERVER and server_token == get_handshake_secret():
        data["server_token"] = get_handshake_response()
        data["error_code"] = 200
        data.pop("error", None)
        if client_id:
            from app.utils import clone_manifest

            manifest = clone_manifest.upsert_client(client_id, display_name)
            data["manifest"] = manifest
            data["client_id"] = manifest.get("client_id")
    else:
        data["error"] = "System in unknown mode"
        data["error_code"] = 400


# SERVER
def request_all_content(server_token, data):
    if server_token != get_handshake_response():
        data["error"] = "unauthorized"
        data["error_code"] = 401
        data["content_srcs"] = []
        data["img_srcs"] = []
        return
    db_connection = DBHandler()
    db_connection.open()
    try:
        data["content_srcs"] = db_connection.get_all_content_paths()
        data["img_srcs"] = db_connection.get_all_image_paths()
        data["error_code"] = 200
    finally:
        db_connection.close()


def request_file(output_file, data):
    output_file = pathlib.Path(output_file) if output_file else None
    if output_file and os.path.exists(output_file):
        try:
            if get_gb(os.path.getsize(output_file)) > FILE_SIZE_LIMIT:
                data["error"] = "File is too large"
                data["error_code"] = 413
            else:
                md5sum = get_file_hash(output_file)
                mimetype = "video/mp4"
                suffix = output_file.suffix.lower()
                if suffix == ".png":
                    mimetype = "image/png"
                elif suffix in (".jpeg", ".jpg"):
                    mimetype = "image/jpeg"
                elif suffix == ".mp4":
                    mimetype = "video/mp4"
                response = send_file(output_file, as_attachment=True, mimetype=mimetype)
                response.headers["md5sum"] = md5sum
                return response
        except FileNotFoundError:
            data["error"] = "File not found"
            data["error_code"] = 404
    else:
        data["error"] = "File not found"
        data["error_code"] = 404


# SERVER
def request_image(json_request, data):
    if json_request.get("server_token") != get_handshake_response():
        data["error"] = "unauthorized"
        data["error_code"] = 401
        return
    db_connection = DBHandler()
    db_connection.open()
    try:
        media_directory_info = db_connection.get_all_content_directory_info()
    finally:
        db_connection.close()
    if output_file := find_existing_img_path(json_request.get("img_src"), media_directory_info):
        return request_file(output_file, data)
    data["error"] = f"Failed to find file {json_request.get('img_src')}"
    data["error_code"] = 404


# SERVER
def request_content(json_request, data):
    if json_request.get("server_token") != get_handshake_response():
        data["error"] = "unauthorized"
        data["error_code"] = 401
        return
    content_id = json_request.get("id")
    content_src = json_request.get("content_src")
    if not content_id and content_src:
        db_connection = DBHandler()
        db_connection.open()
        try:
            row = db_connection.get_data_from_db_first_result(
                "SELECT id FROM content WHERE content_src = :content_src;",
                {"content_src": content_src},
            )
        finally:
            db_connection.close()
        content_id = row.get("id") if row else None
    if not content_id:
        data["error"] = "content id required"
        data["error_code"] = 400
        return
    db_connection = DBHandler()
    db_connection.open()
    try:
        content_data = db_connection.get_content_info(content_id) or {}
        media_directory_info = db_connection.get_all_content_directory_info()
    finally:
        db_connection.close()
    if output_file := content_data.get("path"):
        output_path = pathlib.Path(output_file)
        # Only serve files under configured media roots
        if not _path_is_under_media_roots(output_path, media_directory_info):
            data["error"] = "path outside media roots"
            data["error_code"] = 403
            return
        return request_file(output_path, data)
    data["error"] = f"Failed to find file with provided ID: {content_id}"
    data["error_code"] = 404
