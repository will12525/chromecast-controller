"""Scan skips ffprobe for catalogued TV files and commits one file at a time."""
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from app.database.db_access import DBType
from app.database.db_getter import DBHandler


def _probe(path, content_data):
    content_data["content_title"] = "Probed Title"


class TestMediaScan(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmpdir.name) / "library"
        self.show_dir = self.root / "tv_shows" / "Demo Show"
        self.show_dir.mkdir(parents=True)
        self._write_episode(1)
        self.db_path = os.path.join(self._tmpdir.name, "scan.db")
        self.db = DBHandler(db_type=DBType.PHYSICAL, file_name=self.db_path)
        self.db.open()
        self.db.create_db()
        self.db.add_content_directory_info(
            {
                "content_src": self.root.as_posix(),
                "content_url": "http://127.0.0.1:8000/",
            }
        )

    def tearDown(self):
        self.db.close()
        self._tmpdir.cleanup()

    def _write_episode(self, number):
        path = self.show_dir / f"Demo Show - s01e0{number}.mp4"
        path.write_bytes(b"")
        return path

    def _content_row(self, src_suffix):
        return self.db.get_data_from_db_first_result(
            "SELECT content_title, added_at FROM content WHERE content_src = :content_src;",
            {"content_src": src_suffix},
        )

    def test_rescan_skips_probe_and_keeps_title(self):
        with mock.patch(
            "app.database.media_metadata_collector.get_ffmpeg_metadata",
            side_effect=_probe,
        ) as probe:
            self.db.scan_content_directories()
            self.assertEqual(probe.call_count, 1)
            first = self._content_row("/tv_shows/Demo Show/Demo Show - s01e01.mp4")
            self.assertEqual(first["content_title"], "Probed Title")
            self.assertTrue(first["added_at"])

            self.db.scan_content_directories()
            self.assertEqual(probe.call_count, 1)
            second = self._content_row("/tv_shows/Demo Show/Demo Show - s01e01.mp4")
            self.assertEqual(second["content_title"], "Probed Title")
            self.assertEqual(second["added_at"], first["added_at"])

            self._write_episode(2)
            self.db.scan_content_directories()
            self.assertEqual(probe.call_count, 2)
            new_episode = self._content_row("/tv_shows/Demo Show/Demo Show - s01e02.mp4")
            self.assertEqual(new_episode["content_title"], "Probed Title")

    def test_failed_file_rolls_back_and_scan_continues(self):
        self._write_episode(2)
        original = DBHandler.insert_content

        def fail_second(handler, content):
            original(handler, content)
            if str(content.get("content_src", "")).endswith("s01e02.mp4"):
                raise RuntimeError("boom")

        with mock.patch(
            "app.database.media_metadata_collector.get_ffmpeg_metadata",
            side_effect=_probe,
        ):
            with mock.patch.object(DBHandler, "insert_content", fail_second):
                self.db.scan_content_directories()

        kept = self._content_row("/tv_shows/Demo Show/Demo Show - s01e01.mp4")
        dropped = self._content_row("/tv_shows/Demo Show/Demo Show - s01e02.mp4")
        self.assertEqual(kept["content_title"], "Probed Title")
        self.assertEqual(dropped, {})
