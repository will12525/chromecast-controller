"""Chromecast discovery, multi-device sessions, and media transport.

Phase 0/1:
- Long-lived CastBrowser discovery (not deprecated discover_chromecasts loop)
- Multiple simultaneous sessions keyed by UUID
- Stream modes: local | device | all
- BUFFERED VOD play_media; clean disconnect()
- Skip → next episode; primary-only auto-next with fan-out
"""
import logging
import threading
import time
from enum import Enum, auto
from uuid import UUID

import pychromecast
import zeroconf
from pychromecast import STREAM_TYPE_BUFFERED
from pychromecast.discovery import CastBrowser, SimpleCastListener

from app.database.db_getter import DBHandler

# Stream target modes (process memory only)
STREAM_MODE_LOCAL = "local"
STREAM_MODE_DEVICE = "device"
STREAM_MODE_ALL = "all"


def _as_uuid_str(value):
    """Normalize cast uuid / string to a stable string id, or None."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return str(UUID(text))
    except (ValueError, AttributeError, TypeError):
        return text


def _service_device_info(service, uuid_hint=None):
    """Build {uuid, name} from CastInfo, service object, or mDNS name string.

    pychromecast SimpleCastListener callbacks pass (uuid, service_name: str),
    not a CastInfo — callers should prefer CastInfo from browser.devices and
    only fall back to this helper with uuid_hint set.
    """
    if service is None and uuid_hint is None:
        return None
    # mDNS service name string (listener callback second arg)
    if isinstance(service, str):
        uuid_str = _as_uuid_str(uuid_hint)
        if not uuid_str:
            return None
        # Prefer a short label; raw mDNS names are ugly
        name = service
        if name.endswith("._googlecast._tcp.local."):
            name = uuid_str
        return {"uuid": uuid_str, "name": name or uuid_str}

    uuid_val = getattr(service, "uuid", None) if service is not None else None
    name = ""
    if service is not None:
        name = (
            getattr(service, "friendly_name", None)
            or getattr(service, "model_name", None)
            or ""
        )
    uuid_str = _as_uuid_str(uuid_val) or _as_uuid_str(uuid_hint)
    if not uuid_str and not name:
        return None
    return {
        "uuid": uuid_str or name,
        "name": name or uuid_str,
    }


def _cast_device_id(cast):
    """Stable id for a Chromecast instance."""
    if not cast:
        return None
    uuid_val = getattr(cast, "uuid", None)
    if uuid_val is None and getattr(cast, "cast_info", None):
        uuid_val = getattr(cast.cast_info, "uuid", None)
    uuid_str = _as_uuid_str(uuid_val)
    if uuid_str:
        return uuid_str
    return getattr(cast, "name", None) or getattr(
        getattr(cast, "cast_info", None), "friendly_name", None
    )


def _cast_device_name(cast):
    if not cast:
        return None
    name = getattr(cast, "name", None)
    if name:
        return name
    cast_info = getattr(cast, "cast_info", None)
    if cast_info:
        return getattr(cast_info, "friendly_name", None)
    return _cast_device_id(cast)


class CommandList(Enum):
    CMD_REWIND = auto()
    CMD_REWIND_15 = auto()
    CMD_PLAY = auto()
    CMD_PAUSE = auto()
    CMD_SKIP_15 = auto()
    CMD_SKIP = auto()
    CMD_STOP = auto()

    CMD_PLAY_NEXT = auto()
    CMD_PLAY_PREV = auto()


class MyMediaDevice:
    """Thin wrapper around one device's MediaController."""

    DEFAULT_MEDIA_TYPE = "video/mp4"

    def __init__(self, media_controller, device_uuid=None, on_finished=None):
        self.media_controller = media_controller
        self.device_uuid = device_uuid
        self._on_finished = on_finished
        self.status = None
        self.cmd_data_dict = {
            CommandList.CMD_REWIND: self.rewind,
            CommandList.CMD_REWIND_15: self.rewind_15,
            CommandList.CMD_PLAY: self.media_controller.play,
            CommandList.CMD_PAUSE: self.media_controller.pause,
            CommandList.CMD_SKIP_15: self.skip_15,
            # Skip = next episode (not pychromecast jump-to-end)
            CommandList.CMD_SKIP: self.play_next_episode,
            CommandList.CMD_STOP: self.media_controller.stop,
            CommandList.CMD_PLAY_NEXT: self.play_next_episode,
            CommandList.CMD_PLAY_PREV: self.play_previous_episode,
        }
        self.media_controller.register_status_listener(self)

    def __del__(self):
        self.media_controller = None

    def play_episode_from_sql(self, content_data):
        media_metadata = _resolve_content_metadata(content_data)
        if media_metadata:
            self.play_media_info(media_metadata)
            return media_metadata

    def play_random_content_with_tag(self, json_request):
        media_metadata = _resolve_content_metadata(json_request)
        if media_metadata:
            media_metadata["play_mode"] = "play_random_content_with_tag"
            media_metadata["tag_list"] = json_request.get("tag_list")
            self.play_media_info(media_metadata)
            return media_metadata

    def play_random_container_content(self, json_request):
        db_connection = DBHandler()
        db_connection.open()
        media_metadata = db_connection.get_random_content_in_container(json_request)
        db_connection.close()
        if media_metadata:
            self.play_media_info(media_metadata)
            return media_metadata

    def play_next_episode(self):
        """Resolve next item from current status and play on this device only."""
        media_info = _next_media_from_status(self.status)
        if media_info:
            self.play_media_info(media_info)
            return media_info

    def play_previous_episode(self):
        media_info = None
        if self.status and (media_metadata := self.status.media_metadata):
            current_media_data = {
                "content_id": media_metadata.get("id"),
                "parent_container_id": media_metadata.get("parent_container_id"),
            }
            db_connection = DBHandler()
            db_connection.open()
            media_info = db_connection.get_previous_content_in_container(
                current_media_data
            )
            db_connection.close()
        if media_info:
            self.play_media_info(media_info)
            return media_info

    def play_media_info(self, media_metadata, update_play_count=True):
        if not media_metadata:
            return
        start_seconds = None
        try:
            last_position = float(media_metadata.get("last_position") or 0)
            last_duration = float(media_metadata.get("last_duration") or 0)
            if last_position > 30 and (
                last_duration <= 0 or last_position / last_duration < 0.9
            ):
                start_seconds = last_position
        except (TypeError, ValueError):
            start_seconds = None

        play_kwargs = {
            "title": media_metadata.get("content_title"),
            "metadata": media_metadata,
            "stream_type": STREAM_TYPE_BUFFERED,
        }
        if start_seconds is not None:
            play_kwargs["current_time"] = start_seconds

        self.media_controller.play_media(
            media_metadata.get("url"),
            self.DEFAULT_MEDIA_TYPE,
            **play_kwargs,
        )
        self.media_controller.block_until_active()

        if update_play_count and media_metadata.get("id"):
            db_connection = DBHandler()
            db_connection.open()
            db_connection.update_content_play_count(media_metadata.get("id"))
            db_connection.close()

    def get_media_controller_metadata(self):
        if self.status:
            meta = {
                "media_runtime": self.status.adjusted_current_time,
                "media_duration": self.status.duration,
                "media_title": self.status.title,
            }
            if self.status.media_metadata:
                meta["content_id"] = self.status.media_metadata.get("id")
                meta["parent_container_id"] = self.status.media_metadata.get(
                    "parent_container_id"
                )
            return meta

    def seek(self, position):
        self.media_controller.seek(position)

    def interpret_enum_cmd(self, cmd_enum):
        if cmd := self.cmd_data_dict.get(cmd_enum):
            cmd()

    def rewind(self):
        if self.status and self.status.adjusted_current_time <= 30:
            self.play_previous_episode()
        else:
            self.media_controller.rewind()

    def rewind_15(self):
        if self.status:
            self.seek(self.status.adjusted_current_time - 15)

    def skip_15(self):
        if self.status:
            self.seek(self.status.adjusted_current_time + 15)

    def new_media_status(self, status):
        self.status = status
        try:
            mc_status = self.media_controller.status
            if (
                mc_status
                and mc_status.player_state == "IDLE"
                and mc_status.idle_reason == "FINISHED"
            ):
                if self._on_finished:
                    self._on_finished(self.device_uuid)
                else:
                    self.play_next_episode()
        except Exception:
            logging.exception("new_media_status finished handling failed")


