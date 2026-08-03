"""Unit tests for Chromecast discovery workflow (no live mDNS required)."""
import unittest
from unittest import mock
from uuid import UUID

from app.utils import chromecast_handler
from app.utils.chromecast_handler import (
    ChromecastHandler,
    _service_device_info,
)


def _make_handler(**kwargs):
    return ChromecastHandler(start_discovery=kwargs.get("start_discovery", False))


class TestServiceDeviceInfo(unittest.TestCase):
    def test_cast_info_object(self):
        u = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        info = mock.Mock(uuid=u, friendly_name="Living Room", model_name="Chromecast")
        entry = _service_device_info(info)
        self.assertEqual(entry["uuid"], str(u))
        self.assertEqual(entry["name"], "Living Room")

    def test_mdns_name_string_needs_uuid_hint(self):
        u = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        name = "Chromecast-aaaaaaaa._googlecast._tcp.local."
        self.assertIsNone(_service_device_info(name))
        entry = _service_device_info(name, uuid_hint=u)
        self.assertEqual(entry["uuid"], str(u))
        # Ugly mDNS name replaced with uuid label
        self.assertEqual(entry["name"], str(u))

    def test_string_without_uuid_returns_none(self):
        self.assertIsNone(_service_device_info("not-a-device"))


class TestListenerCallbackSignature(unittest.TestCase):
    """pychromecast SimpleCastListener calls add_callback(uuid, mdns_name: str)."""

    def test_on_cast_add_with_string_service_and_browser_castinfo(self):
        handler = _make_handler()
        uid = UUID("11111111-1111-1111-1111-111111111111")
        cast_info = mock.Mock(
            uuid=uid, friendly_name="Family Room TV", model_name="Chromecast"
        )
        # Simulate browser.devices populated before/when callback fires
        handler._browser = mock.Mock()
        handler._browser.devices = {uid: cast_info}
        handler._discovery_started = True

        # Real listener signature: (uuid, service_name: str)
        handler._on_cast_add(uid, "Chromecast-1111._googlecast._tcp.local.")

        devices = handler.get_scan_list()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["uuid"], str(uid))
        self.assertEqual(devices[0]["name"], "Family Room TV")

    def test_on_cast_add_string_only_still_lists_uuid(self):
        handler = _make_handler()
        uid = UUID("22222222-2222-2222-2222-222222222222")
        handler._browser = mock.Mock()
        handler._browser.devices = {}
        handler._on_cast_add(uid, "Chromecast-2222._googlecast._tcp.local.")
        devices = handler.get_scan_list()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["uuid"], str(uid))

    def test_sync_from_browser_devices(self):
        handler = _make_handler()
        u1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        u2 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        handler._browser = mock.Mock()
        handler._browser.devices = {
            u1: mock.Mock(uuid=u1, friendly_name="TV A", model_name="X"),
            u2: mock.Mock(uuid=u2, friendly_name="TV B", model_name="X"),
        }
        devices = handler.get_scan_list()
        names = {d["name"] for d in devices}
        self.assertEqual(names, {"TV A", "TV B"})


class TestScanFallback(unittest.TestCase):
    def test_scan_for_chromecasts_oneshot_fallback(self):
        handler = _make_handler(start_discovery=False)
        u1 = UUID("11111111-1111-1111-1111-111111111111")
        services = [mock.Mock(uuid=u1, friendly_name="TV A", model_name="Cast")]
        browser = mock.Mock()
        with mock.patch.object(
            chromecast_handler.pychromecast.discovery,
            "discover_chromecasts",
            return_value=(services, browser),
        ) as disc:
            handler.scan_for_chromecasts()
        disc.assert_called()
        devices = handler.get_scan_list()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["name"], "TV A")

    def test_get_scan_list_triggers_oneshot_when_empty_and_discovery_on(self):
        handler = _make_handler(start_discovery=True)
        # Prevent real Zeroconf
        handler._ensure_discovery = mock.Mock(return_value=False)
        u1 = UUID("33333333-3333-3333-3333-333333333333")
        services = [mock.Mock(uuid=u1, friendly_name="Patio", model_name="Cast")]
        with mock.patch.object(
            chromecast_handler.pychromecast.discovery,
            "discover_chromecasts",
            return_value=(services, mock.Mock()),
        ):
            devices = handler.get_scan_list()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["name"], "Patio")

    def test_get_scan_list_ensures_discovery(self):
        handler = _make_handler(start_discovery=True)
        handler._ensure_discovery = mock.Mock(return_value=True)
        handler._browser = mock.Mock()
        handler._browser.devices = {}
        handler.get_scan_list()
        handler._ensure_discovery.assert_called()


class TestRemoveCast(unittest.TestCase):
    def test_remove_drops_from_scan_list(self):
        handler = _make_handler()
        uid = UUID("44444444-4444-4444-4444-444444444444")
        cast_info = mock.Mock(uuid=uid, friendly_name="Gone", model_name="X")
        handler._browser = mock.Mock()
        handler._browser.devices = {uid: cast_info}
        handler._on_cast_add(uid, "name")
        self.assertEqual(len(handler.get_scan_list()), 1)
        handler._browser.devices = {}
        handler._on_cast_remove(uid, "name")
        self.assertEqual(handler.get_scan_list(), [])


if __name__ == "__main__":
    unittest.main()
