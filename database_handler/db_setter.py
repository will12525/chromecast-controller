import json

from .media_metadata_collector import collect_mp4_files

from . import common_objects
from .db_access import DBConnection

INSERT_IGNORE = 'INSERT OR IGNORE INTO'

CREATE_MEDIA_FOLDER_TABLE = f'''CREATE TABLE IF NOT EXISTS content_directory (
                                          id integer PRIMARY KEY,
                                          content_src text NOT NULL UNIQUE,
                                          content_url text NOT NULL UNIQUE
                                          );'''
SET_MEDIA_FOLDER = f'{INSERT_IGNORE} content_directory (content_src, content_url) VALUES (:content_src, :content_url);'
GET_MEDIA_FOLDER_ID_BY_SRC = f"SELECT id FROM content_directory WHERE content_src = :content_src;"
GET_MEDIA_FOLDER_BY_ID = f"SELECT * FROM content_directory WHERE id = :id;"
GET_ALL_MEDIA_FOLDERS = f"SELECT * FROM content_directory;"

CREATE_CONTAINER_TABLE = f'''CREATE TABLE IF NOT EXISTS container (
                                     id integer PRIMARY KEY,
                                     container_title text NOT NULL,
                                     container_path text,
                                     description text DEFAULT "",
                                     img_src text DEFAULT "",
                                     UNIQUE (container_title, container_path)
                                );'''
SET_CONTAINER_TABLE = f'{INSERT_IGNORE} container (container_title, container_path, description, img_src) VALUES (:container_title, :container_path, :description, :img_src);'
GET_CONTAINER_ID = f"SELECT id FROM container WHERE container_title = :container_title AND container_path = :container_path;"

CREATE_CONTENT_TABLE = f'''CREATE TABLE IF NOT EXISTS content (
                                    id integer PRIMARY KEY,
                                    content_directory_id integer,
                                    content_title text NOT NULL,
                                    content_src text NOT NULL UNIQUE,
                                    description text DEFAULT "",
                                    img_src text DEFAULT "",
                                    play_count integer DEFAULT 0,
                                    FOREIGN KEY (content_directory_id) REFERENCES content_directory (id)
                                );'''
SET_CONTENT_TABLE = f'{INSERT_IGNORE} content (content_directory_id, content_title, content_src, description, img_src) VALUES (:content_directory_id, :content_title, :content_src, :description, :img_src);'

CREATE_CONTAINER_CONTENT_TABLE = f'''CREATE TABLE IF NOT EXISTS container_content (
                                             id integer PRIMARY KEY,
                                             parent_container_id integer,
                                             content_id integer,
                                             content_index integer NOT NULL,
                                             FOREIGN KEY (parent_container_id) REFERENCES container (id),
                                             FOREIGN KEY (content_id) REFERENCES content (id),
                                             UNIQUE (parent_container_id, content_index, content_index)
                                         );'''
SET_CONTAINER_CONTENT_TABLE = f'{INSERT_IGNORE} container_content (parent_container_id, content_id, content_index) VALUES (:parent_container_id, :content_id, :content_index);'

CREATE_CONTAINER_CONTAINER_TABLE = f'''CREATE TABLE IF NOT EXISTS container_container (
                                             id integer PRIMARY KEY,
                                             parent_container_id integer,
                                             container_id integer,
                                             content_index integer NOT NULL,
                                             FOREIGN KEY (parent_container_id) REFERENCES container (id),
                                             FOREIGN KEY (container_id) REFERENCES container (id),
                                             UNIQUE (parent_container_id, container_id, content_index)
                                         );'''

SET_CONTAINER_CONTAINER_TABLE = f'{INSERT_IGNORE} container_container (parent_container_id, container_id, content_index) VALUES (:parent_container_id, :container_id, :content_index);'

CREATE_CONTAINER_TAGS_TABLE = f'''CREATE TABLE IF NOT EXISTS user_tags (
                                     id integer PRIMARY KEY,
                                     tag_title text NOT NULL UNIQUE
                                );'''

SET_TAG = f'{INSERT_IGNORE} user_tags (tag_title) VALUES (:tag_title);'
GET_TAG_ID_BY_TITLE = f"SELECT id FROM user_tags WHERE tag_title = :tag_title;"