def _resolve_content_metadata(content_data):
    """Load content row and attach parent/play_mode fields for cast metadata."""
    if not content_data or not content_data.get("content_id"):
        return None
    db_connection = DBHandler()
    db_connection.open()
    try:
        media_metadata = db_connection.get_content_info(content_data.get("content_id"))
    finally:
        db_connection.close()
    if not media_metadata:
        return None
    if content_data.get("parent_container_id") is not None:
        media_metadata["parent_container_id"] = content_data.get("parent_container_id")
    if content_data.get("parent_container_id") is None and content_data.get("tag_list"):
        media_metadata["play_mode"] = "play_random_content_with_tag"
        media_metadata["tag_list"] = content_data.get("tag_list")
    return media_metadata


def _next_media_from_status(status):
    if not status or not status.media_metadata:
        return None
    media_metadata = status.media_metadata
    db_connection = DBHandler()
    db_connection.open()
    try:
        if media_metadata.get("play_mode") == "play_random_content_with_tag":
            media_info = db_connection.get_random_content_with_tag(
                media_metadata.get("tag_list")
            )
            if media_info:
                media_info["play_mode"] = "play_random_content_with_tag"
                media_info["tag_list"] = media_metadata.get("tag_list")
            return media_info
        current_media_data = {
            "content_id": media_metadata.get("id"),
            "parent_container_id": media_metadata.get("parent_container_id"),
        }
        return db_connection.get_next_content_in_container(current_media_data)
    finally:
        db_connection.close()


