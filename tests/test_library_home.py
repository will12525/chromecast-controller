"""Unit tests for library home shelves and playback progress (schema v2)."""
import os
import tempfile
import unittest

from app.database.db_access import DBType
from app.database.db_getter import DBHandler, LIBRARY_TAG_MAP


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

        # tv show container for library counts
        container = {
            "container_title": "Demo Show",
            "container_path": "/tv_shows/Demo Show",
            "description": "",
            "img_src": "",
            "tags": [{"tag_title": "tv show"}],
            "container_content": [],
        }
        self.db.insert_container(container)

    def test_schema_has_progress_columns(self):
        self.assertTrue(self.db.table_has_column("content", "last_position"))
        self.assertTrue(self.db.table_has_column("content", "last_played_at"))
        self.assertTrue(self.db.table_has_column("content", "last_duration"))
        self.assertEqual(self.db.check_db_version(), self.db.VERSION)

    def test_update_playback_progress_and_continue_watching(self):
        ok = self.db.update_playback_progress(self.content_1_id, 120, 600)
        self.assertTrue(ok)
        watching = self.db.list_continue_watching(limit=10)
        ids = [row["id"] for row in watching]
        self.assertIn(self.content_1_id, ids)

    def test_finished_item_excluded_from_continue_watching(self):
        # 95% watched should drop off Continue Watching
        self.db.update_playback_progress(self.content_2_id, 570, 600)
        watching = self.db.list_continue_watching(limit=10)
        ids = [row["id"] for row in watching]
        self.assertNotIn(self.content_2_id, ids)

    def test_recently_played(self):
        self.db.update_content_play_count(self.content_3_id)
        played = self.db.list_recently_played(limit=10)
        ids = [row["id"] for row in played]
        self.assertIn(self.content_3_id, ids)

    def test_recently_added_orders_by_id_desc(self):
        added = self.db.list_recently_added(limit=10)
        self.assertGreaterEqual(len(added), 3)
        ids = [row["id"] for row in added]
        self.assertEqual(ids, sorted(ids, reverse=True)[: len(ids)])

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
        """Create a v1-shaped table and migrate."""
        path = os.path.join(self._tmpdir.name, "legacy.db")
        legacy = DBHandler(db_type=DBType.PHYSICAL, file_name=path)
        legacy.open()
        # Force v1 content table without progress columns
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
            ]
        )
        legacy.create_db()
        self.assertTrue(legacy.table_has_column("content", "last_position"))
        self.assertEqual(legacy.check_db_version(), 2)
        legacy.close()


if __name__ == "__main__":
    unittest.main()