CREATE_CONTENT_TAGS_TABLE = f'''CREATE TABLE IF NOT EXISTS user_tags_content (
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
SET_CONTENT_TAG = f'{INSERT_IGNORE} user_tags_content (user_tags_id, content_id) VALUES (:user_tags_id, :content_id);'
SET_CONTAINER_TAG = f'{INSERT_IGNORE} user_tags_content (user_tags_id, container_id) VALUES (:user_tags_id, :container_id);'
DEL_TAG_FROM_CONTENT = "DELETE FROM user_tags_content WHERE user_tags_id = :user_tags_id AND content_id = :content_id;"
DEL_TAG_FROM_CONTAINER = "DELETE FROM user_tags_content WHERE user_tags_id = :user_tags_id AND container_id = :container_id;"


class DBCreatorV2(DBConnection):

    def create_db(self):
        if self.VERSION != self.check_db_version():
            # Run db update procedure
            pass
        else:
            self.create_tables(''.join(['BEGIN;',
                                        CREATE_CONTAINER_TABLE,
                                        CREATE_CONTENT_TABLE,
                                        CREATE_CONTAINER_CONTENT_TABLE,
                                        CREATE_CONTAINER_CONTAINER_TABLE,
                                        CREATE_MEDIA_FOLDER_TABLE,
                                        CREATE_CONTAINER_TAGS_TABLE,
                                        CREATE_CONTENT_TAGS_TABLE,
                                        'COMMIT;']))

    def add_media_folder(self, media_folder):
        if media_folder_id := self.add_data_to_db(SET_MEDIA_FOLDER, media_folder):
            media_folder["id"] = media_folder_id
            return True
        else:
            media_folder["id"] = self.get_row_id(GET_MEDIA_FOLDER_ID_BY_SRC, media_folder)
            return False

    def get_all_media_folders(self):
        return self.get_data_from_db(GET_ALL_MEDIA_FOLDERS)

    def get_media_folder_info_by_id(self, media_folder_id):
        return self.get_data_from_db_first_result(GET_MEDIA_FOLDER_BY_ID, {"id": media_folder_id})

    def get_tag_id_by_title(self, tag):
        return self.get_row_id(GET_TAG_ID_BY_TITLE, tag)

    def insert_tag(self, tag):
        if tag_id := self.add_data_to_db(SET_TAG, tag):
            tag["id"] = tag_id
        else:
            tag["id"] = self.get_tag_id_by_title(tag)

    def add_tag_to_container(self, params):
        self.add_data_to_db(SET_CONTAINER_TAG, params)

    def remove_tag_from_container(self, params):
        self.add_data_to_db(DEL_TAG_FROM_CONTAINER, params)

    def add_tag_to_content(self, params):
        self.add_data_to_db(SET_CONTENT_TAG, params)

    def remove_tag_from_content(self, params):
        self.add_data_to_db(DEL_TAG_FROM_CONTENT, params)

    def insert_container(self, container):
        if container_id := self.add_data_to_db(SET_CONTAINER_TABLE, container):
            container["id"] = container_id
        else:
            container["id"] = self.get_row_id(GET_CONTAINER_ID, container)

        for tag in container.get("tags"):
            self.insert_tag(tag)
            self.add_tag_to_container({"user_tags_id": tag.get("id"), "container_id": container.get("id")})
        for container_content in container.get("container_content", []):
            if "container_content" in container_content:
                self.add_data_to_db(SET_CONTAINER_CONTAINER_TABLE,
                                    {"parent_container_id": container.get("id"),
                                     "container_id": container_content.get("id"),
                                     "content_index": container_content.get("content_index")})
            else:
                self.add_data_to_db(SET_CONTAINER_CONTENT_TABLE,
                                    {"parent_container_id": container.get("id"),
                                     "content_id": container_content.get("id"),
                                     "content_index": container_content.get("content_index")})
        # print(container)

    def insert_content(self, content):
        if content_id := self.add_data_to_db(SET_CONTENT_TABLE, content):
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
        if content_directory_list := self.get_all_media_folders():
            print(f"Scanning: {content_directory_list}")
            for content_directory_info in content_directory_list:
                self.collect_directory_content(content_directory_info)
        print("Scan Complete")

    def setup_content_directory(self, content_directory_info):
        if self.add_media_folder(content_directory_info):
            self.collect_directory_content(content_directory_info)
        else:
            print(f"Content directory already added: {content_directory_info}")
        print("Setup Complete")
