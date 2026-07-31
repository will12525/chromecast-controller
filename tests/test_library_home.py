"""Unit tests for library home shelves and playback progress (schema v2)."""
import os
import tempfile
import unittest
from unittest import mock

from app.database.db_access import DBType
from app.database.db_getter import DBHandler, LIBRARY_TAG_MAP
from app.utils import backend_handler


class TestLibraryHomeAndProgress(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test_library.db")
        self.db = DBHandler(db_type=DBType.PHYSICAL, file_name=self.db_path)
        self.db.open()
        self.db.create_db()
        self._seed()

    def tearDown(self):
        self.db.close()
        self._tmpdir.cleanup()

    def _seed(self):
        # content directory
        directory = {
            "content_src": "/media/test/",
            "content_url": "http://127.0.0.1:8000/",
        }
        self.db.add_content_directory_info(directory)
        self.dir_id = directory["id"]

        # three content rows
        movie_tag = {"tag_title": "movie"}
        self.db.insert_tag(movie_tag)
        for i, title in enumerate(["Alpha", "Beta", "Gamma"], start=1):
            content = {
                "content_directory_id": self.dir_id,
                "content_title": title,
                "content_src": f"/movies/{title} (200{i}).mp4",
                "description": "",
                "img_src": "",
                "tags": [],
            }
            self.db.insert_content(content)
            if not content.get("id"):
                row = self.db.get_data_from_db_first_result(
                    "SELECT id FROM content WHERE content_src = :content_src;",
                    {"content_src": content["content_src"]},
                )
                content["id"] = row.get("id")
            self.db.add_tag_to_content(
                {"user_tags_id": movie_tag["id"], "content_id": content["id"]}
            )
            setattr(self, f"content_{i}_id", content["id"])

        # tv show container for library counts + parent link for episodes
        container = {
            "container_title": "Demo Show",
            "container_path": "/tv_shows/Demo Show",
            "description": "",
            "img_src": "",
            "tags": [{"tag_title": "tv show"}],
            "container_content": [],
        }
        self.db.insert_container(container)
        self.container_id = container.get("id")
        if not self.container_id:
            row = self.db.get_data_from_db_first_result(
                "SELECT id FROM container WHERE container_path = :p;",
                {"p": container["container_path"]},
            )
            self.container_id = row.get("id")

        # Link content_1 as episode under the show (for parent_container_id on shelves)
        ep = {
            "content_directory_id": self.dir_id,
            "content_title": "Demo Show - s01e01",
            "content_src": "/tv_shows/Demo Show/Demo Show - s01e01.mp4",
            "description": "",
            "img_src": "",
            "tags": [],
        }
        self.db.insert_content(ep)
        if not ep.get("id"):
            row = self.db.get_data_from_db_first_result(
                "SELECT id FROM content WHERE content_src = :content_src;",
                {"content_src": ep["content_src"]},
            )
            ep["id"] = row.get("id")
        self.episode_id = ep["id"]
        self.db.add_data_to_db(
            "INSERT OR IGNORE INTO container_content (parent_container_id, content_id, content_index) "
            "VALUES (:parent_container_id, :content_id, :content_index);",
            {
                "parent_container_id": self.container_id,
                "content_id": self.episode_id,
                "content_index": 1,
            },
        )

    def test_schema_has_progress_columns(self):
        self.assertTrue(self.db.table_has_column("content", "last_position"))
        self.assertTrue(self.db.table_has_column("content", "last_played_at"))
        self.assertTrue(self.db.table_has_column("content", "last_duration"))
        self.assertTrue(self.db.table_has_column("content", "added_at"))
        self.assertEqual(self.db.check_db_version(), self.db.VERSION)
        self.assertEqual(self.db.VERSION, 3)

    def test_update_playback_progress_and_continue_watching(self):
        ok = self.db.update_playback_progress(self.content_1_id, 120, 600)
        self.assertTrue(ok)
        watching = self.db.list_continue_watching(limit=10)
        ids = [row["id"] for row in watching]
        self.assertIn(self.content_1_id, ids)

    def test_finished_item_excluded_from_continue_watching(self):
        # 95% watched should drop off Continue Watching (position cleared to 0)
        self.db.update_playback_progress(self.content_2_id, 570, 600)
        watching = self.db.list_continue_watching(limit=10)
        ids = [row["id"] for row in watching]
        self.assertNotIn(self.content_2_id, ids)
        row = self.db.get_data_from_db_first_result(
            "SELECT last_position, last_duration FROM content WHERE id = :id;",
            {"id": self.content_2_id},
        )
        self.assertEqual(float(row["last_position"] or 0), 0.0)
        self.assertEqual(float(row["last_duration"] or 0), 600.0)

    def test_mid_progress_kept_for_resume(self):
        self.db.update_playback_progress(self.content_1_id, 120, 600)
        row = self.db.get_data_from_db_first_result(
            "SELECT last_position FROM content WHERE id = :id;",
            {"id": self.content_1_id},
        )
        self.assertEqual(float(row["last_position"]), 120.0)

    def test_continue_watching_includes_parent_container_id(self):
        self.db.update_playback_progress(self.episode_id, 90, 600)
        watching = self.db.list_continue_watching(limit=10)
        match = next((row for row in watching if row["id"] == self.episode_id), None)
        self.assertIsNotNone(match)
        self.assertEqual(match.get("parent_container_id"), self.container_id)

    def test_recently_played(self):
        self.db.update_content_play_count(self.content_3_id)
        played = self.db.list_recently_played(limit=10)
        ids = [row["id"] for row in played]
        self.assertIn(self.content_3_id, ids)

    def test_recently_added_orders_by_added_at(self):
        # Override stamps so order is by added_at, not insert id
        self.db.add_data_to_db(
            "UPDATE content SET added_at = :t WHERE id = :id;",
            {"id": self.content_1_id, "t": "2020-01-01T00:00:00+00:00"},
        )
        self.db.add_data_to_db(
            "UPDATE content SET added_at = :t WHERE id = :id;",
            {"id": self.content_2_id, "t": "2024-06-01T00:00:00+00:00"},
        )
        self.db.add_data_to_db(
            "UPDATE content SET added_at = :t WHERE id = :id;",
            {"id": self.content_3_id, "t": "2022-01-01T00:00:00+00:00"},
        )
        added = self.db.list_recently_added(limit=10)
        ids = [row["id"] for row in added]
        # Newest added_at first among the three movies
        movie_order = [i for i in ids if i in (self.content_1_id, self.content_2_id, self.content_3_id)]
        self.assertEqual(
            movie_order[:3],
            [self.content_2_id, self.content_3_id, self.content_1_id],
        )

    def test_insert_content_stamps_added_at(self):
        content = {
            "content_directory_id": self.dir_id,
            "content_title": "Delta",
            "content_src": "/movies/Delta (2025).mp4",
            "description": "",
            "img_src": "",
            "tags": [],
        }
        self.db.insert_content(content)
        self.assertTrue(content.get("id"))
        row = self.db.get_data_from_db_first_result(
            "SELECT added_at FROM content WHERE id = :id;",
            {"id": content["id"]},
        )
        self.assertTrue(row.get("added_at"))
        self.assertIn("T", row["added_at"])

    def test_rescans_keep_original_added_at(self):
        content = {
            "content_directory_id": self.dir_id,
            "content_title": "Echo",
            "content_src": "/movies/Echo (2019).mp4",
            "description": "",
            "img_src": "",
            "tags": [],
            "added_at": "2019-05-05T12:00:00+00:00",
        }
        self.db.insert_content(content)
        cid = content["id"]
        # Second insert with same unique content_src is ignored; stamp must stay
        again = {
            "content_directory_id": self.dir_id,
            "content_title": "Echo",
            "content_src": "/movies/Echo (2019).mp4",
            "description": "",
            "img_src": "",
            "tags": [],
            "added_at": "2099-01-01T00:00:00+00:00",
        }
        self.db.insert_content(again)
        row = self.db.get_data_from_db_first_result(
            "SELECT added_at FROM content WHERE content_src = :s;",
            {"s": "/movies/Echo (2019).mp4"},
        )
        self.assertEqual(row["added_at"], "2019-05-05T12:00:00+00:00")
        self.assertEqual(cid, self.db.get_data_from_db_first_result(
            "SELECT id FROM content WHERE content_src = :s;",
            {"s": "/movies/Echo (2019).mp4"},
        )["id"])

    def test_library_home_shape(self):
        home = self.db.get_library_home(limit=5)
        self.assertIn("continue_watching", home)
        self.assertIn("recently_added", home)
        self.assertIn("recently_played", home)
        self.assertIn("libraries", home)
        keys = {lib["key"] for lib in home["libraries"]}
        self.assertEqual(keys, set(LIBRARY_TAG_MAP.keys()))
        movies = next(lib for lib in home["libraries"] if lib["key"] == "movies")
        self.assertGreaterEqual(movies["count"], 3)
        tv = next(lib for lib in home["libraries"] if lib["key"] == "tv")
        self.assertGreaterEqual(tv["count"], 1)

    def test_migration_from_v1(self):
        """Create a v1-shaped table and migrate through v2 to v3."""
        path = os.path.join(self._tmpdir.name, "legacy.db")
        legacy = DBHandler(db_type=DBType.PHYSICAL, file_name=path)
        legacy.open()
        # Force v1 content table without progress / added_at columns
        legacy.execute_db_script(
            [
                """CREATE TABLE IF NOT EXISTS content (
                    id integer PRIMARY KEY,
                    content_directory_id integer NOT NULL,
                    content_title text NOT NULL,
                    content_src text NOT NULL UNIQUE,
                    description text DEFAULT '',
                    img_src text DEFAULT '',
                    play_count integer DEFAULT 0
                );""",
                """CREATE TABLE IF NOT EXISTS version_info (
                    id integer PRIMARY KEY,
                    version integer NOT NULL
                );""",
                "INSERT INTO version_info(version) VALUES(1);",
                "INSERT INTO content (content_directory_id, content_title, content_src) "
                "VALUES (1, 'Legacy', '/movies/Legacy (2000).mp4');",
            ]
        )
        legacy.create_db()
        self.assertTrue(legacy.table_has_column("content", "last_position"))
        self.assertTrue(legacy.table_has_column("content", "added_at"))
        self.assertEqual(legacy.check_db_version(), 3)
        row = legacy.get_data_from_db_first_result(
            "SELECT added_at FROM content WHERE content_title = 'Legacy';",
            {},
        )
        self.assertTrue(row.get("added_at"))
        legacy.close()


class TestScanMediaGuard(unittest.TestCase):
    """Concurrent scan returns busy without starting a second walk."""

    def test_scan_busy_when_already_running(self):
        handler = object.__new__(backend_handler.BackEndHandler)
        handler.media_scan_in_progress = True
        result = handler.scan_media_directories()
        self.assertEqual(result["status"], "busy")
        self.assertIn("progress", result["message"].lower())

    def test_scan_ok_returns_status_dict(self):
        handler = object.__new__(backend_handler.BackEndHandler)
        handler.media_scan_in_progress = False
        mock_db = mock.MagicMock()
        with mock.patch.object(backend_handler, "DBHandler", return_value=mock_db):
            result = handler.scan_media_directories()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["message"], "Scan complete")
        mock_db.open.assert_called_once()
        mock_db.scan_content_directories.assert_called_once()
        mock_db.close.assert_called_once()
        self.assertFalse(handler.media_scan_in_progress)

    def test_scan_error_clears_flag(self):
        handler = object.__new__(backend_handler.BackEndHandler)
        handler.media_scan_in_progress = False
        mock_db = mock.MagicMock()
        mock_db.scan_content_directories.side_effect = RuntimeError("disk gone")
        with mock.patch.object(backend_handler, "DBHandler", return_value=mock_db):
            result = handler.scan_media_directories()
        self.assertEqual(result["status"], "error")
        self.assertIn("disk gone", result["message"])
        self.assertFalse(handler.media_scan_in_progress)

    def test_scan_status_shape_matches_api_contract(self):
        """Document expected /scan_status payload used by the UI."""
        handler = object.__new__(backend_handler.BackEndHandler)
        handler.media_scan_in_progress = False
        handler.transfer_in_progress = False
        handler.last_scan_result = None
        payload = handler.get_scan_status()
        self.assertEqual(payload["status"], "idle")
        handler.media_scan_in_progress = True
        payload = handler.get_scan_status()
        self.assertEqual(payload["status"], "busy")
        self.assertTrue(payload["scanning"])

    def test_start_scan_async_returns_started_and_sets_result(self):
        handler = object.__new__(backend_handler.BackEndHandler)
        handler.media_scan_in_progress = False
        handler.transfer_in_progress = False
        handler.last_scan_result = None
        handler._scan_lock = __import__("threading").Lock()
        mock_db = mock.MagicMock()
        with mock.patch.object(backend_handler, "DBHandler", return_value=mock_db):
            result = handler.start_scan_media_directories(run_client_sync=False)
            self.assertEqual(result["status"], "started")
            # Wait briefly for daemon thread
            import time
            for _ in range(50):
                if not handler.media_scan_in_progress and handler.last_scan_result:
                    break
                time.sleep(0.02)
        self.assertFalse(handler.media_scan_in_progress)
        self.assertEqual(handler.last_scan_result["status"], "ok")
        status = handler.get_scan_status()
        self.assertEqual(status["status"], "idle")
        self.assertEqual(status["last_result"]["message"], "Scan complete")

    def test_start_scan_async_busy_when_running(self):
        handler = object.__new__(backend_handler.BackEndHandler)
        handler.media_scan_in_progress = True
        handler.transfer_in_progress = False
        handler._scan_lock = __import__("threading").Lock()
        result = handler.start_scan_media_directories()
        self.assertEqual(result["status"], "busy")


if __name__ == "__main__":
    unittest.main()
