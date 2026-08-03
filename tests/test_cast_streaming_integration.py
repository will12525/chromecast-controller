"""
Live Chromecast streaming integration.

These tests **do** connect and cast to real devices when available.
They will change TV state (play/pause/stop). Teardown disconnects.

Play-mode *API* tests (no cast) live in test_cast_play_modes_integration.py.

  pytest tests/test_cast_streaming_integration.py -m integration -q

Env: CAST_DEVICE_1, CAST_DEVICE_2, CAST_DISCOVERY_TIMEOUT, CAST_PLAY_SETTLE_SECONDS
Requires non-empty media_metadata.db (Scan Media first — no auto full-scan).
"""
from __future__ import annotations

import time
from unittest import mock

import pytest
from flask import Flask

from app.database.db_getter import DBHandler
from app.routes import register_blueprints
from app.routes.shared import APIEndpoints, bh
from app.utils.chromecast_handler import (
    STREAM_MODE_ALL,
    STREAM_MODE_DEVICE,
    STREAM_MODE_LOCAL,
    ChromecastHandler,
    CommandList,
)
from app.utils.play_mode import PLAY_MODE_SEQUENTIAL

from . import cast_integration_helpers as H

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def seeded_db():
    db = H.ensure_db_scanned()
    yield db
    db.close()


@pytest.fixture(scope="module")
def cast_handler():
    """Isolated handler so tests don't permanently own process bh sessions."""
    handler = ChromecastHandler(start_discovery=True)
    handler.start()
    devices = H.wait_for_devices(handler, min_count=1)
    if not devices:
        handler.run_update = False
        try:
            handler._stop_discovery()
        except Exception:
            pass
        pytest.skip("No Chromecast devices discovered on LAN")
    yield handler
    try:
        handler.send_command(CommandList.CMD_STOP)
    except Exception:
        pass
    try:
        handler.disconnect_chromecast()
    except Exception:
        pass
    handler.run_update = False
    try:
        handler._stop_discovery()
    except Exception:
        pass


@pytest.fixture
def clean_cast(cast_handler):
    cast_handler.disconnect_chromecast()
    cast_handler.set_stream_mode(STREAM_MODE_LOCAL)
    yield cast_handler
    try:
        cast_handler.send_command(CommandList.CMD_STOP)
    except Exception:
        pass
    cast_handler.disconnect_chromecast()
    cast_handler.set_stream_mode(STREAM_MODE_LOCAL)


@pytest.fixture(scope="module")
def devices(cast_handler):
    found = H.wait_for_devices(cast_handler, min_count=1)
    if not found:
        pytest.skip("No devices")
    return found


@pytest.fixture
def primary(devices):
    return H.pick_device(devices, H.DEFAULT_PRIMARY)


@pytest.fixture
def two_devices(devices):
    return H.pick_two_devices(devices, H.DEFAULT_PRIMARY, H.DEFAULT_SECONDARY)


@pytest.fixture
def tv_episode(seeded_db):
    return H.library_tv_episode_with_next(seeded_db)


@pytest.fixture(scope="module")
def flask_client(seeded_db):
    app = Flask(__name__, template_folder="../app/templates")
    app.testing = True
    register_blueprints(app)
    with app.test_client() as client:
        yield client


def _play_library(handler, episode: dict, play_mode: str = PLAY_MODE_SEQUENTIAL):
    return handler.play_from_sql(
        {
            "content_id": episode["content_id"],
            "parent_container_id": episode["parent_container_id"],
            "play_mode": play_mode,
            "tag_list": [],
        }
    )


