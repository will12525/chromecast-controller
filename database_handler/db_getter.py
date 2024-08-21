import json
import pathlib

from .common_objects import ContentType
from . import common_objects
from .db_access import DBConnection

SEASON_TITLE_BUILDER = f"'Season' || ' ' || {common_objects.SEASON_INDEX_COLUMN} AS season_title"
SORT_ALPHABETICAL = "GLOB '[A-Za-z]*'"


class DatabaseHandlerV2(DBConnection):

    def build_tag_clause(self, table_name, tag_list, params):
        placeholders = ', '.join([f':tag_{i}' for i in range(len(tag_list))])
        for index, value in enumerate(tag_list):
            params[f'tag_{index}'] = value

        return f"INNER JOIN user_tags_content ON {table_name}.id = user_tags_content.{table_name}_id INNER JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id WHERE user_tags.tag_title IN ({placeholders}) GROUP BY {table_name}.id"

    def get_all_tags(self):
        return self.get_data_from_db("SELECT * FROM user_tags;")

    def get_container_info(self, container_id):
        return self.get_data_from_db_first_result(
            "SELECT *, GROUP_CONCAT(user_tags.tag_title) AS user_tags FROM container LEFT JOIN user_tags_content ON container.id = user_tags_content.container_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id WHERE container.id = :id;",
            {'id': container_id})

    def get_content_info(self, content_id):
        return self.get_data_from_db_first_result(
            "SELECT *, content_directory.content_url || '/' || content.content_src AS url, GROUP_CONCAT(user_tags.tag_title) AS user_tags FROM content INNER JOIN content_directory ON content.content_directory_id = content_directory.id LEFT JOIN user_tags_content ON content.id = user_tags_content.content_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id WHERE content.id = :id;",
            {'id': content_id})

    def collect_all_sub_content(self, container_id, sub_content_list):
        content_query = f"SELECT * FROM content INNER JOIN container_content ON content.id = container_content.content_id WHERE container_content.parent_container_id = :id ORDER BY content_index ASC NULLS LAST, content_title {SORT_ALPHABETICAL};"
        sub_content_list.extend(self.get_data_from_db(content_query, {"id": container_id}))
        container_query = f"SELECT * FROM container INNER JOIN container_container ON container.id = container_container.container_id WHERE container_container.parent_container_id = :id GROUP BY container.id ORDER BY content_index ASC NULLS LAST, container_title {SORT_ALPHABETICAL};"
        for container in self.get_data_from_db(container_query, {"id": container_id}):
            self.collect_all_sub_content(container.get("id"), sub_content_list)

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
        UPDATE_MEDIA_PLAY_COUNT = f"UPDATE content SET play_count = play_count + 1 WHERE id=:id;"
        self.add_data_to_db(UPDATE_MEDIA_PLAY_COUNT, {"id": content_id})

    def update_metadata(self, container_dict):
        if container_dict.get("container_id"):
            self.add_data_to_db(
                f"UPDATE container SET {common_objects.DESCRIPTION}=:{common_objects.DESCRIPTION}, img_src=:img_src WHERE id=:container_id;",
                container_dict)
        elif container_dict.get("content_id"):
            self.add_data_to_db(
                f"UPDATE content SET {common_objects.DESCRIPTION}=:{common_objects.DESCRIPTION}, img_src=:img_src WHERE id=:content_id;",
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

    def query_content(
            self,
            tag_list,
            container_dict
    ):
        # print(tag_list)
        # print(container_dict)
        # print()
        ret_data = {}
        params = {}
        container_select_clauses = ["*", "CAST(SUBSTR(container_title, 7) AS INTEGER) AS season_index"]
        content_select_clauses = ["*"]
        container_where_clauses = []
        content_where_clauses = []
        container_join_clauses = []
        content_join_clauses = []
        container_sort_order = f"ORDER BY season_index, container_title"
        content_sort_order = f"ORDER BY content_title"

        if tag_list:
            placeholders = ', '.join([f':tag_{i}' for i in range(len(tag_list))])
            for index, value in enumerate(tag_list):
                params[f'tag_{index}'] = value
            container_where_clauses.append(f"user_tags.tag_title IN ({placeholders})")
            content_where_clauses.append(f"user_tags.tag_title IN ({placeholders})")

        container_select_clauses.append("GROUP_CONCAT(user_tags.tag_title) AS user_tags")
        container_join_clauses.append(
            "LEFT JOIN user_tags_content ON container.id = user_tags_content.container_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id")

        content_select_clauses.append("GROUP_CONCAT(user_tags.tag_title) AS user_tags")
        content_join_clauses.append(
            "LEFT JOIN user_tags_content ON content.id = user_tags_content.content_id LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id")

        if container_dict.get("container_id"):
            container_join_clauses.append(
                "INNER JOIN container_container ON container.id = container_container.container_id")
            container_where_clauses.append("container_container.parent_container_id = :parent_container_id")
            container_sort_order = f"ORDER BY content_index ASC NULLS LAST, container_title {SORT_ALPHABETICAL}"

            content_join_clauses.append(
                "INNER JOIN container_content ON content.id = container_content.content_id")
            content_where_clauses.append("container_content.parent_container_id = :parent_container_id")
            content_sort_order = f"ORDER BY content_index ASC NULLS LAST, content_title {SORT_ALPHABETICAL}"
            params["parent_container_id"] = container_dict.get("container_id")

        if container_dict.get("content_id"):
            content_where_clauses.append("content.id = :content_id")
            params["content_id"] = container_dict.get("content_id")

        container_select_clause = ""
        if container_select_clauses:
            container_select_clause = ", ".join(container_select_clauses)

        container_join_clause = ""
        if container_join_clauses:
            container_join_clause = " ".join(container_join_clauses)

        container_where_clause = ""
        if container_where_clauses:
            container_where_clause = "WHERE " + " AND ".join(container_where_clauses)

        content_select_clause = ""
        if content_select_clauses:
            content_select_clause = ", ".join(content_select_clauses)

        content_join_clause = ""
        if content_join_clauses:
            content_join_clause = " ".join(content_join_clauses)

        content_where_clause = ""
        if content_where_clauses:
            content_where_clause = "WHERE " + " AND ".join(content_where_clauses)

        ret_data["containers"] = self.get_data_from_db(
            f"SELECT {container_select_clause} FROM container {container_join_clause} {container_where_clause} GROUP BY container.id {container_sort_order};",
            params
        )
        ret_data["content"] = self.get_data_from_db(
            f"SELECT {content_select_clause} FROM content {content_join_clause} {content_where_clause} GROUP BY content.id {content_sort_order};",
            params
        )

        if container_id := container_dict.get("container_id"):
            ret_data["parent_containers"] = self.get_top_container(container_id)

        return ret_data
