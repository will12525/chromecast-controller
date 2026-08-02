"""Unit tests for Chromecast UUID identity and multi-session handler (no live devices)."""
import unittest
from unittest import mock
from uuid import UUID

from app.utils import chromecast_handler
from app.utils.chromecast_handler import (
    STREAM_MODE_ALL,
    STREAM_MODE_DEVICE,
    STREAM_MODE_LOCAL,
    ChromecastHandler,
    CommandList,
    _as_uuid_str,
    _service_device_info,
)


def _make_handler():
    # Avoid real Zeroconf / browser in unit tests
    return ChromecastHandler(start_discovery=False)


def _mock_cast(uid, name):
    cast = mock.Mock()
    cast.uuid = uid
    cast.name = name
    cast.cast_info = mock.Mock(uuid=uid, friendly_name=name)
    cast.wait = mock.Mock()
    cast.disconnect = mock.Mock()
    cast.media_controller = mock.Mock()
    cast.media_controller.register_status_listener = mock.Mock()
    return cast


class TestUuidHelpers(unittest.TestCase):
    def test_as_uuid_str_from_uuid(self):
        u = UUID("12345678-1234-5678-1234-567812345678")
        self.assertEqual(_as_uuid_str(u), str(u))

    def test_as_uuid_str_from_string(self):
        raw = "12345678-1234-5678-1234-567812345678"
        self.assertEqual(_as_uuid_str(raw), raw)

    def test_as_uuid_str_none(self):
        self.assertIsNone(_as_uuid_str(None))
        self.assertIsNone(_as_uuid_str(""))

    def test_service_device_info(self):
        u = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        service = mock.Mock(uuid=u, friendly_name="Living Room")
        info = _service_device_info(service)
        self.assertEqual(info["uuid"], str(u))
        self.assertEqual(info["name"], "Living Room")

    def test_service_device_info_name_only_fallback(self):
        service = mock.Mock(spec=["friendly_name"])
        service.friendly_name = "Kitchen"
        info = _service_device_info(service)
        self.assertEqual(info["uuid"], "Kitchen")
        self.assertEqual(info["name"], "Kitchen")


class TestScanListShape(unittest.TestCase):
    def test_scan_builds_uuid_name_entries(self):
        handler = _make_handler()
        u1 = UUID("11111111-1111-1111-1111-111111111111")
        u2 = UUID("22222222-2222-2222-2222-222222222222")
        services = [
            mock.Mock(uuid=u1, friendly_name="TV A"),
            mock.Mock(uuid=u2, friendly_name="TV B"),
            mock.Mock(uuid=u1, friendly_name="TV A"),
        ]
        browser = mock.Mock()
        with mock.patch.object(
            chromecast_handler.pychromecast.discovery,
            "discover_chromecasts",
            return_value=(services, browser),
        ):
            handler.scan_for_chromecasts()
        devices = handler.get_scan_list()
        self.assertEqual(len(devices), 2)
        names = {d["name"] for d in devices}
        self.assertEqual(names, {"TV A", "TV B"})


class TestConnectByUuid(unittest.TestCase):
    def test_connect_prefers_uuid(self):
        handler = _make_handler()
        uid = UUID("33333333-3333-3333-3333-333333333333")
        cast = _mock_cast(uid, "Den TV")
        browser = mock.Mock()
        with mock.patch.object(
            chromecast_handler.pychromecast,
            "get_listed_chromecasts",
            return_value=([cast], browser),
        ) as get_listed, mock.patch.object(
            chromecast_handler, "MyMediaDevice", return_value=mock.Mock()
        ):
            ok = handler.connect_chromecast(str(uid))

        self.assertTrue(ok)
        get_listed.assert_called()
        kwargs = get_listed.call_args_list[0].kwargs
        self.assertIn("uuids", kwargs)
        self.assertEqual(kwargs["uuids"], [uid])
        self.assertEqual(handler.get_chromecast_id(), str(uid))
        self.assertEqual(handler.get_chromecast_name(), "Den TV")

    def test_connect_falls_back_to_friendly_name(self):
        handler = _make_handler()
        cast = _mock_cast(None, "Patio")
        cast.uuid = None
        cast.cast_info = mock.Mock(uuid=None, friendly_name="Patio")

        def side_effect(**kwargs):
            if kwargs.get("uuids"):
                return [], None
            if kwargs.get("friendly_names") == ["Patio"]:
                return [cast], mock.Mock()
            return [], None

        with mock.patch.object(
            chromecast_handler.pychromecast,
            "get_listed_chromecasts",
            side_effect=side_effect,
        ), mock.patch.object(
            chromecast_handler, "MyMediaDevice", return_value=mock.Mock()
        ):
            ok = handler.connect_chromecast("Patio")

        self.assertTrue(ok)
        self.assertEqual(handler.get_chromecast_name(), "Patio")


