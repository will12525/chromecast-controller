import json

from .media_metadata_collector import collect_mp4_files

from . import common_objects
from .db_access import DBConnection

INSERT_IGNORE = 'INSERT OR IGNORE INTO'

CREATE_CONTENT_DIRECTORY_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS content_directory (
                                          id integer PRIMARY KEY,
                                          content_src text NOT NULL UNIQUE,
                                          content_url text NOT NULL UNIQUE
                                          );'''
SET_CONTENT_DIRECTORY_INFO_TABLE = f'{INSERT_IGNORE} content_directory (content_src, content_url) VALUES (:content_src, :content_url);'
GET_CONTENT_DIRECTORY_INFO_ID = f"SELECT id FROM content_directory WHERE content_src = :content_src;"
GET_CONTENT_DIRECTORY_INFO = f"SELECT * FROM content_directory;"

CREATE_CONTAINER_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS container (
                                     id integer PRIMARY KEY,
                                     container_title text NOT NULL,
                                     container_path text,
                                     description text DEFAULT "",
                                     img_src text DEFAULT "",
                                     UNIQUE (container_title, container_path)
                                );'''
SET_CONTAINER_INFO_TABLE = f'{INSERT_IGNORE} container (container_title, container_path, description, img_src) VALUES (:container_title, :container_path, :description, :img_src);'
GET_CONTAINER_INFO_ID = f"SELECT id FROM container WHERE container_title = :container_title AND container_path = :container_path;"

CREATE_CONTENT_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS content (
                                    id integer PRIMARY KEY,
                                    content_directory_id integer,
                                    content_title text NOT NULL,
                                    content_src text NOT NULL UNIQUE,
                                    description text DEFAULT "",
                                    img_src text DEFAULT "",
                                    play_count integer DEFAULT 0,
                                    FOREIGN KEY (content_directory_id) REFERENCES content_directory (id)
                                );'''
SET_CONTENT_INFO_TABLE = f'{INSERT_IGNORE} content (content_directory_id, content_title, content_src, description, img_src) VALUES (:content_directory_id, :content_title, :content_src, :description, :img_src);'

CREATE_CONTAINER_CONTENT_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS container_content (
                                             id integer PRIMARY KEY,
                                             parent_container_id integer,
                                             content_id integer,
                                             content_index integer NOT NULL,
                                             FOREIGN KEY (parent_container_id) REFERENCES container (id),
                                             FOREIGN KEY (content_id) REFERENCES content (id)
                                         );'''
SET_CONTAINER_CONTENT_INFO_TABLE = f'{INSERT_IGNORE} container_content (parent_container_id, content_id, content_index) VALUES (:parent_container_id, :content_id, :content_index);'

CREATE_CONTAINER_CONTAINER_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS container_container (
                                             id integer PRIMARY KEY,
                                             parent_container_id integer,
                                             container_id integer,
                                             content_index integer NOT NULL,
                                             FOREIGN KEY (parent_container_id) REFERENCES container (id),
                                             FOREIGN KEY (container_id) REFERENCES container (id)
                                         );'''

SET_CONTAINER_CONTAINER_INFO_TABLE = f'{INSERT_IGNORE} container_container (parent_container_id, container_id, content_index) VALUES (:parent_container_id, :container_id, :content_index);'

CREATE_USER_TAGS_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS user_tags (
                                     id integer PRIMARY KEY,
                                     tag_title text NOT NULL UNIQUE
                                );'''

SET_USER_TAGS_INFO_TABLE = f'{INSERT_IGNORE} user_tags (tag_title) VALUES (:tag_title);'
GET_USER_TAGS_INFO_ID = f"SELECT id FROM user_tags WHERE tag_title = :tag_title;"

