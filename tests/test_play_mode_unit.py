"""Unit tests for durable play_mode resolution (CI — no live cast)."""
import unittest
from unittest import mock

from app.utils import play_mode as pm
from app.utils import chromecast_handler as ch


class TestNormalizeAndResolve(unittest.TestCase):
    def test_normalize_legacy_tag(self):
        self.assertEqual(
            pm.normalize_play_mode("play_random_content_with_tag"),
            pm.PLAY_MODE_RANDOM_TAG,
        )

    def test_resolve_explicit_wins(self):
        self.assertEqual(
            pm.resolve_play_mode(
                {
                    "play_mode": "reverse",
                    "parent_container_id": 9,
                    "tag_list": ["movie"],
                }
            ),
            pm.PLAY_MODE_REVERSE,
        )

    def test_resolve_tv_episode_without_mode_is_sequential(self):
        self.assertEqual(
            pm.resolve_play_mode(
                {"parent_container_id": 3, "tag_list": ["movie"]}
            ),
            pm.PLAY_MODE_SEQUENTIAL,
        )

    def test_resolve_tag_without_parent(self):
        self.assertEqual(
            pm.resolve_play_mode({"tag_list": ["movie"]}),
            pm.PLAY_MODE_RANDOM_TAG,
        )

    def test_resolve_single_default(self):
        self.assertEqual(pm.resolve_play_mode({}), pm.PLAY_MODE_SINGLE)


class TestStampAndRestamp(unittest.TestCase):
    def test_stamp_random_tag_keeps_tags(self):
        meta = {"id": 1, "content_title": "A"}
        pm.stamp_play_mode(
            meta, pm.PLAY_MODE_RANDOM_TAG, {"tag_list": ["movie"]}
        )
        self.assertEqual(meta["play_mode"], pm.PLAY_MODE_RANDOM_TAG)
        self.assertEqual(meta["tag_list"], ["movie"])

    def test_restamp_preserves_random_tag_on_parented_content(self):
        session = {
            "play_mode": pm.PLAY_MODE_RANDOM_TAG,
            "tag_list": ["tv show", "movie"],
            "parent_container_id": None,
        }
        next_item = {
            "id": 99,
            "content_title": "Ep",
            "parent_container_id": 5,
        }
        out = pm.restamp_from_session(next_item, session)
        self.assertEqual(out["play_mode"], pm.PLAY_MODE_RANDOM_TAG)
        self.assertEqual(out["tag_list"], ["tv show", "movie"])
        # parent on the item itself is fine; mode still random_tag
        self.assertEqual(out["parent_container_id"], 5)


class TestAdjacentFromStatus(unittest.TestCase):
    def _status(self, meta):
        st = mock.Mock()
        st.media_metadata = meta
        return st

    def test_single_returns_none(self):
        st = self._status({"id": 1, "play_mode": pm.PLAY_MODE_SINGLE})
        self.assertIsNone(ch._next_media_from_status(st))

    def test_random_tag_restamps_mode(self):
        st = self._status(
            {
                "id": 1,
                "play_mode": pm.PLAY_MODE_RANDOM_TAG,
                "tag_list": ["movie"],
            }
        )
        picked = {
            "id": 7,
            "content_title": "X",
            "parent_container_id": 42,
        }
        with mock.patch.object(ch, "DBHandler") as DB:
            inst = DB.return_value
            inst.get_random_content_with_tag.return_value = picked
            out = ch._next_media_from_status(st)
        self.assertEqual(out["play_mode"], pm.PLAY_MODE_RANDOM_TAG)
        self.assertEqual(out["tag_list"], ["movie"])
        self.assertEqual(out["id"], 7)
        self.assertEqual(out["parent_container_id"], 42)

    def test_reverse_uses_previous_no_wrap(self):
        st = self._status(
            {
                "id": 10,
                "play_mode": pm.PLAY_MODE_REVERSE,
                "parent_container_id": 3,
            }
        )
        prev = {"id": 9, "parent_container_id": 3}
        with mock.patch.object(ch, "DBHandler") as DB:
            inst = DB.return_value
            inst.get_previous_content_in_container.return_value = prev
            out = ch._next_media_from_status(st)
            inst.get_previous_content_in_container.assert_called()
            _, kwargs = inst.get_previous_content_in_container.call_args
            self.assertEqual(kwargs.get("wrap"), False)
        self.assertEqual(out["play_mode"], pm.PLAY_MODE_REVERSE)
        self.assertEqual(out["id"], 9)

    def test_sequential_uses_next(self):
        st = self._status(
            {
                "id": 10,
                "play_mode": pm.PLAY_MODE_SEQUENTIAL,
                "parent_container_id": 3,
            }
        )
        nxt = {"id": 11, "parent_container_id": 3}
        with mock.patch.object(ch, "DBHandler") as DB:
            inst = DB.return_value
            inst.get_next_content_in_container.return_value = nxt
            out = ch._next_media_from_status(st)
        self.assertEqual(out["id"], 11)
        self.assertEqual(out["play_mode"], pm.PLAY_MODE_SEQUENTIAL)


class TestResolveContentMetadata(unittest.TestCase):
    def test_resolve_stamps_explicit_mode(self):
        with mock.patch.object(ch, "DBHandler") as DB:
            inst = DB.return_value
            inst.get_content_info.return_value = {
                "id": 5,
                "content_title": "E",
                "url": "http://x/a.mp4",
            }
            meta = ch._resolve_content_metadata(
                {
                    "content_id": 5,
                    "parent_container_id": 9,
                    "play_mode": "random_tag",
                    "tag_list": ["movie"],
                }
            )
        self.assertEqual(meta["play_mode"], pm.PLAY_MODE_RANDOM_TAG)
        self.assertEqual(meta["tag_list"], ["movie"])
        self.assertEqual(meta["parent_container_id"], 9)


if __name__ == "__main__":
    unittest.main()