class ChromecastHandler(threading.Thread):
    """Discovery thread + multi-device cast sessions."""

    def __init__(self, start_discovery=True):
        threading.Thread.__init__(self, daemon=True)
        logging.basicConfig(
            filename="status_change.log",
            filemode="w",
            format="%(name)s - %(levelname)s - %(message)s",
            level=logging.DEBUG,
        )
        self.run_update = True
        self._lock = threading.RLock()
        # uuid_str -> CastInfo (or mock-friendly object with uuid/friendly_name)
        self._discovered = {}
        self._zconf = None
        self._browser = None
        # uuid_str -> {"cast": Chromecast, "media": MyMediaDevice, "name": str}
        self._sessions = {}
        self.stream_mode = STREAM_MODE_LOCAL
        self.active_uuid = None
        # Legacy single-device attrs (tests / old callers)
        self.chromecast_device = None
        self.media_controller = None
        self.chromecast_browser = None
        self.last_scanned_devices = []
        self._discovery_started = False
        self._start_discovery = start_discovery
        self._next_guard_until = 0.0
        self._last_discovery_attempt = 0.0
        self._last_oneshot_scan = 0.0
        self._discovery_retry_interval = 15.0
        self._oneshot_scan_interval = 20.0

    def __del__(self):
        self.run_update = False
        try:
            self.disconnect_chromecast()
        except Exception:
            pass
        self._stop_discovery()

    # --- discovery ---

    def _on_cast_add(self, uuid, service):
        """Listener callback. pychromecast passes (uuid, mDNS_name: str)."""
        info = self._cast_info_from_browser(uuid)
        store = info if info is not None else service
        device = _service_device_info(store, uuid_hint=uuid)
        if not device:
            # Still record a stub so the uuid appears while CastInfo catches up
            uuid_str = _as_uuid_str(uuid)
            if not uuid_str:
                return
            device = {"uuid": uuid_str, "name": uuid_str}
            store = service
        with self._lock:
            self._discovered[device["uuid"]] = store if store is not None else device
            self._sync_browser_devices_locked()
            self._refresh_scan_list_locked()

    def _on_cast_remove(self, uuid, service):
        uuid_str = _as_uuid_str(uuid)
        with self._lock:
            if uuid_str and uuid_str in self._discovered:
                del self._discovered[uuid_str]
            # Drop live session if device disappears
            if uuid_str and uuid_str in self._sessions:
                self._disconnect_uuid_locked(uuid_str)
            self._refresh_scan_list_locked()

    def _on_cast_update(self, uuid, service):
        self._on_cast_add(uuid, service)

    def _cast_info_from_browser(self, uuid):
        if not self._browser:
            return None
        devices = getattr(self._browser, "devices", None) or {}
        # keys may be UUID objects
        if uuid in devices:
            return devices[uuid]
        uuid_str = _as_uuid_str(uuid)
        for key, val in devices.items():
            if _as_uuid_str(key) == uuid_str:
                return val
        return None

    def _sync_browser_devices_locked(self):
        """Merge CastBrowser.devices into _discovered (caller holds lock)."""
        if not self._browser:
            return
        devices = getattr(self._browser, "devices", None) or {}
        for key, cast_info in devices.items():
            entry = _service_device_info(cast_info, uuid_hint=key)
            if entry:
                self._discovered[entry["uuid"]] = cast_info

    def _refresh_scan_list_locked(self):
        devices = []
        seen = set()
        for uuid_str, info in self._discovered.items():
            entry = _service_device_info(info, uuid_hint=uuid_str)
            if not entry:
                continue
            key = entry["uuid"]
            if key in seen:
                continue
            seen.add(key)
            devices.append(entry)
        # Stable order by name then uuid
        devices.sort(key=lambda d: (d.get("name") or "", d.get("uuid") or ""))
        self.last_scanned_devices = devices

    def _ensure_discovery(self):
        """Start long-lived CastBrowser (retries on failure)."""
        if not self._start_discovery:
            return False
        if self._discovery_started and self._browser is not None:
            return True
        now = time.time()
        if now - self._last_discovery_attempt < 2.0 and self._last_discovery_attempt:
            return bool(self._discovery_started)
        self._last_discovery_attempt = now
        try:
            # Clean partial state before retry
            if self._browser or self._zconf:
                self._stop_discovery()
            self._zconf = zeroconf.Zeroconf()
            listener = SimpleCastListener(
                add_callback=self._on_cast_add,
                remove_callback=self._on_cast_remove,
                update_callback=self._on_cast_update,
            )
            self._browser = CastBrowser(listener, self._zconf)
            self._browser.start_discovery()
            self.chromecast_browser = self._browser
            self._discovery_started = True
            logging.info("CastBrowser discovery started")
            return True
        except Exception:
            logging.exception("Failed to start CastBrowser discovery")
            self._discovery_started = False
            self._browser = None
            self._zconf = None
            return False

    def _stop_discovery(self):
        try:
            if self._browser:
                self._browser.stop_discovery()
        except Exception:
            pass
        try:
            if self._zconf:
                self._zconf.close()
        except Exception:
            pass
        self._browser = None
        self._zconf = None
        self.chromecast_browser = None
        self._discovery_started = False

    def _oneshot_discover_fallback(self, force=False):
        """Blocking one-shot mDNS scan when continuous browser is empty/unavailable."""
        now = time.time()
        if not force and (now - self._last_oneshot_scan) < self._oneshot_scan_interval:
            return
        self._last_oneshot_scan = now
        try:
            services, browser = pychromecast.discovery.discover_chromecasts(timeout=5)
            with self._lock:
                for service in services or []:
                    entry = _service_device_info(service)
                    if entry:
                        self._discovered[entry["uuid"]] = service
                self._refresh_scan_list_locked()
            # Prefer continuous browser; stop temporary browser if we already have one
            if browser:
                if self._browser:
                    try:
                        browser.stop_discovery()
                    except Exception:
                        pass
                else:
                    self.chromecast_browser = browser
        except Exception:
            logging.exception("oneshot discover_chromecasts fallback failed")

    def get_scan_list(self):
        """Return discovered devices as list of dicts: {"uuid": str, "name": str}."""
        # Always ensure discovery is running when the UI asks for devices
        if self._start_discovery:
            self._ensure_discovery()
        with self._lock:
            self._sync_browser_devices_locked()
            self._refresh_scan_list_locked()
            devices = list(self.last_scanned_devices)
        # If continuous discovery is empty, try a one-shot scan (helps cold start / zconf flakiness)
        if not devices and self._start_discovery:
            self._oneshot_discover_fallback(force=True)
            with self._lock:
                self._sync_browser_devices_locked()
                self._refresh_scan_list_locked()
                devices = list(self.last_scanned_devices)
        return devices

    def scan_for_chromecasts(self):
        """
        Refresh scan list from CastBrowser (or one-shot discover fallback).

        Prefer continuous discovery; this method remains for API compatibility.
        """
        if self._start_discovery:
            self._ensure_discovery()
        with self._lock:
            self._sync_browser_devices_locked()
            self._refresh_scan_list_locked()
            if self.last_scanned_devices:
                return
        self._oneshot_discover_fallback(force=True)

    # --- sessions ---

    def _lookup_cast_info(self, chromecast_id):
        """Find CastInfo / service object from discovery cache by uuid or name."""
        if not chromecast_id:
            return None, None
        uuid_str = _as_uuid_str(chromecast_id)
        with self._lock:
            if uuid_str and uuid_str in self._discovered:
                return uuid_str, self._discovered[uuid_str]
            for uid, info in self._discovered.items():
                entry = _service_device_info(info)
                if not entry:
                    continue
                if entry["uuid"] == uuid_str or entry["name"] == chromecast_id:
                    return entry["uuid"], info
            for device in self.last_scanned_devices:
                if device.get("uuid") == uuid_str or device.get("name") == chromecast_id:
                    return device.get("uuid"), self._discovered.get(device.get("uuid"))
        return uuid_str, None

    def _create_chromecast(self, chromecast_id):
        """
        Build a Chromecast instance for the given id.

        Prefer get_chromecast_from_cast_info when CastInfo is cached; else
        get_listed_chromecasts (uuid then friendly name).
        """
        uuid_str, cast_info = self._lookup_cast_info(chromecast_id)
        if cast_info is not None and self._zconf is not None:
            try:
                # Real CastInfo has host/services; mocks may not
                if getattr(cast_info, "host", None) or getattr(cast_info, "services", None):
                    cast = pychromecast.get_chromecast_from_cast_info(
                        cast_info, self._zconf
                    )
                    return cast, uuid_str
            except Exception:
                logging.exception("get_chromecast_from_cast_info failed; falling back")

        # get_listed_chromecasts path (also used by unit tests)
        try:
            uid = UUID(str(chromecast_id))
            chromecasts, browser = pychromecast.get_listed_chromecasts(uuids=[uid])
            if chromecasts:
                if browser and not self._browser:
                    self.chromecast_browser = browser
                return chromecasts[0], str(uid)
        except (ValueError, TypeError, AttributeError):
            pass

        chromecasts, browser = pychromecast.get_listed_chromecasts(
            friendly_names=[str(chromecast_id)]
        )
        if chromecasts:
            if browser and not self._browser:
                self.chromecast_browser = browser
            cast = chromecasts[0]
            return cast, _cast_device_id(cast) or uuid_str or str(chromecast_id)

        if uuid_str:
            try:
                uid = UUID(uuid_str)
                chromecasts, browser = pychromecast.get_listed_chromecasts(uuids=[uid])
                if chromecasts:
                    return chromecasts[0], uuid_str
            except (ValueError, TypeError, AttributeError):
                pass
        return None, uuid_str

    def connect_chromecast(self, chromecast_id):
        """Add a device to the connected set (does not drop other sessions)."""
        self._ensure_discovery()
        cast, uuid_str = self._create_chromecast(chromecast_id)
        if not cast:
            return False
        try:
            cast.wait()
        except Exception:
            logging.exception("cast.wait failed for %s", chromecast_id)
            try:
                cast.disconnect(timeout=2)
            except Exception:
                pass
            return False

        device_id = _cast_device_id(cast) or uuid_str or str(chromecast_id)
        name = _cast_device_name(cast) or str(chromecast_id)
        media = MyMediaDevice(
            cast.media_controller,
            device_uuid=device_id,
            on_finished=self._on_device_finished,
        )
        with self._lock:
            # Replace existing session for same uuid cleanly
            if device_id in self._sessions:
                self._disconnect_uuid_locked(device_id)
            self._sessions[device_id] = {
                "cast": cast,
                "media": media,
                "name": name,
            }
            # Legacy single-device pointers = primary
            if self.stream_mode == STREAM_MODE_LOCAL or not self.active_uuid:
                self.stream_mode = STREAM_MODE_DEVICE
                self.active_uuid = device_id
            elif self.stream_mode == STREAM_MODE_DEVICE and self.active_uuid not in self._sessions:
                self.active_uuid = device_id
            self._sync_legacy_locked()
        return True

    def _disconnect_uuid_locked(self, uuid_str):
        session = self._sessions.pop(uuid_str, None)
        if not session:
            return
        cast = session.get("cast")
        if cast:
            try:
                cast.disconnect(timeout=5)
            except Exception:
                logging.exception("cast.disconnect failed for %s", uuid_str)
        if self.active_uuid == uuid_str:
            self.active_uuid = next(iter(self._sessions), None)
            if not self.active_uuid:
                self.stream_mode = STREAM_MODE_LOCAL
        self._sync_legacy_locked()

    def disconnect_chromecast(self, chromecast_id=None):
        """Disconnect one device by id, or all if chromecast_id is None."""
        with self._lock:
            if chromecast_id is None:
                for uid in list(self._sessions.keys()):
                    self._disconnect_uuid_locked(uid)
                self.stream_mode = STREAM_MODE_LOCAL
                self.active_uuid = None
                self._sync_legacy_locked()
                return
            uuid_str = _as_uuid_str(chromecast_id) or str(chromecast_id)
            # Also match by name
            if uuid_str not in self._sessions:
                for uid, sess in list(self._sessions.items()):
                    if sess.get("name") == chromecast_id or uid == chromecast_id:
                        uuid_str = uid
                        break
            self._disconnect_uuid_locked(uuid_str)

    def _sync_legacy_locked(self):
        primary = self._primary_session_locked()
        if primary:
            self.chromecast_device = primary["cast"]
            self.media_controller = primary["media"]
        else:
            self.chromecast_device = None
            self.media_controller = None

    def _primary_session_locked(self):
        if self.stream_mode == STREAM_MODE_LOCAL:
            return None
        if self.stream_mode == STREAM_MODE_DEVICE and self.active_uuid:
            return self._sessions.get(self.active_uuid)
        if self.stream_mode == STREAM_MODE_ALL and self._sessions:
            if self.active_uuid and self.active_uuid in self._sessions:
                return self._sessions[self.active_uuid]
            # first connected
            return next(iter(self._sessions.values()), None)
        if self.active_uuid and self.active_uuid in self._sessions:
            return self._sessions.get(self.active_uuid)
        return next(iter(self._sessions.values()), None)

    def _primary_uuid(self):
        with self._lock:
            sess = self._primary_session_locked()
            if not sess:
                return None
            for uid, s in self._sessions.items():
                if s is sess:
                    return uid
            return self.active_uuid

    def iter_targets(self):
        """Media wrappers that should receive play/command/seek for current mode."""
        with self._lock:
            if self.stream_mode == STREAM_MODE_LOCAL:
                return []
            if self.stream_mode == STREAM_MODE_DEVICE:
                if self.active_uuid and self.active_uuid in self._sessions:
                    return [self._sessions[self.active_uuid]["media"]]
                return []
            # all
            return [s["media"] for s in self._sessions.values()]

    def get_connected_devices(self):
        with self._lock:
            return [
                {"uuid": uid, "name": sess.get("name") or uid}
                for uid, sess in self._sessions.items()
            ]

    def set_stream_mode(self, mode, chromecast_id=None):
        """
        Set stream mode: local | all | device.

        For device mode, chromecast_id selects the active uuid (connect if needed).
        """
        mode = (mode or STREAM_MODE_LOCAL).lower()
        if mode not in (STREAM_MODE_LOCAL, STREAM_MODE_ALL, STREAM_MODE_DEVICE):
            return False
        with self._lock:
            if mode == STREAM_MODE_LOCAL:
                self.stream_mode = STREAM_MODE_LOCAL
                self._sync_legacy_locked()
                return True
            if mode == STREAM_MODE_ALL:
                self.stream_mode = STREAM_MODE_ALL
                if not self.active_uuid and self._sessions:
                    self.active_uuid = next(iter(self._sessions))
                self._sync_legacy_locked()
                return True
            # device
            self.stream_mode = STREAM_MODE_DEVICE
            target = chromecast_id or self.active_uuid
        if target and target not in self._sessions:
            # connect outside lock (network)
            if not self.connect_chromecast(target):
                return False
        with self._lock:
            uuid_str = _as_uuid_str(target) or target
            if uuid_str not in self._sessions:
                # name match
                for uid, sess in self._sessions.items():
                    if sess.get("name") == target:
                        uuid_str = uid
                        break
            if uuid_str not in self._sessions:
                return False
            self.active_uuid = uuid_str
            self.stream_mode = STREAM_MODE_DEVICE
            self._sync_legacy_locked()
        return True

    def get_stream_state(self):
        """Snapshot for /get_chromecast_list."""
        with self._lock:
            primary = self._primary_session_locked()
            primary_id = None
            primary_name = None
            if primary:
                for uid, sess in self._sessions.items():
                    if sess is primary:
                        primary_id = uid
                        primary_name = sess.get("name")
                        break
            connected = [
                {"uuid": uid, "name": sess.get("name") or uid}
                for uid, sess in self._sessions.items()
            ]
            return {
                "scanned_devices": list(self.last_scanned_devices),
                "connected_devices": connected,
                "stream_mode": self.stream_mode,
                "active_device_id": self.active_uuid,
                "connected_device": primary_name or (
                    "Local" if self.stream_mode == STREAM_MODE_LOCAL else None
                ),
                "connected_device_id": primary_id,
            }

    def get_media_controller(self) -> MyMediaDevice:
        with self._lock:
            return self.media_controller

    def get_media_controller_metadata(self):
        targets = self.iter_targets()
        if not targets:
            primary = None
            with self._lock:
                sess = self._primary_session_locked()
                primary = sess["media"] if sess else None
            if primary:
                return primary.get_media_controller_metadata()
            return None
        # Prefer primary among targets
        with self._lock:
            sess = self._primary_session_locked()
            if sess and sess["media"] in targets:
                return sess["media"].get_media_controller_metadata()
        return targets[0].get_media_controller_metadata()

    def get_chromecast_id(self) -> str:
        with self._lock:
            sess = self._primary_session_locked()
            if not sess:
                return None
            return _cast_device_id(sess["cast"]) or self.active_uuid

    def get_chromecast_name(self) -> str:
        with self._lock:
            sess = self._primary_session_locked()
            if not sess:
                return None
            return sess.get("name") or _cast_device_name(sess["cast"])

    def seek_media_time(self, media_time):
        for media in self.iter_targets():
            try:
                media.seek(media_time)
            except Exception:
                logging.exception("seek failed")

    def play_from_sql(self, content_data):
        targets = self.iter_targets()
        if not targets:
            return None
        media_metadata = _resolve_content_metadata(content_data)
        if not media_metadata:
            return None
        if content_data.get("parent_container_id") is None and content_data.get(
            "tag_list"
        ):
            media_metadata["play_mode"] = "play_random_content_with_tag"
            media_metadata["tag_list"] = content_data.get("tag_list")
        elif content_data.get("parent_container_id") is not None:
            media_metadata["parent_container_id"] = content_data.get(
                "parent_container_id"
            )
        for i, media in enumerate(targets):
            try:
                media.play_media_info(media_metadata, update_play_count=(i == 0))
            except Exception:
                logging.exception("play_media_info failed on target %s", i)
        return media_metadata

    def play_random_container_content(self, json_request):
        targets = self.iter_targets()
        if not targets:
            return None
        db_connection = DBHandler()
        db_connection.open()
        media_metadata = db_connection.get_random_content_in_container(json_request)
        db_connection.close()
        if not media_metadata:
            return None
        for i, media in enumerate(targets):
            try:
                media.play_media_info(media_metadata, update_play_count=(i == 0))
            except Exception:
                logging.exception("play_random_container failed on target %s", i)
        return media_metadata

    def send_command(self, media_device_command):
        # Next/prev/skip: resolve once on primary, fan-out play for multi
        if media_device_command in (
            CommandList.CMD_SKIP,
            CommandList.CMD_PLAY_NEXT,
            CommandList.CMD_PLAY_PREV,
        ):
            self._command_playlist(media_device_command)
            return
        for media in self.iter_targets():
            try:
                media.interpret_enum_cmd(media_device_command)
            except Exception:
                logging.exception("command %s failed", media_device_command)

    def _command_playlist(self, cmd):
        """Next/prev: compute on primary status, play on all targets."""
        with self._lock:
            primary = self._primary_session_locked()
        if not primary:
            return
        media = primary["media"]
        if cmd == CommandList.CMD_PLAY_PREV:
            info = None
            if media.status and media.status.media_metadata:
                current = {
                    "content_id": media.status.media_metadata.get("id"),
                    "parent_container_id": media.status.media_metadata.get(
                        "parent_container_id"
                    ),
                }
                db = DBHandler()
                db.open()
                info = db.get_previous_content_in_container(current)
                db.close()
        else:
            info = _next_media_from_status(media.status)
        if not info:
            return
        for i, target in enumerate(self.iter_targets()):
            try:
                target.play_media_info(info, update_play_count=(i == 0))
            except Exception:
                logging.exception("playlist command fan-out failed")

    def _on_device_finished(self, device_uuid):
        """Primary-only auto-next with fan-out to all targets."""
        now = time.time()
        if now < self._next_guard_until:
            return
        primary_uuid = self._primary_uuid()
        if not primary_uuid or device_uuid != primary_uuid:
            return
        self._next_guard_until = now + 2.0
        with self._lock:
            sess = self._sessions.get(primary_uuid)
        if not sess:
            return
        info = _next_media_from_status(sess["media"].status)
        if not info:
            return
        for i, target in enumerate(self.iter_targets()):
            try:
                target.play_media_info(info, update_play_count=(i == 0))
            except Exception:
                logging.exception("auto-next fan-out failed")

    def run(self):
        if self._start_discovery:
            self._ensure_discovery()
        while self.run_update:
            try:
                if self._start_discovery and not self._discovery_started:
                    self._ensure_discovery()
                # Keep scan list fresh from browser
                if self._browser:
                    with self._lock:
                        self._sync_browser_devices_locked()
                        self._refresh_scan_list_locked()
                        empty = not self.last_scanned_devices
                    # Periodic one-shot if browser stays empty (zconf glitches)
                    if empty:
                        now = time.time()
                        if now - self._last_oneshot_scan >= self._oneshot_scan_interval:
                            self._oneshot_discover_fallback(force=False)
                time.sleep(1.0)
            except KeyboardInterrupt:
                break
            except Exception:
                logging.exception("ChromecastHandler run loop error")
                time.sleep(1.0)
