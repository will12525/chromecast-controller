"""
Shared helpers for live Chromecast / library integration tests.

Environment:
  CAST_DEVICE_1 / CHROMECAST_ID, CAST_DEVICE_2 / CHROMECAST_ID_2
  CAST_ALLOW_FULL_SCAN=1 — allow a full disk walk (SLOW; can take many minutes)
  CAST_FORCE_RESCAN=1 — rescan even if content exists (implies full scan)
  CAST_DISCOVERY_TIMEOUT, CAST_PLAY_SETTLE_SECONDS

Note: Most play-mode *API* tests force stream_mode=local and will NOT change
Chromecast/TV state. Live cast tests live in separate classes and connect
explicitly.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

import pytest
import requests

from app.database.db_getter import DBHandler
from app.utils import config_file_handler

DEFAULT_PRIMARY = os.environ.get("CAST_DEVICE_1") or os.environ.get(
    "CHROMECAST_ID", "Family Room TV"
)
DEFAULT_SECONDARY = os.environ.get("CAST_DEVICE_2") or os.environ.get(
    "CHROMECAST_ID_2", "Bedroom"
)
DISCOVERY_TIMEOUT = float(os.environ.get("CAST_DISCOVERY_TIMEOUT", "15"))
PLAY_SETTLE = float(os.environ.get("CAST_PLAY_SETTLE_SECONDS", "4"))
BBB_URL = (
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
)


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").lower() in ("1", "true", "yes")


def content_count(db: DBHandler) -> int:
    # DBHandler only executes statements sqlite3.complete_statement accepts (need ';')
    row = db.get_data_from_db_first_result("SELECT COUNT(*) AS c FROM content;")
    return int((row or {}).get("c") or 0)


def ensure_db_scanned(force: Optional[bool] = None) -> DBHandler:
    """
    Open catalog DB; optionally scan media disks.

    **Default:** if the DB already has content, return it (fast).
    **Never** start an unbounded full-library scan unless
    CAST_ALLOW_FULL_SCAN=1 (or force=True with that flag).

    A full scan of multi-disk libraries can take tens of minutes and looks like a hang.
    Prefer: run Scan Media once in the app UI, then run tests against media_metadata.db.
    """
    force_rescan = force if force is not None else _env_flag("CAST_FORCE_RESCAN")
    allow_full = _env_flag("CAST_ALLOW_FULL_SCAN") or force_rescan

    db = DBHandler()
    db.open()
    db.create_db()
    cfg = config_file_handler.load_json_file_content() or {}
    folders = cfg.get("media_folders") or []
    for folder in folders:
        src = folder.get("content_src")
        if src and os.path.isdir(src):
            # setup_content_directory may collect that folder when first added —
            # only call add path without re-collect when already present
            try:
                db.add_content_directory_info(folder)
            except Exception:
                db.setup_content_directory(folder)

    count = content_count(db)
    if count > 0 and not force_rescan:
        return db

    if count == 0 and not allow_full:
        db.close()
        pytest.skip(
            "Catalog empty (media_metadata.db has 0 content). "
            "Run Scan Media in the app once, or re-run with CAST_ALLOW_FULL_SCAN=1 "
            "(full disk walk — can take a long time)."
        )

    if force_rescan and not allow_full and count > 0:
        # force without allow: still use existing
        return db

    print(
        "WARNING: starting full media scan for tests "
        "(CAST_ALLOW_FULL_SCAN / CAST_FORCE_RESCAN). This can take a long time…"
    )
    db.scan_content_directories()
    count = content_count(db)
    if count == 0:
        db.close()
        pytest.skip(
            "Catalog still empty after scan — check media_folders / disks"
        )
    return db


def library_url_bases(db: DBHandler) -> list[str]:
    rows = db.get_all_content_directory_info() or []
    return [r.get("content_url") for r in rows if r.get("content_url")]


def assert_url_is_library(url: str, bases: list[str]) -> None:
    assert url, "missing url"
    if not bases:
        return
    if str(url).startswith("https://commondatastorage.googleapis.com"):
        return
    ok = any(
        str(url).startswith(str(b).rstrip("/")) or str(b) in str(url) for b in bases
    )
    assert ok, f"url not under library bases: {url} bases={bases}"


def library_tv_episode_with_next(db: DBHandler) -> dict[str, Any]:
    """Episode A with sequential next B (real library URLs)."""
    rows = db.get_data_from_db(
        """
        SELECT c.id AS content_id, c.content_title,
               cc.parent_container_id AS parent_container_id,
               cd.content_url || '/' || c.content_src AS url,
               cc.content_index
        FROM content c
        INNER JOIN container_content cc ON cc.content_id = c.id
        INNER JOIN content_directory cd ON c.content_directory_id = cd.id
        WHERE c.content_src IS NOT NULL AND c.content_src != ''
        ORDER BY cc.parent_container_id, cc.content_index, c.id
        LIMIT 500;
        """
    )
    if not rows:
        pytest.skip("No TV-linked content in catalog — scan library first")

    by_parent: dict = {}
    for r in rows:
        pid = r.get("parent_container_id")
        by_parent.setdefault(pid, []).append(r)

    for pid, items in by_parent.items():
        if len(items) < 2:
            continue
        a = items[0]
        expected = db.get_next_content_in_container(
            {"content_id": a["content_id"], "parent_container_id": pid}
        )
        if not expected or expected.get("id") == a["content_id"]:
            continue
        return {
            "content_id": a["content_id"],
            "content_title": a.get("content_title"),
            "parent_container_id": pid,
            "url": a.get("url"),
            "next_content_id": expected.get("id"),
            "next_url": expected.get("url"),
            "next_title": expected.get("content_title"),
        }
    pytest.skip("No container with ≥2 sequential episodes found")


def library_tagged_pool(db: DBHandler, min_size: int = 2) -> tuple[str, list[dict]]:
    tags = db.get_data_from_db("SELECT tag_title FROM user_tags ORDER BY tag_title;") or []
    env_tag = os.environ.get("CAST_TEST_TAG")
    candidates = [env_tag] if env_tag else [t.get("tag_title") for t in tags]
    for tag in candidates:
        if not tag:
            continue
        items = []
        db.get_all_content_with_tags([tag], items)
        if len(items) < min_size:
            continue
        pool = []
        for it in items:
            info = db.get_content_info(it.get("id"))
            if info and info.get("url"):
                pool.append(info)
            if len(pool) >= min_size:
                break
        if len(pool) >= min_size:
            return tag, pool
    pytest.skip(f"No tag with ≥{min_size} content items for random_tag tests")


def wait_for_devices(handler, min_count: int = 1, timeout: float = DISCOVERY_TIMEOUT):
    deadline = time.time() + timeout
    last = []
    while time.time() < deadline:
        last = handler.get_scan_list() or []
        if len(last) >= min_count:
            return last
        try:
            handler.scan_for_chromecasts()
        except Exception:
            pass
        time.sleep(0.5)
    return last


def pick_device(devices: list, preferred: Optional[str] = None) -> dict:
    if not devices:
        pytest.skip("No Chromecast devices discovered")
    if preferred:
        for d in devices:
            if d.get("uuid") == preferred or d.get("name") == preferred:
                return d
    return devices[0]


def pick_two_devices(devices: list, pref_a: str, pref_b: str):
    if len(devices) < 2:
        pytest.skip("Need ≥2 Chromecasts for multi-device tests")
    a = pick_device(devices, pref_a)
    rest = [d for d in devices if d.get("uuid") != a.get("uuid")]
    b = pick_device(rest, pref_b)
    if a.get("uuid") == b.get("uuid"):
        b = rest[0]
    return a, b


def http_url_ok(url: str, timeout: float = 5.0) -> bool:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code < 400:
            return True
        r = requests.get(url, timeout=timeout, stream=True)
        return r.status_code < 400
    except Exception:
        return False


def settle_after_play(seconds: float = PLAY_SETTLE):
    time.sleep(seconds)
