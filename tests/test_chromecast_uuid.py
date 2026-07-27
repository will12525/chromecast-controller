"""Unit tests for Chromecast UUID identity (no live devices required)."""
import unittest
from unittest import mock
from uuid import UUID

from app.utils import chromecast_handler
from app.utils.chromecast_handler import (
    ChromecastHandler,
    _as_uuid_str,
    _service_device_info,
)


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
        # no uuid attr
        info = _service_device_info(service)
        self.assertEqual(info["uuid"], "Kitchen")
        self.assertEqual(info["name"], "Kitchen")


class TestScanListShape(unittest.TestCase):
    def test_scan_builds_uuid_name_entries(self):
        handler = ChromecastHandler()
        u1 = UUID("11111111-1111-1111-1111-111111111111")
        u2 = UUID("22222222-2222-2222-2222-222222222222")
        services = [
            mock.Mock(uuid=u1, friendly_name="TV A"),
            mock.Mock(uuid=u2, friendly_name="TV B"),
            mock.Mock(uuid=u1, friendly_name="TV A"),  # duplicate uuid ignored
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
        self.assertEqual(devices[0]["uuid"], str(u1))
        self.assertEqual(devices[0]["name"], "TV A")
        self.assertEqual(devices[1]["name"], "TV B")


class TestConnectByUuid(unittest.TestCase):
    def test_connect_prefers_uuid(self):
        handler = ChromecastHandler()
        uid = UUID("33333333-3333-3333-3333-333333333333")
        cast = mock.Mock()
        cast.uuid = uid
        cast.name = "Den TV"
        cast.cast_info = mock.Mock(uuid=uid, friendly_name="Den TV")
        cast.wait = mock.Mock()
        cast.media_controller = mock.Mock()
        cast.media_controller.register_status_listener = mock.Mock()

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
        # First call should use uuids=
        kwargs = get_listed.call_args_list[0].kwargs
        self.assertIn("uuids", kwargs)
        self.assertEqual(kwargs["uuids"], [uid])
        self.assertEqual(handler.get_chromecast_id(), str(uid))
        self.assertEqual(handler.get_chromecast_name(), "Den TV")

    def test_connect_falls_back_to_friendly_name(self):
        handler = ChromecastHandler()
        cast = mock.Mock()
        cast.uuid = None
        cast.name = "Patio"
        cast.cast_info = mock.Mock(uuid=None, friendly_name="Patio")
        cast.wait = mock.Mock()
        cast.media_controller = mock.Mock()
        cast.media_controller.register_status_listener = mock.Mock()

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


if __name__ == "__main__":
    unittest.main()