class TestMultiSession(unittest.TestCase):
    def test_connect_two_devices(self):
        handler = _make_handler()
        u1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        u2 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        casts = {
            str(u1): _mock_cast(u1, "TV A"),
            str(u2): _mock_cast(u2, "TV B"),
        }

        def side_effect(**kwargs):
            uuids = kwargs.get("uuids") or []
            if uuids:
                key = str(uuids[0])
                return [casts[key]], mock.Mock()
            return [], None

        with mock.patch.object(
            chromecast_handler.pychromecast,
            "get_listed_chromecasts",
            side_effect=side_effect,
        ), mock.patch.object(
            chromecast_handler,
            "MyMediaDevice",
            side_effect=lambda mc, device_uuid=None, on_finished=None: mock.Mock(
                device_uuid=device_uuid, play_media_info=mock.Mock()
            ),
        ):
            self.assertTrue(handler.connect_chromecast(str(u1)))
            self.assertTrue(handler.connect_chromecast(str(u2)))

        connected = handler.get_connected_devices()
        self.assertEqual(len(connected), 2)
        ids = {c["uuid"] for c in connected}
        self.assertEqual(ids, {str(u1), str(u2)})

    def test_disconnect_one_keeps_other(self):
        handler = _make_handler()
        u1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        u2 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        c1, c2 = _mock_cast(u1, "TV A"), _mock_cast(u2, "TV B")

        def side_effect(**kwargs):
            uuids = kwargs.get("uuids") or []
            if uuids and str(uuids[0]) == str(u1):
                return [c1], mock.Mock()
            if uuids and str(uuids[0]) == str(u2):
                return [c2], mock.Mock()
            return [], None

        with mock.patch.object(
            chromecast_handler.pychromecast,
            "get_listed_chromecasts",
            side_effect=side_effect,
        ), mock.patch.object(
            chromecast_handler, "MyMediaDevice", return_value=mock.Mock()
        ):
            handler.connect_chromecast(str(u1))
            handler.connect_chromecast(str(u2))
            handler.disconnect_chromecast(str(u1))

        connected = handler.get_connected_devices()
        self.assertEqual(len(connected), 1)
        self.assertEqual(connected[0]["uuid"], str(u2))
        c1.disconnect.assert_called()

    def test_stream_mode_all_fans_out_play(self):
        handler = _make_handler()
        u1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        u2 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        media_a = mock.Mock()
        media_b = mock.Mock()
        medias = iter([media_a, media_b])

        def side_effect(**kwargs):
            uuids = kwargs.get("uuids") or []
            uid = uuids[0] if uuids else None
            cast = _mock_cast(uid, "TV")
            return [cast], mock.Mock()

        with mock.patch.object(
            chromecast_handler.pychromecast,
            "get_listed_chromecasts",
            side_effect=side_effect,
        ), mock.patch.object(
            chromecast_handler, "MyMediaDevice", side_effect=lambda *a, **k: next(medias)
        ), mock.patch.object(
            chromecast_handler,
            "_resolve_content_metadata",
            return_value={
                "id": 1,
                "url": "http://x/a.mp4",
                "content_title": "Ep1",
                "last_position": 0,
                "last_duration": 0,
            },
        ):
            handler.connect_chromecast(str(u1))
            handler.connect_chromecast(str(u2))
            handler.set_stream_mode(STREAM_MODE_ALL)
            result = handler.play_from_sql(
                {"content_id": 1, "parent_container_id": 9}
            )

        self.assertIsNotNone(result)
        media_a.play_media_info.assert_called_once()
        media_b.play_media_info.assert_called_once()

    def test_stream_mode_device_targets_one(self):
        handler = _make_handler()
        u1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        u2 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        media_a = mock.Mock()
        media_b = mock.Mock()
        medias = iter([media_a, media_b])

        def side_effect(**kwargs):
            uuids = kwargs.get("uuids") or []
            return [_mock_cast(uuids[0], "TV")], mock.Mock()

        with mock.patch.object(
            chromecast_handler.pychromecast,
            "get_listed_chromecasts",
            side_effect=side_effect,
        ), mock.patch.object(
            chromecast_handler, "MyMediaDevice", side_effect=lambda *a, **k: next(medias)
        ), mock.patch.object(
            chromecast_handler,
            "_resolve_content_metadata",
            return_value={"id": 1, "url": "http://x/a.mp4", "content_title": "Ep1"},
        ):
            handler.connect_chromecast(str(u1))
            handler.connect_chromecast(str(u2))
            handler.set_stream_mode(STREAM_MODE_DEVICE, str(u1))
            handler.play_from_sql({"content_id": 1, "parent_container_id": 9})

        media_a.play_media_info.assert_called_once()
        media_b.play_media_info.assert_not_called()

    def test_local_mode_no_cast_targets(self):
        handler = _make_handler()
        u1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        with mock.patch.object(
            chromecast_handler.pychromecast,
            "get_listed_chromecasts",
            return_value=([_mock_cast(u1, "TV A")], mock.Mock()),
        ), mock.patch.object(
            chromecast_handler, "MyMediaDevice", return_value=mock.Mock()
        ):
            handler.connect_chromecast(str(u1))
            handler.set_stream_mode(STREAM_MODE_LOCAL)
            self.assertEqual(handler.iter_targets(), [])
            self.assertIsNone(
                handler.play_from_sql({"content_id": 1, "parent_container_id": 1})
            )

    def test_disconnect_calls_library_disconnect(self):
        handler = _make_handler()
        uid = UUID("33333333-3333-3333-3333-333333333333")
        cast = _mock_cast(uid, "Den")
        with mock.patch.object(
            chromecast_handler.pychromecast,
            "get_listed_chromecasts",
            return_value=([cast], mock.Mock()),
        ), mock.patch.object(
            chromecast_handler, "MyMediaDevice", return_value=mock.Mock()
        ):
            handler.connect_chromecast(str(uid))
            handler.disconnect_chromecast()
        cast.disconnect.assert_called()
        self.assertEqual(handler.get_connected_devices(), [])
        self.assertEqual(handler.stream_mode, STREAM_MODE_LOCAL)


class TestCommandSkipMapsToNext(unittest.TestCase):
    def test_skip_command_uses_playlist_path(self):
        handler = _make_handler()
        handler._command_playlist = mock.Mock()
        handler.send_command(CommandList.CMD_SKIP)
        handler._command_playlist.assert_called_once_with(CommandList.CMD_SKIP)


if __name__ == "__main__":
    unittest.main()