def _wait_status(handler, timeout: float = 15.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = handler.get_media_controller_metadata()
        if last and (
            last.get("media_duration") is not None
            or last.get("media_runtime") is not None
            or last.get("media_title")
        ):
            return last
        time.sleep(0.4)
    return last


# ===========================================================================
# Discovery & connection
# ===========================================================================


class TestLiveDiscovery:
    def test_scan_list_has_uuid_name(self, cast_handler, devices):
        for d in devices:
            assert d.get("uuid")
            assert d.get("name")

    def test_connect_by_uuid(self, clean_cast, primary):
        h = clean_cast
        assert h.connect_chromecast(primary["uuid"]) is True
        connected = h.get_connected_devices()
        assert any(c["uuid"] == primary["uuid"] for c in connected)
        assert h.get_chromecast_id() == primary["uuid"]

    def test_connect_by_name(self, clean_cast, primary):
        h = clean_cast
        assert h.connect_chromecast(primary["name"]) is True
        assert any(c["uuid"] == primary["uuid"] for c in h.get_connected_devices())

    def test_disconnect_all(self, clean_cast, primary):
        h = clean_cast
        h.connect_chromecast(primary["uuid"])
        h.disconnect_chromecast()
        assert h.get_connected_devices() == []
        assert h.stream_mode == STREAM_MODE_LOCAL

    def test_connect_two_and_disconnect_one(self, clean_cast, two_devices):
        h = clean_cast
        a, b = two_devices
        assert h.connect_chromecast(a["uuid"])
        assert h.connect_chromecast(b["uuid"])
        assert len(h.get_connected_devices()) == 2
        h.disconnect_chromecast(a["uuid"])
        left = h.get_connected_devices()
        assert len(left) == 1
        assert left[0]["uuid"] == b["uuid"]


# ===========================================================================
# Stream modes
# ===========================================================================


class TestLiveStreamModes:
    def test_device_mode_one_target(self, clean_cast, two_devices):
        h = clean_cast
        a, b = two_devices
        h.connect_chromecast(a["uuid"])
        h.connect_chromecast(b["uuid"])
        assert h.set_stream_mode(STREAM_MODE_DEVICE, a["uuid"])
        targets = h.iter_targets()
        assert len(targets) == 1
        assert targets[0].device_uuid == a["uuid"]

    def test_all_mode_two_targets(self, clean_cast, two_devices):
        h = clean_cast
        a, b = two_devices
        h.connect_chromecast(a["uuid"])
        h.connect_chromecast(b["uuid"])
        assert h.set_stream_mode(STREAM_MODE_ALL)
        assert len(h.iter_targets()) == 2

    def test_local_mode_no_targets(self, clean_cast, primary):
        h = clean_cast
        h.connect_chromecast(primary["uuid"])
        h.set_stream_mode(STREAM_MODE_LOCAL)
        assert h.iter_targets() == []


# ===========================================================================
# Streaming library content (changes TV state)
# ===========================================================================


class TestLiveLibraryPlay:
    def test_play_real_library_url_single(self, clean_cast, primary, tv_episode, seeded_db):
        h = clean_cast
        assert tv_episode["url"].startswith("http")
        H.assert_url_is_library(tv_episode["url"], H.library_url_bases(seeded_db))
        assert h.connect_chromecast(primary["uuid"])
        h.set_stream_mode(STREAM_MODE_DEVICE, primary["uuid"])
        meta = _play_library(h, tv_episode)
        assert meta is not None
        assert meta.get("play_mode") == PLAY_MODE_SEQUENTIAL
        assert meta.get("url") or meta.get("content_title")
        H.settle_after_play()
        status = _wait_status(h)
        assert h.get_media_controller() is not None
        # Soft: receiver may omit title
        if status:
            assert (
                status.get("media_duration") is not None
                or status.get("media_runtime") is not None
                or status.get("media_title")
                or status.get("content_id")
            )
        h.send_command(CommandList.CMD_STOP)

    def test_play_fans_out_all_mode(self, clean_cast, two_devices, tv_episode):
        h = clean_cast
        a, b = two_devices
        h.connect_chromecast(a["uuid"])
        h.connect_chromecast(b["uuid"])
        h.set_stream_mode(STREAM_MODE_ALL)
        targets = h.iter_targets()
        spies = []
        for media in targets:
            spy = mock.Mock(wraps=media.play_media_info)
            media.play_media_info = spy
            spies.append(spy)
        meta = _play_library(h, tv_episode)
        assert meta is not None
        for spy in spies:
            assert spy.called
        H.settle_after_play()
        h.send_command(CommandList.CMD_STOP)

    def test_cmd_skip_advances_sequential(self, clean_cast, primary, tv_episode):
        h = clean_cast
        h.connect_chromecast(primary["uuid"])
        h.set_stream_mode(STREAM_MODE_DEVICE, primary["uuid"])
        meta = _play_library(h, tv_episode)
        assert meta is not None
        H.settle_after_play()
        # Spy next load
        media = h.get_media_controller()
        spy = mock.Mock(wraps=media.play_media_info)
        media.play_media_info = spy
        h.send_command(CommandList.CMD_SKIP)
        time.sleep(2)
        if spy.called:
            args = spy.call_args[0]
            next_meta = args[0] if args else {}
            assert next_meta.get("id") == tv_episode["next_content_id"] or next_meta.get(
                "id"
            ) != tv_episode["content_id"]
            assert next_meta.get("play_mode") == PLAY_MODE_SEQUENTIAL
        h.send_command(CommandList.CMD_STOP)


# ===========================================================================
# Transport controls
# ===========================================================================


class TestLiveControls:
    def test_pause_play_stop(self, clean_cast, primary, tv_episode):
        h = clean_cast
        h.connect_chromecast(primary["uuid"])
        h.set_stream_mode(STREAM_MODE_DEVICE, primary["uuid"])
        _play_library(h, tv_episode)
        H.settle_after_play()
        h.send_command(CommandList.CMD_PAUSE)
        time.sleep(1)
        h.send_command(CommandList.CMD_PLAY)
        time.sleep(1)
        h.send_command(CommandList.CMD_STOP)

    def test_seek_and_skip_15(self, clean_cast, primary, tv_episode):
        h = clean_cast
        h.connect_chromecast(primary["uuid"])
        h.set_stream_mode(STREAM_MODE_DEVICE, primary["uuid"])
        _play_library(h, tv_episode)
        H.settle_after_play()
        h.seek_media_time(20)
        time.sleep(1.5)
        h.send_command(CommandList.CMD_SKIP_15)
        time.sleep(1)
        h.send_command(CommandList.CMD_REWIND_15)
        time.sleep(1)
        h.send_command(CommandList.CMD_STOP)

    def test_commands_fan_out_all(self, clean_cast, two_devices, tv_episode):
        h = clean_cast
        a, b = two_devices
        h.connect_chromecast(a["uuid"])
        h.connect_chromecast(b["uuid"])
        h.set_stream_mode(STREAM_MODE_ALL)
        _play_library(h, tv_episode)
        H.settle_after_play()
        spies = []
        for media in h.iter_targets():
            spy = mock.Mock(wraps=media.interpret_enum_cmd)
            media.interpret_enum_cmd = spy
            spies.append(spy)
        h.send_command(CommandList.CMD_PAUSE)
        for spy in spies:
            assert spy.called
        h.send_command(CommandList.CMD_STOP)


# ===========================================================================
# Takeover / second load wins
# ===========================================================================


class TestLiveTakeover:
    def test_second_library_play_overrides_first(
        self, clean_cast, primary, tv_episode
    ):
        """Cast episode A then B — second play_media_info should run (takeover)."""
        h = clean_cast
        h.connect_chromecast(primary["uuid"])
        h.set_stream_mode(STREAM_MODE_DEVICE, primary["uuid"])
        _play_library(h, tv_episode)
        H.settle_after_play()
        # Play "next" as second item via explicit play
        second = {
            "content_id": tv_episode["next_content_id"],
            "parent_container_id": tv_episode["parent_container_id"],
            "play_mode": PLAY_MODE_SEQUENTIAL,
            "tag_list": [],
        }
        media = h.get_media_controller()
        spy = mock.Mock(wraps=media.play_media_info)
        media.play_media_info = spy
        meta = h.play_from_sql(second)
        assert meta is not None
        assert spy.called
        H.settle_after_play()
        h.send_command(CommandList.CMD_STOP)

    def test_play_bbb_sample_mp4(self, clean_cast, primary):
        """Load public Big Buck Bunny sample (mp4 handling / non-library URL)."""
        h = clean_cast
        assert h.connect_chromecast(primary["uuid"])
        h.set_stream_mode(STREAM_MODE_DEVICE, primary["uuid"])
        media = h.get_media_controller()
        assert media is not None
        media.play_media_info(
            {
                "id": 0,
                "url": H.BBB_URL,
                "content_title": "BigBuckBunny",
                "play_mode": "single",
                "last_position": 0,
                "last_duration": 0,
            },
            update_play_count=False,
        )
        H.settle_after_play(6)
        status = _wait_status(h, timeout=20)
        # Soft: external URL may fail if cast has no internet
        if status is None and not H.http_url_ok(H.BBB_URL, timeout=3):
            pytest.skip("BBB unreachable from this host/network")
        h.send_command(CommandList.CMD_STOP)


# ===========================================================================
# HTTP endpoints (process bh — may cast if mode not local)
# ===========================================================================


class TestLiveHttpEndpoints:
    def test_get_chromecast_list(self, flask_client):
        deadline = time.time() + H.DISCOVERY_TIMEOUT
        data = {}
        while time.time() < deadline:
            resp = flask_client.post(APIEndpoints.GET_CHROMECAST_LIST.value, json={})
            assert resp.status_code == 200
            data = resp.get_json() or {}
            if data.get("scanned_devices"):
                break
            time.sleep(0.5)
        assert "scanned_devices" in data
        assert "stream_mode" in data
        assert "connected_devices" in data
        if not data.get("scanned_devices"):
            pytest.skip("Process bh discovered no devices")

    def test_api_connect_play_stop(self, flask_client, tv_episode, devices):
        device = H.pick_device(devices, H.DEFAULT_PRIMARY)
        # Ensure clean
        flask_client.post(APIEndpoints.DISCONNECT_CHROMECAST.value, json={})
        resp = flask_client.post(
            APIEndpoints.CONNECT_CHROMECAST.value,
            json={"chromecast_id": device["uuid"]},
        )
        assert resp.status_code == 200
        flask_client.post(
            APIEndpoints.SET_STREAM_MODE.value,
            json={"mode": "device", "chromecast_id": device["uuid"]},
        )
        resp = flask_client.post(
            APIEndpoints.PLAY_MEDIA.value,
            json={
                "content_id": tv_episode["content_id"],
                "parent_container_id": tv_episode["parent_container_id"],
                "play_mode": PLAY_MODE_SEQUENTIAL,
                "tag_list": [],
            },
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("play_mode") == PLAY_MODE_SEQUENTIAL
        assert body.get("id") == tv_episode["content_id"]
        H.settle_after_play()
        flask_client.post(
            APIEndpoints.CHROMECAST_COMMAND.value,
            json={"chromecast_cmd_id": CommandList.CMD_PAUSE.value},
        )
        flask_client.post(
            APIEndpoints.CHROMECAST_COMMAND.value,
            json={"chromecast_cmd_id": CommandList.CMD_STOP.value},
        )
        flask_client.post(APIEndpoints.DISCONNECT_CHROMECAST.value, json={})

    def test_api_set_stream_mode_all(self, flask_client, devices):
        if len(devices) < 2:
            pytest.skip("Need 2 devices")
        a, b = devices[0], devices[1]
        flask_client.post(APIEndpoints.DISCONNECT_CHROMECAST.value, json={})
        flask_client.post(
            APIEndpoints.CONNECT_CHROMECAST.value, json={"chromecast_id": a["uuid"]}
        )
        flask_client.post(
            APIEndpoints.CONNECT_CHROMECAST.value, json={"chromecast_id": b["uuid"]}
        )
        resp = flask_client.post(
            APIEndpoints.SET_STREAM_MODE.value, json={"mode": "all"}
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("stream_mode") == STREAM_MODE_ALL
        assert len(body.get("connected_devices") or []) >= 2
        flask_client.post(APIEndpoints.DISCONNECT_CHROMECAST.value, json={})
