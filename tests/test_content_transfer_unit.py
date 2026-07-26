"""Unit tests for hardened content_transfer (no live server required)."""
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from app.utils import content_transfer
from app.utils.common import SystemMode


class TestHandshake(unittest.TestCase):
    def test_server_connect_rejects_client_mode(self):
        data = {}
        content_transfer.new_client_connection(SystemMode.CLIENT, "anything", data)
        self.assertEqual(data["error_code"], 400)
        self.assertEqual(data["error"], "not a server")

    def test_server_connect_rejects_bad_token(self):
        data = {}
        content_transfer.new_client_connection(SystemMode.SERVER, "wrong", data)
        self.assertEqual(data["error_code"], 400)

    def test_server_connect_accepts_secret(self):
        data = {}
        content_transfer.new_client_connection(
            SystemMode.SERVER, content_transfer.get_handshake_secret(), data
        )
        self.assertEqual(data["error_code"], 200)
        self.assertEqual(data["server_token"], content_transfer.get_handshake_response())

    def test_handshake_from_env(self):
        with mock.patch.dict(
            os.environ,
            {
                "TRANSFER_HANDSHAKE_SECRET": "sec-test",
                "TRANSFER_HANDSHAKE_RESPONSE": "resp-test",
            },
            clear=False,
        ):
            self.assertEqual(content_transfer.get_handshake_secret(), "sec-test")
            self.assertEqual(content_transfer.get_handshake_response(), "resp-test")
            data = {}
            content_transfer.new_client_connection(SystemMode.SERVER, "sec-test", data)
            self.assertEqual(data["error_code"], 200)
            self.assertEqual(data["server_token"], "resp-test")


class TestAuthOnServerEndpoints(unittest.TestCase):
    def test_request_all_content_unauthorized(self):
        data = {}
        content_transfer.request_all_content("bad-token", data)
        self.assertEqual(data["error_code"], 401)
        self.assertEqual(data["content_srcs"], [])

    def test_request_image_unauthorized(self):
        data = {}
        content_transfer.request_image({"server_token": "nope", "img_src": "/x.jpg"}, data)
        self.assertEqual(data["error_code"], 401)

    def test_request_content_unauthorized(self):
        data = {}
        content_transfer.request_content({"server_token": "nope", "id": 1}, data)
        self.assertEqual(data["error_code"], 401)


class TestServerRequestAndDownload(unittest.TestCase):
    def test_server_request_returns_none_on_failure(self):
        with mock.patch.object(
            content_transfer.requests,
            "post",
            side_effect=content_transfer.requests.RequestException("down"),
        ):
            self.assertIsNone(
                content_transfer.server_request("http://example.invalid/x", {})
            )

    def test_request_file_md5_mismatch_deletes_without_input(self):
        conn = content_transfer.ServerConnection("http://server.example")
        conn.server_token = content_transfer.get_handshake_response()

        with tempfile.TemporaryDirectory() as tmp:
            dest = pathlib.Path(tmp) / "clip.mp4"
            fake_resp = mock.Mock()
            fake_resp.content = b"payload-bytes"
            fake_resp.headers = {"md5sum": "deadbeef"}
            fake_resp.raise_for_status = mock.Mock()

            with mock.patch.object(
                content_transfer.requests, "post", return_value=fake_resp
            ), mock.patch.object(
                content_transfer, "get_file_hash", return_value="cafebabe"
            ):
                ok = conn.request_file({"id": 1}, dest, "request_content")

            self.assertFalse(ok)
            self.assertFalse(dest.exists())

    def test_request_file_success(self):
        conn = content_transfer.ServerConnection("http://server.example")
        conn.server_token = "token"

        with tempfile.TemporaryDirectory() as tmp:
            dest = pathlib.Path(tmp) / "ok.mp4"
            body = b"hello-media"
            fake_resp = mock.Mock()
            fake_resp.content = body
            fake_resp.headers = {"md5sum": "abc"}
            fake_resp.raise_for_status = mock.Mock()

            with mock.patch.object(
                content_transfer.requests, "post", return_value=fake_resp
            ), mock.patch.object(
                content_transfer, "get_file_hash", return_value="abc"
            ):
                ok = conn.request_file({"id": 2}, dest, "request_content")

            self.assertTrue(ok)
            self.assertTrue(dest.exists())
            self.assertEqual(dest.read_bytes(), body)

    def test_query_server_without_url(self):
        with mock.patch.object(
            content_transfer, "load_json_file_content", return_value={"mode": "CLIENT"}
        ):
            result = content_transfer.query_server()
        self.assertEqual(result["status"], "error")
        self.assertIn("server_url", result["message"])

    def test_connect_without_base_url(self):
        conn = content_transfer.ServerConnection("")
        self.assertFalse(conn.connect())
        self.assertFalse(conn.connected())


class TestPathGuard(unittest.TestCase):
    def test_path_under_media_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            nested = root / "movies" / "a.mp4"
            nested.parent.mkdir(parents=True)
            nested.write_bytes(b"x")
            roots = [{"content_src": str(root)}]
            self.assertTrue(
                content_transfer._path_is_under_media_roots(nested, roots)
            )
            outside = pathlib.Path("/tmp/not-under-root-xyz")
            self.assertFalse(
                content_transfer._path_is_under_media_roots(outside, roots)
            )


if __name__ == "__main__":
    unittest.main()
