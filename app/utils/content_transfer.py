import os
import pathlib

import requests
from flask import send_file

from app.utils.common import SystemMode, get_file_hash, build_tv_show_output_path, get_gb
from app.utils.config_file_handler import load_json_file_content
from app.database.db_getter import DBHandler

HANDSHAKE_SECRET = "Hello world!"
HANDSHAKE_RESPONSE = "LEONARD IS THE COOLEST DINOSAUR"
# GB
FILE_SIZE_LIMIT = 2


def server_request(url, json_data):
    try:
        response = requests.post(url, json=json_data)
        return response.json()
    except (requests.JSONDecodeError, Exception) as e:
        print(e)


def find_existing_img_dir(img_src, media_directory_info):
    for media_directory in media_directory_info:
        output_file = pathlib.Path(f"{media_directory.get('content_src')}{img_src}").resolve()
        if output_file.parent.exists():
            return output_file


def find_existing_img_path(img_src, media_directory_info):
    for media_directory in media_directory_info:
        output_file = pathlib.Path(f"{media_directory.get('content_src')}{img_src}").resolve()
        if output_file.exists():
            return output_file


class ServerConnection:
    base_url = ""
    server_token = None
    content_srcs = None
    img_srcs = None

    def __init__(self, base_url):
        self.base_url = base_url

    def connect(self):
        search_response_data = server_request(f"{self.base_url}/server_connect", {"server_token": HANDSHAKE_SECRET})
        if search_response_data and search_response_data.get("server_token"):
            self.server_token = search_response_data.get("server_token")
        else:
            print(search_response_data)

    def connected(self):
        return self.server_token is not None

    def request_server_content(self):
        path_request_response_data = server_request(f"{self.base_url}/request_all_content",
                                                    {"server_token": self.server_token})
        if path_request_response_data.get("error_code") == 200:
            self.content_srcs = path_request_response_data.get("content_srcs")
            self.img_srcs = path_request_response_data.get("img_srcs")

    def check_for_missing_content(self):
        db_connection = DBHandler()
        db_connection.open()
        for content_src in self.content_srcs:
            if not db_connection.check_if_content_src_exists(content_src):
                content_src["transfer"] = True
        db_connection.close()

    def request_missing_content(self):
        for content_src in self.content_srcs:
            if content_src.get("transfer"):
                try:
                    content_src_path = pathlib.Path(content_src.get("content_src")).name
                    if output_file := pathlib.Path(build_tv_show_output_path(content_src_path)):
                        print(f"{content_src} -> {output_file}")
                        self.request_file(content_src, output_file, "request_content")
                except FileExistsError as e:
                    print(f'ERROR: downloading file: {e} ')

    def process_img_files(self):
        db_connection = DBHandler()
        db_connection.open()
        media_directory_info = db_connection.get_all_content_directory_info()
        db_connection.close()

        for content_src in self.img_srcs:
            if media_directory_info:
                if output_file := find_existing_img_dir(content_src.get('img_src'), media_directory_info):
                    print(f"{content_src} -> {output_file}")
                    self.request_file(content_src, output_file, "request_image")
                else:
                    print(f"Destination Doesn't exist: {content_src}")

    def request_file(self, content_src, file_destination, server_endpoint):
        content_src["server_token"] = self.server_token
        try:
            response = requests.post(f"{self.base_url}/{server_endpoint}", json=content_src)
            response.raise_for_status()  # Raise an exception for error responses
            if 'md5sum' in response.headers:
                with open(file_destination, 'wb') as f:
                    f.write(response.content)
                md5sum = get_file_hash(file_destination)
                if response.headers['md5sum'] == md5sum:
                    print(f'INFO: File downloaded successfully! {file_destination}')
                else:
                    print(f"ERROR: {response.headers['md5sum']} != {md5sum}")
                    input("ERROR: File download failed, Press enter to continue...")
                    pathlib.Path(file_destination).unlink(missing_ok=True)
        except requests.exceptions.RequestException as e:
            print(f'ERROR: File request failed: {e} ')


# CLIENT
def query_server():
    server_connection = ServerConnection(load_json_file_content().get("server_url"))
    server_connection.connect()
    if server_connection.connected():
        server_connection.request_server_content()
    if server_connection.content_srcs:
        server_connection.check_for_missing_content()
        server_connection.request_missing_content()
    if server_connection.img_srcs:
        server_connection.process_img_files()


# SERVER
def new_client_connection(system_mode, server_token, data):
    if system_mode == SystemMode.CLIENT:
        data["error"] = "not a server"
        data["error_code"] = 400
    elif system_mode == SystemMode.SERVER and server_token == HANDSHAKE_SECRET:
        data["server_token"] = HANDSHAKE_RESPONSE
        data["error_code"] = 200
    else:
        data["error"] = "System in unknown mode"
        data["error_code"] = 400


# SERVER
def request_all_content(server_token, data):
    if server_token == HANDSHAKE_RESPONSE:
        db_connection = DBHandler()
        db_connection.open()
        data["content_srcs"] = db_connection.get_all_content_paths()
        data["img_srcs"] = db_connection.get_all_image_paths()
        db_connection.close()


def request_file(output_file, data):
    if os.path.exists(output_file):
        try:
            if get_gb(os.path.getsize(output_file)) > FILE_SIZE_LIMIT:
                data["error"] = 'File is too large'
            else:
                md5sum = get_file_hash(output_file)
                mimetype = 'video/mp4'
                if '.png' == output_file.suffix:
                    mimetype = 'image/png'
                elif '.jpeg' == output_file.suffix:
                    mimetype = 'image/jpeg'
                elif '.mp4' == output_file.suffix:
                    mimetype = 'video/mp4'
                response = send_file(output_file, as_attachment=True, mimetype=mimetype)
                response.headers['md5sum'] = md5sum
                return response
        except FileNotFoundError:
            data["error"] = 'File not found'
            data["error_code"] = 404
    else:
        data["error"] = 'File not found'
        data["error_code"] = 404


# SERVER
def request_image(json_request, data):
    if json_request.get("server_token") == HANDSHAKE_RESPONSE:
        db_connection = DBHandler()
        db_connection.open()
        media_directory_info = db_connection.get_all_content_directory_info()
        db_connection.close()
        if output_file := find_existing_img_path(json_request.get('img_src'), media_directory_info):
            return request_file(output_file, data)
        else:
            data["error"] = f"Failed to find file {json_request.get('img_src')}"
            data["error_code"] = 404


# SERVER
def request_content(json_request, data):
    if json_request.get("server_token") == HANDSHAKE_RESPONSE and (content_id := json_request.get("id")):
        db_connection = DBHandler()
        db_connection.open()
        content_data = db_connection.get_content_info(content_id)
        db_connection.close()
        if output_file := content_data.get('path'):
            output_path = pathlib.Path(output_file)
            return request_file(output_path, data)
        else:
            data["error"] = f"Failed to find file with provided ID: {content_id}"
            data["error_code"] = 404
