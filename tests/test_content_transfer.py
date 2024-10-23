import json
from unittest import TestCase
import os
import backend_handler

import content_transfer
import config_file_handler
from . import pytest_mocks


class TestContentTransferSetup(TestCase):
    DB_PATH = "media_metadata.db"

    def setUp(self) -> None:
        pytest_mocks.patch_get_file_hash(self)
        pytest_mocks.patch_get_ffmpeg_metadata(self)
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)
        # if os.path.exists(self.DB_PATH):
        #     os.remove(self.DB_PATH)
        # assert not os.path.exists(self.DB_PATH)
        backend_handler.setup_db()
        assert os.path.exists(self.DB_PATH)


class TestConnectServer(TestContentTransferSetup):
    def test_server_connect_unknown(self):
        data = {}
        content_transfer.new_client_connection(content_transfer.SystemMode.SERVER, "", data)
        assert data["error_code"] == 400
        assert data["error"] == "System in unknown mode"
        print(data)

    def test_server_connect_not_a_server(self):
        data = {}
        content_transfer.new_client_connection(content_transfer.SystemMode.CLIENT, "", data)
        assert data["error_code"] == 400
        assert data["error"] == "not a server"
        print(data)

    def test_server_connect_valid(self):
        data = {}
        content_transfer.new_client_connection(content_transfer.SystemMode.SERVER, content_transfer.HANDSHAKE_SECRET,
                                               data)
        assert data["error_code"] == 200
        assert data["server_token"] == content_transfer.HANDSHAKE_RESPONSE
        print(data)


class TestQueryServer(TestContentTransferSetup):
    def test_connect_to_server(self):
        server_connection = content_transfer.ServerConnection(
            config_file_handler.load_json_file_content().get("server_url"))
        server_connection.connect()
        assert server_connection.connected()
        assert server_connection.server_token == content_transfer.HANDSHAKE_RESPONSE

    def test_request_server_content(self):
        server_connection = content_transfer.ServerConnection(
            config_file_handler.load_json_file_content().get("server_url"))
        server_connection.connect()
        assert server_connection.connected()
        assert server_connection.server_token == content_transfer.HANDSHAKE_RESPONSE
        server_connection.request_server_content()
        assert type(server_connection.content_srcs) is list
        assert type(server_connection.img_srcs) is list
        for item in server_connection.content_srcs:
            assert type(item.get("content_src")) is str
            assert type(item.get("id")) is int
        for item in server_connection.img_srcs:
            assert type(item.get("img_src")) is str
            if item.get("content_src"):
                assert type(item.get("content_src")) is str
                assert type(item.get("content_id")) is int
            elif item.get("container_path"):
                assert type(item.get("container_path")) is str
                assert type(item.get("container_id")) is int
            else:
                assert False

    def test_process_content_files(self):
        server_connection = content_transfer.ServerConnection(
            config_file_handler.load_json_file_content().get("server_url"))
        server_connection.connect()
        assert server_connection.connected()
        server_connection.content_srcs = [
            {'content_src': '/books/The Angel of Indian Lake - Stephen Graham Jones.mp4', 'id': 409},
            {'content_src': '/books/This Is How You Lose the Time War - Amal El-Mohtar and Max Gladstone.mp4',
             'id': 410},
            {'content_src': '/books/Those Across The River - Christopher Buehlman.mp4', 'id': 408},
            {'content_src': '/movies/(500) Days of Summer (2009).mp4', 'id': 96},
            {'content_src': '/movies/10 Cloverfield Lane (2016).mp4', 'id': 59}]
        server_connection.check_for_missing_content()

    def test_query_server(self):
        json_request = {}
        # data = {}
        content_transfer.query_server()
        # assert data["error_code"] == 400
        # assert data["error"] == "System in unknown mode"
        # print(data)

    def test_media_share(self):
        data = {}
        content_transfer.request_all_content(content_transfer.HANDSHAKE_RESPONSE, data)
        # assert data["error_code"] == 400
        # assert data["error"] == "System in unknown mode"
        print(json.dumps(data, indent=4))

    def test_request_image(self):
        data = {}
        content_transfer.request_all_content(content_transfer.HANDSHAKE_RESPONSE, data)
        # assert data["error_code"] == 400
        # assert data["error"] == "System in unknown mode"

        for img_src in data.get("img_srcs"):
            img_src["server_token"] = content_transfer.HANDSHAKE_RESPONSE
            content_transfer.request_image(img_src, data)
        for content_src in data.get("content_srcs"):
            content_src["server_token"] = content_transfer.HANDSHAKE_RESPONSE
            content_transfer.request_content(content_src, data)
        # # assert data["error_code"] == 400
        # # assert data["error"] == "System in unknown mode"
        # print(json.dumps(data, indent=4))
