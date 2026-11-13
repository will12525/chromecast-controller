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
            ), mock.patch(
                "app.utils.clone_manifest.current_system_mode",
                return_value=SystemMode.CLIENT,
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


def _show_catalog():
    def episode(src, show_id=1):
        return {
            "content_src": src,
            "title": src,
            "img_src": "",
            "show_id": show_id,
            "show_img_src": "tv_shows/Show/Show.png",
            "show_title": "Show",
        }

    ep1 = episode("tv_shows/Show/Show - s01e01.mp4")
    ep2 = episode("tv_shows/Show/Show - s01e02.mp4")
    ep3 = episode("tv_shows/Show/Show - s02e01.mp4")
    movie = {
        "content_src": "movies/Title (2010).mp4",
        "title": "Title",
        "img_src": "movies/Title (2010).png",
        "show_id": None,
        "show_img_src": "",
        "kind": "movie",
    }
    return {
        "shows": {
            1: {
                "container_id": 1,
                "title": "Show",
                "img_src": "tv_shows/Show/Show.png",
                "img_url": "",
                "seasons": [
                    {"container_id": 2, "title": "Season 1", "episodes": [ep1, ep2]},
                    {"container_id": 3, "title": "Season 2", "episodes": [ep3]},
                ],
            }
        },
        "movies": [],
        "books": [],
        "content_by_src": {
            ep1["content_src"]: ep1,
            ep2["content_src"]: ep2,
            ep3["content_src"]: ep3,
            movie["content_src"]: movie,
        },
    }


class TestClonePlan(unittest.TestCase):
    def test_show_season_and_episode_expansion(self):
        from app.utils import clone_manifest

        catalog = _show_catalog()
        show_plan = clone_manifest.build_clone_plan(
            {"selections": [{"kind": "show", "container_id": 1}], "exclude": [], "remove": [], "inventory": []},
            catalog,
        )
        show_files = {row["content_src"] for row in show_plan["download"]}
        self.assertEqual(len(show_files), 3)
        self.assertEqual(show_plan["covers"], [{"img_src": "tv_shows/Show/Show.png", "kind": "image"}])

        season_plan = clone_manifest.build_clone_plan(
            {"selections": [{"kind": "season", "container_id": 2}], "exclude": [], "remove": [], "inventory": []},
            catalog,
        )
        self.assertEqual(
            {row["content_src"] for row in season_plan["download"]},
            {
                "tv_shows/Show/Show - s01e01.mp4",
                "tv_shows/Show/Show - s01e02.mp4",
            },
        )

        one = clone_manifest.build_clone_plan(
            {
                "selections": [{"kind": "episode", "content_src": "tv_shows/Show/Show - s02e01.mp4"}],
                "exclude": [],
                "remove": [],
                "inventory": [],
            },
            catalog,
        )
        self.assertEqual(
            [row["content_src"] for row in one["download"]],
            ["tv_shows/Show/Show - s02e01.mp4"],
        )
        self.assertEqual(one["covers"][0]["img_src"], "tv_shows/Show/Show.png")

    def test_exclude_drops_episode_and_empty_manifest_downloads_nothing(self):
        from app.utils import clone_manifest

        catalog = _show_catalog()
        plan = clone_manifest.build_clone_plan(
            {
                "selections": [{"kind": "show", "container_id": 1}],
                "exclude": ["tv_shows/Show/Show - s01e02.mp4"],
                "remove": [],
                "inventory": [],
            },
            catalog,
        )
        srcs = {row["content_src"] for row in plan["download"]}
        self.assertNotIn("tv_shows/Show/Show - s01e02.mp4", srcs)
        self.assertEqual(len(srcs), 2)
        empty = clone_manifest.build_clone_plan(
            {"selections": [], "exclude": [], "remove": [], "inventory": []},
            catalog,
        )
        self.assertEqual(empty["download"], [])
        self.assertEqual(empty["covers"], [])

    def test_last_episode_removal_includes_show_cover_and_movie_cover(self):
        from app.utils import clone_manifest

        catalog = _show_catalog()
        plan = clone_manifest.build_clone_plan(
            {
                "selections": [],
                "exclude": ["tv_shows/Show/Show - s01e01.mp4"],
                "remove": ["tv_shows/Show/Show - s01e01.mp4"],
                "inventory": [{"content_src": "tv_shows/Show/Show - s01e01.mp4"}],
            },
            catalog,
        )
        self.assertIn("tv_shows/Show/Show - s01e01.mp4", plan["delete"])
        self.assertIn("tv_shows/Show/Show.png", plan["delete"])

        movie = clone_manifest.build_clone_plan(
            {
                "selections": [],
                "exclude": [],
                "remove": ["movies/Title (2010).mp4"],
                "inventory": [{"content_src": "movies/Title (2010).mp4"}],
            },
            catalog,
        )
        self.assertIn("movies/Title (2010).mp4", movie["delete"])
        self.assertIn("movies/Title (2010).png", movie["delete"])

    def test_media_url_encodes_space_and_ampersand(self):
        from app.utils import clone_manifest

        url = clone_manifest.media_http_url(
            "http://192.168.1.175:8000/",
            "/tv_shows/Timon & Pumbaa/Timon & Pumbaa - s1e5.mp4",
        )
        self.assertEqual(
            url,
            "http://192.168.1.175:8000/tv_shows/Timon%20%26%20Pumbaa/"
            "Timon%20%26%20Pumbaa%20-%20s1e5.mp4",
        )
        self.assertEqual(clone_manifest.media_http_url("", "tv_shows/a.mp4"), "")

    def test_plan_pairs_absolute_url_with_catalog_path(self):
        from app.utils import clone_manifest

        catalog = _show_catalog()
        for row in catalog["content_by_src"].values():
            row["content_url"] = "http://192.168.1.175:8000/"
        plan = clone_manifest.build_clone_plan(
            {
                "selections": [{"kind": "episode", "content_src": "tv_shows/Show/Show - s02e01.mp4"}],
                "exclude": [],
                "remove": [],
                "inventory": [],
            },
            catalog,
        )
        self.assertEqual(
            [row["path"] for row in plan["urls"]],
            ["tv_shows/Show/Show - s02e01.mp4", "tv_shows/Show/Show.png"],
        )
        video = plan["urls"][0]
        self.assertEqual(
            video["url"],
            "http://192.168.1.175:8000/tv_shows/Show/Show%20-%20s02e01.mp4",
        )
        self.assertTrue(plan["urls"][1]["url"].endswith("/tv_shows/Show/Show.png"))

    def test_unlink_is_client_only_and_refuses_escape(self):
        from app.utils import clone_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            target = root / "movies" / "Title (2010).mp4"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"video")
            outside = pathlib.Path(tmp).parent / "escape-me.mp4"
            roots = [{"content_src": str(root)}]
            with mock.patch.object(clone_manifest, "current_system_mode", return_value=SystemMode.SERVER):
                self.assertFalse(clone_manifest.unlink_media_file(target))
            self.assertTrue(target.exists())
            self.assertFalse(clone_manifest.delete_relative("../escape-me.mp4", roots))
            with mock.patch.object(clone_manifest, "current_system_mode", return_value=SystemMode.CLIENT):
                self.assertTrue(clone_manifest.delete_relative("movies/Title (2010).mp4", roots))
            self.assertFalse(target.exists())
            self.assertFalse(outside.exists())


