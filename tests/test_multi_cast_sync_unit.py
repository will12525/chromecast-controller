"""Unit tests for multi-cast barrier sync (no live devices)."""
import unittest
from unittest import mock

from app.utils.chromecast_handler import (
    ChromecastHandler,
    _resume_start_seconds,
    _sync_start_seconds,
)


class TestStartSeconds(unittest.TestCase):
    def test_resume_none_when_short(self):
        self.assertIsNone(
            _resume_start_seconds({"last_position": 10, "last_duration": 100})
        )

    def test_resume_when_past_30(self):
        self.assertEqual(
            _resume_start_seconds({"last_position": 45, "last_duration": 200}),
            45.0,
        )

    def test_sync_start_zero_default(self):
        self.assertEqual(_sync_start_seconds({}), 0.0)

    def test_sync_start_resume(self):
        self.assertEqual(
            _sync_start_seconds({"last_position": 50, "last_duration": 300}),
            50.0,
        )


class TestPlayOnTargetsSynced(unittest.TestCase):
    def test_single_target_uses_play_media_info(self):
        h = ChromecastHandler(start_discovery=False)
        media = mock.Mock()
        meta = {"id": 1, "url": "http://x/a.mp4", "content_title": "A"}
        h._play_on_targets_synced(meta, targets=[media])
        media.play_media_info.assert_called_once()
        media.load_media_info.assert_not_called()

    def test_multi_loads_autoplay_false_then_play(self):
        h = ChromecastHandler(start_discovery=False)
        order = []

        def make_media(uid):
            m = mock.Mock()
            m.device_uuid = uid

            def load(*a, **k):
                order.append((uid, "load", k.get("autoplay"), k.get("start_seconds")))
                return True

            def pause():
                order.append((uid, "pause"))

            def seek(t):
                order.append((uid, "seek", t))

            def play():
                order.append((uid, "play"))

            m.load_media_info.side_effect = load
            m.pause.side_effect = pause
            m.seek.side_effect = seek
            m.play.side_effect = play
            return m

        a, b = make_media("a"), make_media("b")
        meta = {
            "id": 1,
            "url": "http://x/a.mp4",
            "content_title": "A",
            "last_position": 0,
            "last_duration": 0,
        }
        with mock.patch(
            "app.utils.chromecast_handler.DBHandler"
        ) as DB:
            DB.return_value.update_content_play_count = mock.Mock()
            ok = h._play_on_targets_synced(meta, targets=[a, b])
        self.assertTrue(ok)

        # Both loads with autoplay=False before final play burst
        load_idxs = [i for i, e in enumerate(order) if e[1] == "load"]
        play_idxs = [i for i, e in enumerate(order) if e[1] == "play"]
        self.assertEqual(len(load_idxs), 2)
        self.assertEqual(len(play_idxs), 2)
        self.assertTrue(max(load_idxs) < min(play_idxs))
        for e in order:
            if e[1] == "load":
                self.assertIs(e[2], False)
                self.assertEqual(e[3], 0.0)
        # Realign seek happens before play (at least one seek per device after load)
        seek_idxs = [i for i, e in enumerate(order) if e[1] == "seek"]
        self.assertGreaterEqual(len(seek_idxs), 2)
        self.assertTrue(max(seek_idxs) < min(play_idxs) or max(load_idxs) < min(play_idxs))

    def test_multi_resume_start_seconds(self):
        h = ChromecastHandler(start_discovery=False)
        starts = []

        def make_media(uid):
            m = mock.Mock()
            m.device_uuid = uid

            def load(*a, **k):
                starts.append(k.get("start_seconds"))
                return True

            m.load_media_info.side_effect = load
            return m

        meta = {
            "id": 2,
            "url": "http://x/b.mp4",
            "last_position": 90,
            "last_duration": 400,
        }
        with mock.patch("app.utils.chromecast_handler.DBHandler"):
            h._play_on_targets_synced(meta, targets=[make_media("a"), make_media("b")])
        self.assertEqual(starts, [90.0, 90.0])


if __name__ == "__main__":
    unittest.main()
