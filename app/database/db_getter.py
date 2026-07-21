import pathlib
import random
import traceback
from datetime import datetime, timezone

from app.database.db_access import DBConnection
from app.database import db_queries
from app.database.media_metadata_collector import collect_mp4_files

SEASON_TITLE_BUILDER = f"'Season' || ' ' || season_index AS season_title"
SORT_ALPHABETICAL = "GLOB '[A-Za-z]*'"

# Library type key -> tag used by the scanner
LIBRARY_TAG_MAP = {
    "tv": "tv show",
    "movies": "movie",
    "books": "book",
}
LIBRARY_TITLES = {
    "tv": "TV Shows",
    "movies": "Movies",
    "books": "Books",
}


def build_tag_clause(table_name, tag_list, params):
    placeholders = ', '.join([f':tag_{i}' for i in range(len(tag_list))])
    for index, value in enumerate(tag_list):
        params[f'tag_{index}'] = value

    return f"INNER JOIN user_tags_content ON {table_name}.id = user_tags_content.{table_name}_id INNER JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id WHERE user_tags.tag_title IN ({placeholders}) GROUP BY {table_name}.id"


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DBHandler(DBConnection):

    def update_database(self, current_version):
        """Updates the database schema from current_version toward VERSION."""
        if current_version < 2:
            self._migrate_to_v2()

    def _migrate_to_v2(self):
        """Add playback progress columns for Continue Watching shelves."""
        migrations = [
            ("last_position", "ALTER TABLE content ADD COLUMN last_position REAL DEFAULT 0;"),
            ("last_played_at", "ALTER TABLE content ADD COLUMN last_played_at text DEFAULT '';"),
            ("last_duration", "ALTER TABLE content ADD COLUMN last_duration REAL DEFAULT 0;"),
        ]
        for column_name, alter_sql in migrations:
            if not self.table_has_column("content", column_name):
                self.execute_db_script([alter_sql])
                print(f"Migrated content: added {column_name}")

    def create_db(self):
        # Always ensure base tables exist (CREATE IF NOT EXISTS)
        db_table_creation_script = [
            db_queries.CREATE_CONTAINER_INFO_TABLE,
            db_queries.CREATE_CONTENT_INFO_TABLE,
            db_queries.CREATE_CONTAINER_CONTENT_INFO_TABLE,
            db_queries.CREATE_CONTAINER_CONTAINER_INFO_TABLE,
            db_queries.CREATE_CONTENT_DIRECTORY_INFO_TABLE,
            db_queries.CREATE_USER_TAGS_INFO_TABLE,
            db_queries.CREATE_USER_TAGS_CONTENT_INFO_TABLE,
        ]
        self.execute_db_script(db_table_creation_script)

        db_version = self.check_db_version()
        print(f"DB COMPARE: Current: {db_version}, Expected: {self.VERSION}")
        if db_version < self.VERSION:
            self.update_database(db_version)
            self.set_db_version(self.VERSION)
            print(f"DB migrated to version {self.VERSION}")

    def add_content_directory_info(self, content_directory_info):
        if media_directory_id := self.add_data_to_db(db_queries.SET_CONTENT_DIRECTORY_INFO_TABLE,
                                                     content_directory_info):
            content_directory_info["id"] = media_directory_id
            return True
        else:
            content_directory_info["id"] = self.get_row_id(db_queries.GET_CONTENT_DIRECTORY_INFO_ID,
                                                           content_directory_info)
            return False

    def get_all_content_directory_info(self):
        return self.get_data_from_db(db_queries.GET_CONTENT_DIRECTORY_INFO)

    def get_tag_id(self, tag):
        return self.get_row_id(db_queries.GET_USER_TAGS_INFO_ID, tag)

    def insert_tag(self, tag):
        tag["id"] = self.add_data_to_db(db_queries.SET_USER_TAGS_INFO_TABLE, tag)
        if not tag["id"]:
            tag["id"] = self.get_tag_id(tag)
        return tag["id"]

    def add_tag_to_container(self, params):
        self.add_data_to_db(db_queries.SET_USER_TAGS_CONTAINER_INFO_TABLE, params)

    def remove_tag_from_container(self, params):
        self.add_data_to_db(
            "DELETE FROM user_tags_content WHERE user_tags_id = :user_tags_id AND container_id = :container_id;",
            params)

    def add_tag_to_content(self, params):
        return self.add_data_to_db(db_queries.SET_USER_TAGS_CONTENT_INFO_TABLE, params)

    def remove_tag_from_content(self, params):
        self.add_data_to_db(
            "DELETE FROM user_tags_content WHERE user_tags_id = :user_tags_id AND content_id = :content_id;",
            params)

    def insert_container(self, container):
        if container_id := self.add_data_to_db(db_queries.SET_CONTAINER_INFO_TABLE, container):
            container["id"] = container_id
        else:
            container["id"] = self.get_row_id(db_queries.GET_CONTAINER_INFO_ID, container)
            # self.update_metadata()
        for tag in container.get("tags"):
            self.insert_tag(tag)
            self.add_tag_to_container({"user_tags_id": tag.get("id"), "container_id": container.get("id")})
        for container_content in container.get("container_content", []):
            if "container_content" in container_content:
                self.add_data_to_db(db_queries.SET_CONTAINER_CONTAINER_INFO_TABLE,
                                    {"parent_container_id": container.get("id"),
                                     "container_id": container_content.get("id"),
                                     "content_index": container_content.get("content_index")})
            else:
                self.add_data_to_db(db_queries.SET_CONTAINER_CONTENT_INFO_TABLE,
                                    {"parent_container_id": container.get("id"),
                                     "content_id": container_content.get("id"),
                                     "content_index": container_content.get("content_index")})
        # print(container)

    def insert_content(self, content):
        if content_id := self.add_data_to_db(db_queries.SET_CONTENT_INFO_TABLE, content):
            content["id"] = content_id
            for tag in content.get("tags"):
                self.insert_tag(tag)
                self.add_tag_to_content({"user_tags_id": tag.get("id"), "content_id": content.get("id")})

    def insert_container_content(self, container_content):
        if "container_content" in container_content:
            for content in container_content.get("container_content"):
                self.insert_container_content(content)
            self.insert_container(container_content)
        else:
            self.insert_content(container_content)

    def collect_directory_content(self, content_directory_info):
        print(f"Scanning directory: {content_directory_info}")
        for container_content in collect_mp4_files(content_directory_info):
            self.insert_container_content(container_content)

    def scan_content_directories(self):
        if content_directory_list := self.get_all_content_directory_info():
            print(f"Scanning: {content_directory_list}")
            for content_directory_info in content_directory_list:
                self.collect_directory_content(content_directory_info)
        print("Scan Complete")

    def setup_content_directory(self, content_directory_info):
        if self.add_content_directory_info(content_directory_info):
            self.collect_directory_content(content_directory_info)
        else:
            print(f"Content directory already added: {content_directory_info}")
        print("Setup Complete")

    def get_all_tags(self):
        return self.get_data_from_db("SELECT * FROM user_tags;")

    def get_all_content_paths(self):
        return self.get_data_from_db("SELECT id, content_src FROM content;")

    def get_all_image_paths(self):
        img_path_list = []
        img_path_list.extend(
            self.get_data_from_db("SELECT id AS content_id, img_src, content_src FROM content WHERE img_src != '';"))
        img_path_list.extend(
            self.get_data_from_db(
                "SELECT id AS container_id, img_src, container_path FROM container WHERE img_src != '';"))
        return img_path_list

    def get_content_img_path(self, content_id):
        return self.get_data_from_db_first_result(
            "SELECT content_directory.content_src || content.content_src AS path FROM content INNER JOIN content_directory ON content.content_directory_id = content_directory.id WHERE content.id = :id;",
            {'id': content_id})

    def get_container_img_path(self, container_id):
        return self.get_data_from_db_first_result(
            "SELECT img_src FROM container WHERE container.id = :id;",
            {'id': container_id})

    def check_if_content_src_exists(self, content_src):
        return self.get_data_from_db("SELECT * FROM content WHERE :content_src == content_src;", content_src)

    def check_if_container_src_exists(self, content_src):
        return self.get_data_from_db("SELECT * FROM container WHERE :container_path LIKE container_path;",
                                     {"container_path": f"%{content_src.get('container_path')}%"})

    def get_container_info(self, container_id):
        return self.get_data_from_db_first_result(
            "SELECT *, GROUP_CONCAT(user_tags.tag_title) AS user_tags FROM container LEFT JOIN user_tags_content ON container.id = user_tags_content.container_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id WHERE container.id = :id;",
            {'id': container_id})

    def get_content_info(self, content_id):
        return self.get_data_from_db_first_result(
            "SELECT *, content_directory.content_url || '/' || content.content_src AS url, content_directory.content_src || content.content_src AS path, GROUP_CONCAT(user_tags.tag_title) AS user_tags FROM content INNER JOIN content_directory ON content.content_directory_id = content_directory.id LEFT JOIN user_tags_content ON content.id = user_tags_content.content_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id WHERE content.id = :id;",
            {'id': content_id})

    def collect_all_sub_content(self, container_id, sub_content_list):
        content_query = f"SELECT * FROM content INNER JOIN container_content ON content.id = container_content.content_id WHERE container_content.parent_container_id = :id ORDER BY content_index ASC NULLS LAST, content_title {SORT_ALPHABETICAL};"
        sub_content_list.extend(self.get_data_from_db(content_query, {"id": container_id}))
        container_query = f"SELECT * FROM container INNER JOIN container_container ON container.id = container_container.container_id WHERE container_container.parent_container_id = :id GROUP BY container.id ORDER BY content_index ASC NULLS LAST, container_title {SORT_ALPHABETICAL};"
        for container in self.get_data_from_db(container_query, {"id": container_id}):
            self.collect_all_sub_content(container.get("id"), sub_content_list)

    def get_all_content_with_tags(self, tags_to_find, sub_content_list):
        # The list provided by your user
        # 1. Generate placeholders: ":tag0, :tag1, :tag2"
        placeholders = ", ".join([f":t{i}" for i in range(len(tags_to_find))])

        # 2. Map those placeholders to the actual values in a dictionary
        # e.g., {"t0": "Action", "t1": "Sci-Fi", ...}
        params = {f"t{i}": tag for i, tag in enumerate(tags_to_find)}

        # 3. Construct the query using the generated placeholders
        # We use DISTINCT to ensure a piece of content isn't listed twice
        # if it matches multiple tags in your list.
        tag_query = f"""
        SELECT DISTINCT c.*
        FROM content c
        JOIN user_tags_content utc ON c.id = utc.content_id
        JOIN user_tags ut ON utc.user_tags_id = ut.id
        WHERE ut.tag_title IN ({placeholders})
        ORDER BY c.content_title ASC;
        """

        # 4. Execute using your existing helper method
        sub_content_list.extend(self.get_data_from_db(tag_query, params))

    def get_next_content_in_container(self, json_request):
        sub_content_list = []
        next_content_id = None
        parent_container_id = None
        parent_containers = self.get_top_container(json_request.get("parent_container_id"))
        if parent_containers:
            parent_container_id = parent_containers[0].get("id")
            self.collect_all_sub_content(parent_container_id, sub_content_list)
        for index, sub_content in enumerate(sub_content_list):
            if sub_content.get("id") == json_request.get("content_id"):
                if index == len(sub_content_list) - 1:
                    next_content_id = sub_content_list[0].get("id")
                else:
                    next_content_id = sub_content_list[index + 1].get("id")

        if next_content_id:
            next_content_info = self.get_content_info(next_content_id)
            next_content_info["parent_container_id"] = parent_container_id
            return next_content_info

    def get_random_content_in_container(self, json_request):
        sub_content_list = []
        parent_container_id = None
        parent_containers = self.get_top_container(json_request.get("parent_container_id"))
        if parent_containers:
            parent_container_id = parent_containers[0].get("id")
            self.collect_all_sub_content(parent_container_id, sub_content_list)

        if sub_content_list:
            content_id = random.choice(sub_content_list).get("id")
            media_metadata = self.get_content_info(content_id)
            media_metadata["parent_container_id"] = parent_container_id
            return media_metadata

    def get_random_content_with_tag(self, tag_list):
        sub_content_list = []
        self.get_all_content_with_tags(tag_list, sub_content_list)
        if sub_content_list:
            content_id = random.choice(sub_content_list).get("id")
            media_metadata = self.get_content_info(content_id)
            media_metadata["tag_list"] = tag_list
            return media_metadata

    def get_previous_content_in_container(self, json_request):
        sub_content_list = []
        next_content_id = None
        parent_container_id = None
        parent_containers = self.get_top_container(json_request.get("parent_container_id"))
        if parent_containers:
            parent_container_id = parent_containers[0].get("id")
            self.collect_all_sub_content(parent_container_id, sub_content_list)
        for index, sub_content in enumerate(sub_content_list):
            if sub_content.get("id") == json_request.get("content_id"):
                if index == 0:
                    next_content_id = sub_content_list[-1].get("id")
                else:
                    next_content_id = sub_content_list[index - 1].get("id")

        if next_content_id:
            next_content_info = self.get_content_info(next_content_id)
            next_content_info["parent_container_id"] = parent_container_id
            return next_content_info

    def update_content_play_count(self, content_id):
        self.add_data_to_db(
            db_queries.UPDATE_CONTENT_PLAYED,
            {"id": content_id, "last_played_at": utc_now_iso()},
        )

    def update_playback_progress(self, content_id, position, duration=None):
        """Persist resume position for Continue Watching.

        When position is past 90% of duration (or caller passes a finished flag
        via position >= duration), reset last_position to 0 so the item drops
        off Continue Watching while still updating last_played_at.
        """
        if not content_id:
            return False
        try:
            position = float(position or 0)
        except (TypeError, ValueError):
            return False
        try:
            duration_val = float(duration) if duration not in (None, "") else 0.0
        except (TypeError, ValueError):
            duration_val = 0.0
        # Finished: clear resume point so Continue Watching drops the item
        if duration_val > 0 and position / duration_val >= 0.9:
            position = 0.0
        self.add_data_to_db(
            db_queries.UPDATE_CONTENT_PLAYBACK_PROGRESS,
            {
                "id": content_id,
                "last_position": position,
                "last_duration": duration_val,
                "last_played_at": utc_now_iso(),
            },
        )
        return True

    def _resolve_content_img_urls(self, items):
        """Fill img_url from content_directory when missing or empty."""
        directories = self.get_all_content_directory_info()
        for item in items:
            if item.get("img_url") and item.get("img_src"):
                # Prefer filesystem-verified URL when img_src is relative
                pass
            img_src = item.get("img_src") or ""
            if not img_src:
                item["img_url"] = item.get("img_url") or ""
                continue
            for media_directory in directories:
                try:
                    img_path = pathlib.Path(
                        f'{media_directory.get("content_src")}{img_src}'
                    )
                    if img_path.exists():
                        item["img_url"] = f'{media_directory.get("content_url")}{img_src}'
                        break
                except Exception:
                    continue
            if not item.get("img_url") and img_src:
                # Fall back to directory join from content row if present
                for media_directory in directories:
                    item["img_url"] = f'{media_directory.get("content_url")}/{img_src}'.replace(
                        "//", "/"
                    ).replace(":/", "://")
                    break
        return items

    def list_continue_watching(self, limit=20):
        items = self.get_data_from_db(
            db_queries.LIST_CONTINUE_WATCHING, {"limit": limit}
        )
        return self._resolve_content_img_urls(items)

    def list_recently_played(self, limit=20):
        items = self.get_data_from_db(
            db_queries.LIST_RECENTLY_PLAYED, {"limit": limit}
        )
        return self._resolve_content_img_urls(items)

    def list_recently_added(self, limit=20):
        items = self.get_data_from_db(
            db_queries.LIST_RECENTLY_ADDED, {"limit": limit}
        )
        return self._resolve_content_img_urls(items)

    def count_by_tag(self, tag_title, for_containers=False):
        query = (
            db_queries.COUNT_CONTAINERS_WITH_TAG
            if for_containers
            else db_queries.COUNT_CONTENT_WITH_TAG
        )
        row = self.get_data_from_db_first_result(query, {"tag_title": tag_title})
        return int(row.get("count") or 0)

    def get_library_summaries(self):
        libraries = []
        for key, tag in LIBRARY_TAG_MAP.items():
            # TV is container-oriented; movies/books are content
            for_containers = key == "tv"
            libraries.append(
                {
                    "key": key,
                    "title": LIBRARY_TITLES[key],
                    "tag": tag,
                    "count": self.count_by_tag(tag, for_containers=for_containers),
                }
            )
        return libraries

    def get_library_home(self, limit=20):
        return {
            "continue_watching": self.list_continue_watching(limit=limit),
            "recently_added": self.list_recently_added(limit=limit),
            "recently_played": self.list_recently_played(limit=limit),
            "libraries": self.get_library_summaries(),
        }

    def update_metadata(self, container_dict):
        if container_dict.get("container_id"):
            self.add_data_to_db(
                f"UPDATE container SET description=:description, img_src=:img_src WHERE id=:container_id;",
                container_dict)
        elif container_dict.get("content_id"):
            self.add_data_to_db(
                f"UPDATE content SET description=:description, img_src=:img_src WHERE id=:content_id;",
                container_dict)

    def get_top_container(self, container_id):
        parent_containers_query = "SELECT *, GROUP_CONCAT(user_tags.tag_title) AS user_tags FROM container LEFT JOIN container_container ON container.id = container_container.container_id LEFT JOIN user_tags_content ON container.id = user_tags_content.container_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id WHERE container.id = :id;"
        top_container_list = []
        params = {'id': container_id}
        top_container_list.append(self.get_data_from_db_first_result(parent_containers_query, params))
        while parent_id := top_container_list[0].get("parent_container_id"):
            top_container_list.insert(0, self.get_data_from_db_first_result(parent_containers_query,
                                                                            {'id': parent_id}))
        return top_container_list

    def query_container_tags(self, container_id):
        parent_containers_query = "SELECT GROUP_CONCAT(user_tags.tag_title) AS user_tags FROM container LEFT JOIN user_tags_content ON container.id = user_tags_content.container_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id WHERE container.id = :id;"
        params = {'id': container_id}
        return self.get_data_from_db_first_result(parent_containers_query, params)

    def query_content_tags(self, content_id):
        parent_containers_query = "SELECT GROUP_CONCAT(user_tags.tag_title) AS user_tags FROM content LEFT JOIN user_tags_content ON content.id = user_tags_content.content_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id WHERE content.id = :id;"
        params = {'id': content_id}
        return self.get_data_from_db_first_result(parent_containers_query, params)

    def query_container(self, tag_list, container_dict, container_txt_search):
        # DEFINE
        container_select_clauses = ["*", "CAST(SUBSTR(container_title, 7) AS INTEGER) AS season_index"]
        container_where_clauses = []
        container_join_clauses = []
        params = {}
        container_sort_order = f"ORDER BY season_index, container_title"

        # BUILD
        if tag_list:
            placeholders = ', '.join([f':tag_{i}' for i in range(len(tag_list))])
            for index, value in enumerate(tag_list):
                params[f'tag_{index}'] = value
            container_where_clauses.append(f"user_tags.tag_title IN ({placeholders})")

            container_select_clauses.append("GROUP_CONCAT(user_tags.tag_title) AS user_tags")
            container_join_clauses.append(
                "LEFT JOIN user_tags_content ON container.id = user_tags_content.container_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id")

        if container_dict.get("container_id"):
            container_join_clauses.append(
                "INNER JOIN container_container ON container.id = container_container.container_id")
            container_where_clauses.append("container_container.parent_container_id = :parent_container_id")
            container_sort_order = f"ORDER BY content_index ASC NULLS LAST, container_title {SORT_ALPHABETICAL}"

            params["parent_container_id"] = container_dict.get("container_id")

        if container_txt_search:
            container_where_clauses.append("container.container_title LIKE :container_txt_search")
            params["container_txt_search"] = f"%{container_txt_search}%"

        # COMBINE
        container_select_clause = ""
        if container_select_clauses:
            container_select_clause = ", ".join(container_select_clauses)

        container_join_clause = ""
        if container_join_clauses:
            container_join_clause = " ".join(container_join_clauses)

        container_where_clause = ""
        if container_where_clauses:
            container_where_clause = "WHERE " + " AND ".join(container_where_clauses)

        return self.get_data_from_db(
            f"SELECT {container_select_clause} FROM container {container_join_clause} {container_where_clause} GROUP BY container.id {container_sort_order};",
            params
        )

    def query_content(self, tag_list, container_dict, content_txt_search):
        # print(tag_list)
        # print(container_dict)
        # print()
        params = {}
        content_select_clauses = ["*"]
        content_where_clauses = []
        content_join_clauses = []
        content_sort_order = f"ORDER BY content_title"

        if tag_list:
            placeholders = ', '.join([f':tag_{i}' for i in range(len(tag_list))])
            for index, value in enumerate(tag_list):
                params[f'tag_{index}'] = value
            content_where_clauses.append(f"user_tags.tag_title IN ({placeholders})")

        content_select_clauses.append("GROUP_CONCAT(user_tags.tag_title) AS user_tags")
        content_join_clauses.append(
            "LEFT JOIN user_tags_content ON content.id = user_tags_content.content_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id")

        content_select_clauses.append("content_directory.content_url || '/' || content.img_src AS img_url")
        content_join_clauses.append(
            "INNER JOIN content_directory ON content.content_directory_id = content_directory.id")

        if container_dict.get("container_id"):
            content_join_clauses.append(
                "INNER JOIN container_content ON content.id = container_content.content_id")
            content_where_clauses.append("container_content.parent_container_id = :parent_container_id")
            content_sort_order = f"ORDER BY content_index ASC NULLS LAST, content_title {SORT_ALPHABETICAL}"
            params["parent_container_id"] = container_dict.get("container_id")

        if container_dict.get("content_id"):
            content_where_clauses.append("content.id = :content_id")
            params["content_id"] = container_dict.get("content_id")

        if content_txt_search:
            content_where_clauses.append("content.content_title LIKE :content_txt_search")
            params["content_txt_search"] = f"%{content_txt_search}%"

        content_select_clause = ""
        if content_select_clauses:
            content_select_clause = ", ".join(content_select_clauses)

        content_join_clause = ""
        if content_join_clauses:
            content_join_clause = " ".join(content_join_clauses)

        content_where_clause = ""
        if content_where_clauses:
            content_where_clause = "WHERE " + " AND ".join(content_where_clauses)

        return self.get_data_from_db(
            f"SELECT {content_select_clause} FROM content {content_join_clause} {content_where_clause} GROUP BY content.id {content_sort_order};",
            params
        )

    def _attach_container_img_urls(self, containers):
        directories = self.get_all_content_directory_info()
        for container in containers or []:
            if not container.get("img_src"):
                container["img_url"] = container.get("img_url") or ""
                continue
            for media_directory in directories:
                try:
                    img_path = pathlib.Path(
                        f'{media_directory.get("content_src")}{container.get("img_src")}'
                    )
                    if img_path.exists():
                        container["img_url"] = (
                            f'{media_directory.get("content_url")}{container.get("img_src")}'
                        )
                        break
                except Exception as e:
                    print("Exception class: ", e.__class__)
                    print(f"ERROR: {e}")
                    print(traceback.print_exc())
                    print(container)
                    container["img_url"] = ""
        return containers

    def query_db(self, tag_list, container_dict, container_txt_search, content_txt_search):
        ret_data = {}
        # When only one search field is set, keep legacy single-dimension browse.
        # When both are set (unified search) or neither is, return both kinds.
        include_containers = (not content_txt_search) or bool(container_txt_search)
        include_content = (not container_txt_search) or bool(content_txt_search)

        if include_containers:
            ret_data["containers"] = self.query_container(
                tag_list, container_dict, container_txt_search
            )
            self._attach_container_img_urls(ret_data.get("containers"))

        if include_content:
            ret_data["content"] = self.query_content(
                tag_list, container_dict, content_txt_search
            )
        if container_id := container_dict.get("container_id"):
            ret_data["parent_containers"] = self.get_top_container(container_id)
            self._attach_container_img_urls(ret_data.get("parent_containers"))

        return ret_data