CREATE_USER_TAGS_CONTENT_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS user_tags_content (
                                          id integer PRIMARY KEY,
                                          user_tags_id integer NOT NULL,
                                          container_id integer,
                                          content_id integer,
                                          FOREIGN KEY (user_tags_id) REFERENCES user_tags (id),
                                          FOREIGN KEY (container_id) REFERENCES container (id),
                                          FOREIGN KEY (content_id) REFERENCES content (id),
                                          UNIQUE (user_tags_id, container_id),
                                          UNIQUE (user_tags_id, content_id)
                                         );'''
SET_USER_TAGS_CONTENT_INFO_TABLE = f'{INSERT_IGNORE} user_tags_content (user_tags_id, content_id) VALUES (:user_tags_id, :content_id);'
SET_USER_TAGS_CONTAINER_INFO_TABLE = f'{INSERT_IGNORE} user_tags_content (user_tags_id, container_id) VALUES (:user_tags_id, :container_id);'


class DBCreatorV2(DBConnection):

    def create_db(self):
        if self.VERSION != self.check_db_version():
            # Run db update procedure
            pass
        db_table_creation_script = ''.join(['BEGIN;',
                                            CREATE_CONTAINER_INFO_TABLE,
                                            CREATE_CONTENT_INFO_TABLE,
                                            CREATE_CONTAINER_CONTENT_INFO_TABLE,
                                            CREATE_CONTAINER_CONTAINER_INFO_TABLE,
                                            CREATE_CONTENT_DIRECTORY_INFO_TABLE,
                                            CREATE_USER_TAGS_INFO_TABLE,
                                            CREATE_USER_TAGS_CONTENT_INFO_TABLE,
                                            'COMMIT;'])
        self.create_tables(db_table_creation_script)

    def add_content_directory_info(self, content_directory_info):
        if media_directory_id := self.add_data_to_db(SET_CONTENT_DIRECTORY_INFO_TABLE, content_directory_info):
            content_directory_info["id"] = media_directory_id
        else:
            content_directory_info["id"] = self.get_row_id(GET_CONTENT_DIRECTORY_INFO_ID, content_directory_info)

    def get_all_content_directory_info(self):
        return self.get_data_from_db(GET_CONTENT_DIRECTORY_INFO)

    def get_tag_id(self, tag):
        return self.get_row_id(GET_USER_TAGS_INFO_ID, tag)

    def insert_tag(self, tag):
        if tag_id := self.add_data_to_db(SET_USER_TAGS_INFO_TABLE, tag):
            tag["id"] = tag_id
        else:
            tag["id"] = self.get_tag_id(tag)

    def add_tag_to_container(self, params):
        self.add_data_to_db(SET_USER_TAGS_CONTAINER_INFO_TABLE, params)

    def remove_tag_from_container(self, params):
        self.add_data_to_db(
            "DELETE FROM user_tags_content WHERE user_tags_id = :user_tags_id AND container_id = :container_id;",
            params)

    def add_tag_to_content(self, params):
        self.add_data_to_db(SET_USER_TAGS_CONTENT_INFO_TABLE, params)

    def remove_tag_from_content(self, params):
        self.add_data_to_db(
            "DELETE FROM user_tags_content WHERE user_tags_id = :user_tags_id AND content_id = :content_id;",
            params)

    def insert_container(self, container):
        if container_id := self.add_data_to_db(SET_CONTAINER_INFO_TABLE, container):
            container["id"] = container_id
        else:
            container["id"] = self.get_row_id(GET_CONTAINER_INFO_ID, container)

        for tag in container.get("tags"):
            self.insert_tag(tag)
            self.add_tag_to_container({"user_tags_id": tag["id"], "container_id": container["id"]})
        for container_content in container.get("container_content", []):
            if "container_content" in container_content:
                self.add_data_to_db(SET_CONTAINER_CONTAINER_INFO_TABLE,
                                    {"parent_container_id": container["id"], "container_id": container_content["id"],
                                     "content_index": container_content["content_index"]})
            else:
                self.add_data_to_db(SET_CONTAINER_CONTENT_INFO_TABLE,
                                    {"parent_container_id": container["id"], "content_id": container_content["id"],
                                     "content_index": container_content["content_index"]})
        # print(container)

    def insert_content(self, content):
        content["id"] = self.add_data_to_db(SET_CONTENT_INFO_TABLE, content)
        for tag in content.get("tags"):
            self.insert_tag(tag)
            self.add_tag_to_content({"user_tags_id": tag["id"], "content_id": content["id"]})

    def insert_container_content(self, container_content):
        if "container_content" in container_content:
            for content in container_content.get("container_content"):
                self.insert_container_content(content)
            self.insert_container(container_content)
        else:
            self.insert_content(container_content)

    def collect_directory_content(self, content_directory_info):
        for container_content in collect_mp4_files(content_directory_info):
            self.insert_container_content(container_content)

    def scan_content_directories(self):
        if content_directory_list := self.get_all_content_directory_info():
            print(content_directory_list)
            for content_directory_info in content_directory_list:
                self.collect_directory_content(content_directory_info)
        print("Scan Complete")

    def setup_content_directory(self, content_directory_info):
        if not self.get_row_id(GET_CONTENT_DIRECTORY_INFO_ID, content_directory_info):
            self.add_content_directory_info(content_directory_info)
            self.collect_directory_content(content_directory_info)
        print("Setup Complete")


sql_create_user_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.MEDIA_DIRECTORY_TABLE} (
                                        {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                        {common_objects.MEDIA_TYPE_COLUMN} integer NOT NULL,
                                        {common_objects.MEDIA_DIRECTORY_PATH_COLUMN} text NOT NULL UNIQUE,
                                        {common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN} text,
                                        {common_objects.MEDIA_DIRECTORY_URL_COLUMN} text NOT NULL UNIQUE
                                     );'''

sql_insert_user_info_table = f'{INSERT_IGNORE} {common_objects.MEDIA_DIRECTORY_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.MEDIA_TYPE_COLUMN}, :{common_objects.MEDIA_DIRECTORY_PATH_COLUMN}, :{common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN}, :{common_objects.MEDIA_DIRECTORY_URL_COLUMN});'
