"""
Integration: durable play_mode + real library catalog.

**Important:** `TestPlayModeApi` forces `stream_mode=local` so it validates
play_mode / next-episode **JSON** only — it will **not** change Chromecast/TV
state. Use a separate live-cast suite for on-device playback.

Requires a non-empty `media_metadata.db` (run Scan Media in the app first).
Does **not** auto-walk the whole library (that looked like a hang).

  pytest tests/test_cast_play_modes_integration.py -m integration -q
"""
from __future__ import annotations

import pytest
from flask import Flask

from app.routes import register_blueprints
from app.routes.shared import APIEndpoints, bh
from app.utils.play_mode import (
    PLAY_MODE_RANDOM_TAG,
    PLAY_MODE_REVERSE,
    PLAY_MODE_SEQUENTIAL,
    PLAY_MODE_SINGLE,
)

from . import cast_integration_helpers as H

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def seeded_db():
    db = H.ensure_db_scanned()
    yield db
    db.close()


@pytest.fixture(scope="module")
def flask_client(seeded_db):
    app = Flask(__name__, template_folder="../app/templates")
    app.testing = True
    register_blueprints(app)
    with app.test_client() as client:
        yield client


class TestLibraryPrecondition:
    def test_catalog_has_content_and_urls(self, seeded_db):
        row = seeded_db.get_data_from_db_first_result(
            "SELECT COUNT(*) AS c FROM content;"
        )
        assert int(row.get("c") or 0) > 0
        bases = H.library_url_bases(seeded_db)
        assert bases


class TestPlayModeApi:
    """API-only: no Chromecast activity (local stream mode)."""

    def test_play_media_returns_play_mode_sequential(self, flask_client, seeded_db):
        ep = H.library_tv_episode_with_next(seeded_db)
        H.assert_url_is_library(ep["url"], H.library_url_bases(seeded_db))
        # Force local — does not cast to TV
        bh.set_stream_mode("local")
        resp = flask_client.post(
            APIEndpoints.PLAY_MEDIA.value,
            json={
                "content_id": ep["content_id"],
                "parent_container_id": ep["parent_container_id"],
                "tag_list": [],
                "play_mode": PLAY_MODE_SEQUENTIAL,
            },
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("local_play_url")
        H.assert_url_is_library(body["local_play_url"], H.library_url_bases(seeded_db))
        assert body.get("play_mode") == PLAY_MODE_SEQUENTIAL
        assert body.get("id") == ep["content_id"]

    def test_get_next_sequential(self, flask_client, seeded_db):
        ep = H.library_tv_episode_with_next(seeded_db)
        resp = flask_client.post(
            APIEndpoints.GET_NEXT_MEDIA.value,
            json={
                "content_id": ep["content_id"],
                "parent_container_id": ep["parent_container_id"],
                "play_mode": PLAY_MODE_SEQUENTIAL,
                "tag_list": [],
            },
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("id") == ep["next_content_id"]
        assert body.get("play_mode") == PLAY_MODE_SEQUENTIAL
        assert body.get("local_play_url")

    def test_get_next_reverse(self, flask_client, seeded_db):
        ep = H.library_tv_episode_with_next(seeded_db)
        # Start from the *next* episode and reverse back to A
        resp = flask_client.post(
            APIEndpoints.GET_NEXT_MEDIA.value,
            json={
                "content_id": ep["next_content_id"],
                "parent_container_id": ep["parent_container_id"],
                "play_mode": PLAY_MODE_REVERSE,
                "tag_list": [],
            },
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("id") == ep["content_id"]
        assert body.get("play_mode") == PLAY_MODE_REVERSE

    def test_random_tag_mode_persists_when_item_has_parent(
        self, flask_client, seeded_db
    ):
        tag, pool = H.library_tagged_pool(seeded_db, min_size=2)
        start = pool[0]
        resp = flask_client.post(
            APIEndpoints.PLAY_MEDIA.value,
            json={
                "content_id": start.get("id"),
                "parent_container_id": None,
                "tag_list": [tag],
                "play_mode": PLAY_MODE_RANDOM_TAG,
            },
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("play_mode") == PLAY_MODE_RANDOM_TAG

        # get_next should keep random_tag even if picks parented content
        nxt = flask_client.post(
            APIEndpoints.GET_NEXT_MEDIA.value,
            json={
                "content_id": start.get("id"),
                "parent_container_id": None,
                "tag_list": [tag],
                "play_mode": PLAY_MODE_RANDOM_TAG,
            },
        )
        assert nxt.status_code == 200
        nbody = nxt.get_json() or {}
        assert nbody.get("play_mode") == PLAY_MODE_RANDOM_TAG
        assert nbody.get("id") is not None

    def test_tv_start_with_tags_still_sequential_without_explicit_random(
        self, flask_client, seeded_db
    ):
        ep = H.library_tv_episode_with_next(seeded_db)
        # No play_mode: parent set → sequential even if tags present
        resp = flask_client.post(
            APIEndpoints.PLAY_MEDIA.value,
            json={
                "content_id": ep["content_id"],
                "parent_container_id": ep["parent_container_id"],
                "tag_list": ["movie"],
            },
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("play_mode") == PLAY_MODE_SEQUENTIAL

    def test_explicit_random_tag_with_parent_stays_random(
        self, flask_client, seeded_db
    ):
        ep = H.library_tv_episode_with_next(seeded_db)
        tag, _pool = H.library_tagged_pool(seeded_db, min_size=1)
        resp = flask_client.post(
            APIEndpoints.PLAY_MEDIA.value,
            json={
                "content_id": ep["content_id"],
                "parent_container_id": ep["parent_container_id"],
                "tag_list": [tag],
                "play_mode": PLAY_MODE_RANDOM_TAG,
            },
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("play_mode") == PLAY_MODE_RANDOM_TAG

    def test_single_mode_no_next(self, flask_client, seeded_db):
        ep = H.library_tv_episode_with_next(seeded_db)
        resp = flask_client.post(
            APIEndpoints.GET_NEXT_MEDIA.value,
            json={
                "content_id": ep["content_id"],
                "parent_container_id": ep["parent_container_id"],
                "play_mode": PLAY_MODE_SINGLE,
            },
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("play_mode") == PLAY_MODE_SINGLE
        assert not body.get("id") or body.get("error_msg")