class _StreamResponse:
    def __init__(self, status, body, headers):
        self.status_code = status
        self.headers = headers
        self._body = body

    def iter_content(self, chunk_size=1024):
        yield self._body

    def close(self):
        return None


class TestMediaUrlDownload(unittest.TestCase):
    def test_stream_renames_when_size_matches(self):
        body = b"hello-media"
        with tempfile.TemporaryDirectory() as tmp:
            dest = pathlib.Path(tmp) / "clip.mp4"
            response = _StreamResponse(200, body, {"Content-Length": str(len(body))})
            with mock.patch.object(content_transfer.requests, "get", return_value=response) as get:
                ok, err = content_transfer.download_media_url("http://192.168.1.175:8000/clip.mp4", dest)
            self.assertTrue(ok, err)
            self.assertEqual(dest.read_bytes(), body)
            self.assertFalse((dest.parent / (dest.name + ".partial")).exists())
            self.assertNotIn("Range", get.call_args.kwargs["headers"])

    def test_resume_sends_range_and_appends(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = pathlib.Path(tmp) / "clip.mp4"
            partial = dest.with_name(dest.name + ".partial")
            partial.write_bytes(b"hel")
            response = _StreamResponse(
                206,
                b"lo-media",
                {"Content-Range": "bytes 3-10/11", "Content-Length": "8"},
            )
            with mock.patch.object(content_transfer.requests, "get", return_value=response) as get:
                ok, err = content_transfer.download_media_url("http://192.168.1.175:8000/clip.mp4", dest)
            self.assertTrue(ok, err)
            self.assertEqual(dest.read_bytes(), b"hello-media")
            self.assertEqual(get.call_args.kwargs["headers"]["Range"], "bytes=3-")

    def test_bad_url_and_refused_delete_do_not_stop_the_next_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            body = b"ok"
            response = _StreamResponse(200, body, {"Content-Length": "2"})
            db = mock.Mock()
            db.get_all_content_directory_info.return_value = [{"content_src": str(root)}]
            db.close.return_value = None
            plan = {
                "delete": ["../nope.mp4"],
                "urls": [
                    {"url": "", "path": "tv_shows/missing.mp4"},
                    {"url": "http://192.168.1.175:8000/tv_shows/ok.mp4", "path": "tv_shows/ok.mp4"},
                ],
            }
            with mock.patch.object(content_transfer, "_open_db", return_value=db), mock.patch.object(
                content_transfer.requests, "get", return_value=response
            ):
                failures, removed, changed = content_transfer._apply_clone_plan(plan)
            self.assertTrue(any("no media url for tv_shows/missing.mp4" in item for item in failures))
            self.assertTrue(any("refusing delete" in item for item in failures))
            self.assertEqual((root / "tv_shows" / "ok.mp4").read_bytes(), body)
            self.assertEqual(removed, [])
            self.assertTrue(changed)


class TestCloneSync(unittest.TestCase):
    def test_unreachable_sync_sets_pending_and_does_not_download(self):
        from app.utils import clone_manifest

        with tempfile.TemporaryDirectory() as tmp:
            pending = pathlib.Path(tmp) / "pending.json"
            with mock.patch.object(clone_manifest, "PENDING_PATH", pending), mock.patch.object(
                content_transfer, "load_json_file_content",
                return_value={"mode": "CLIENT", "server_url": "http://down.example"},
            ), mock.patch.object(content_transfer.ServerConnection, "connect", return_value=False):
                result = content_transfer.run_client_contact(apply=True)
                decision = clone_manifest.interpret_contact(result, True, source="sync")
                if decision["set_pending"]:
                    clone_manifest.set_pending()
            self.assertEqual(result["status"], "skipped")
            self.assertFalse(result["applied"])
            self.assertTrue(pending.is_file())

    def test_pending_clears_only_after_success(self):
        from app.utils import clone_manifest

        failed = clone_manifest.interpret_contact(
            {"status": "error", "applied": False, "message": "download failed"},
            True,
            source="scan",
        )
        self.assertTrue(failed["set_pending"])
        self.assertFalse(failed["clear_pending"])
        done = clone_manifest.interpret_contact(
            {"status": "ok", "applied": True}, True, source="scan"
        )
        self.assertTrue(done["clear_pending"])
        self.assertTrue(done["rescan"])
        partial = clone_manifest.interpret_contact(
            {"status": "error", "applied": False, "changed": True, "message": "no media url for a.mp4"},
            True,
            source="sync",
        )
        self.assertTrue(partial["set_pending"])
        self.assertFalse(partial["clear_pending"])
        self.assertTrue(partial["rescan"])
        with tempfile.TemporaryDirectory() as tmp:
            pending = pathlib.Path(tmp) / "pending.json"
            with mock.patch.object(clone_manifest, "PENDING_PATH", pending), mock.patch.object(
                clone_manifest, "current_system_mode", return_value=SystemMode.CLIENT
            ):
                clone_manifest.set_pending()
                self.assertTrue(clone_manifest.pending_is_set())
                clone_manifest.clear_pending()
                self.assertFalse(clone_manifest.pending_is_set())

    def test_scan_without_pending_does_not_download(self):
        from app.utils import clone_manifest

        def _connect(self, client_id=None, display_name=None):
            self.server_token = "token"
            self.client_id = client_id
            return True

        with mock.patch.object(
            content_transfer, "load_json_file_content",
            return_value={"mode": "CLIENT", "server_url": "http://server.example"},
        ), mock.patch.object(
            content_transfer.ServerConnection, "connect", _connect
        ), mock.patch.object(
            content_transfer.ServerConnection, "report_inventory", return_value=True
        ), mock.patch.object(
            content_transfer, "_open_db"
        ) as open_db, mock.patch.object(
            content_transfer.ServerConnection, "fetch_clone_plan"
        ) as fetch_plan:
            open_db.return_value.get_all_content_paths.return_value = []
            open_db.return_value.close.return_value = None
            result = content_transfer.run_client_contact(apply=False)
        fetch_plan.assert_not_called()
        self.assertEqual(result["message"], "Scan complete (inventory updated)")
        decision = clone_manifest.interpret_contact(result, False, source="scan")
        self.assertFalse(decision["set_pending"])
        self.assertIn("inventory updated", decision["message"])

    def test_cast_routes_hidden_when_client(self):
        from flask import Flask

        from app.routes import register_blueprints, shared

        app = Flask(__name__, template_folder="../app/templates")
        register_blueprints(app)
        with mock.patch.object(shared, "system_mode", SystemMode.CLIENT):
            client = app.test_client()
            response = client.post("/get_chromecast_list")
        self.assertEqual(response.status_code, 404)

    def test_chromecast_handler_not_started_for_client(self):
        from app.utils.backend_handler import BackEndHandler

        saved = BackEndHandler._chromecast_handler
        BackEndHandler._chromecast_handler = None
        try:
            with mock.patch("app.utils.backend_handler._is_server_mode", return_value=False):
                self.assertIsNone(BackEndHandler.get_chromecast())
            self.assertIsNone(BackEndHandler._chromecast_handler)
        finally:
            BackEndHandler._chromecast_handler = saved


if __name__ == "__main__":
    unittest.main()
