import json

from .media_metadata_collector import collect_mp4_files, collect_tv_shows, collect_movies, get_extra_metadata

from .common_objects import ContentType
from . import common_objects
from .db_access import DBConnection

# playlist_info and media_info are the sources

INSERT_IGNORE = 'INSERT OR IGNORE INTO'

CREATE_CONTENT_DIRECTORY_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS content_directory (
                                          id integer PRIMARY KEY,
                                          content_src text NOT NULL UNIQUE,
                                          content_url text NOT NULL UNIQUE
                                          );'''
SET_CONTENT_DIRECTORY_INFO_TABLE = f'{INSERT_IGNORE} content_directory (content_src, content_url) VALUES (:content_src, :content_url);'
GET_CONTENT_DIRECTORY_INFO_ID = f"SELECT id FROM content_directory WHERE content_src = :content_src;"

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
                                    FOREIGN KEY (content_directory_id) REFERENCES content_directory (id)
                                );'''
SET_CONTENT_INFO_TABLE = f'{INSERT_IGNORE} content (content_directory_id, content_title, content_src, description, img_src) VALUES (:content_directory_id, :content_title, :content_src, :description, :img_src);'

CREATE_CONTAINER_CONTENT_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS container_content (
                                             id integer PRIMARY KEY,
                                             parent_container_id integer,
                                             container_id integer,
                                             content_id integer,
                                             content_index integer NOT NULL,
                                             FOREIGN KEY (parent_container_id) REFERENCES container (id),
                                             FOREIGN KEY (container_id) REFERENCES container (id),
                                             FOREIGN KEY (content_id) REFERENCES content (id)
                                         );'''

SET_CONTAINER_CONTENT_INFO_TABLE = f'{INSERT_IGNORE} container_content (parent_container_id, content_id, content_index) VALUES (:parent_container_id, :content_id, :content_index);'
SET_CONTAINER_CONTAINER_INFO_TABLE = f'{INSERT_IGNORE} container_content (parent_container_id, container_id, content_index) VALUES (:parent_container_id, :container_id, :content_index);'

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

    def insert_tag(self, tag):
        if tag_id := self.add_data_to_db(SET_USER_TAGS_INFO_TABLE, tag):
            tag["id"] = tag_id
        else:
            tag["id"] = self.get_row_id(GET_USER_TAGS_INFO_ID, tag)

    def insert_container(self, container):
        if container_id := self.add_data_to_db(SET_CONTAINER_INFO_TABLE, container):
            container["id"] = container_id
        else:
            container["id"] = self.get_row_id(GET_CONTAINER_INFO_ID, container)

        for tag in container.get("tags"):
            self.insert_tag(tag)
            self.add_data_to_db(SET_USER_TAGS_CONTAINER_INFO_TABLE,
                                {"user_tags_id": tag["id"], "container_id": container["id"]})
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
            self.add_data_to_db(SET_USER_TAGS_CONTENT_INFO_TABLE,
                                {"user_tags_id": tag["id"], "content_id": content["id"]})

    def insert_container_content(self, container_content):
        if "container_content" in container_content:
            for content in container_content.get("container_content"):
                self.insert_container_content(content)
            self.insert_container(container_content)
        else:
            self.insert_content(container_content)

    def setup_content_directory(self, content_directory_info):
        self.add_content_directory_info(content_directory_info)
        for container_content in collect_mp4_files(content_directory_info):
            self.insert_container_content(container_content)
            # print()
            # pass
        print("Done")
        # print(content)
        # for media in collect_mp4_files(content_directory_info):
        #     pass
        # if content_directory_info.get(common_objects.MEDIA_TYPE_COLUMN) == ContentType.TV.value:
        #     self.add_tv_show_data(content_directory_info)
        # elif content_directory_info.get(common_objects.MEDIA_TYPE_COLUMN) == ContentType.MOVIE.value:
        #     for movie in collect_movies(content_directory_info):
        #         print(movie)
        # else:
        #     print(
        #         f'ERROR: Unknown ContentType provided: {content_directory_info.get(common_objects.MEDIA_TYPE_COLUMN)}')
        #     print(f'INFO: Supported values {ContentType.list()}')


sql_create_playlist_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.PLAYLIST_INFO_TABLE} (
                                    {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                    {common_objects.PLAYLIST_TITLE} text NOT NULL UNIQUE,
                                    {common_objects.DESCRIPTION} text DEFAULT "",
                                    {common_objects.IMAGE_URL} text DEFAULT ""
                                );'''

SET_PLAYLIST_METADATA = f'{INSERT_IGNORE} {common_objects.PLAYLIST_INFO_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.PLAYLIST_TITLE}, "", "");'

sql_create_playlist_media_list_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.PLAYLIST_MEDIA_LIST_TABLE} (
                                          {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                          {common_objects.PLAYLIST_ID_COLUMN} integer NOT NULL,
                                          {common_objects.MEDIA_ID_COLUMN} integer NOT NULL,
                                          {common_objects.LIST_INDEX_COLUMN} integer NOT NULL,
                                          FOREIGN KEY ({common_objects.MEDIA_ID_COLUMN}) REFERENCES {common_objects.MEDIA_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                          FOREIGN KEY ({common_objects.PLAYLIST_ID_COLUMN}) REFERENCES {common_objects.PLAYLIST_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                          UNIQUE ({common_objects.PLAYLIST_ID_COLUMN}, {common_objects.MEDIA_ID_COLUMN}, {common_objects.LIST_INDEX_COLUMN})
                                       );'''

sql_insert_playlist_media_list_table = f'{INSERT_IGNORE} {common_objects.PLAYLIST_MEDIA_LIST_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.PLAYLIST_ID_COLUMN}, :{common_objects.MEDIA_ID_COLUMN}, :{common_objects.LIST_INDEX_COLUMN});'

sql_create_tv_show_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.TV_SHOW_INFO_TABLE} (
                                    {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                    {common_objects.PLAYLIST_ID_COLUMN} integer NOT NULL UNIQUE,
                                    {common_objects.DESCRIPTION} text DEFAULT "",
                                    {common_objects.IMAGE_URL} text DEFAULT "",
                                    FOREIGN KEY ({common_objects.PLAYLIST_ID_COLUMN}) REFERENCES {common_objects.PLAYLIST_INFO_TABLE} ({common_objects.ID_COLUMN})
                                    );'''

SET_TV_SHOW_METADATA = f'{INSERT_IGNORE} {common_objects.TV_SHOW_INFO_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.PLAYLIST_ID_COLUMN}, "", "");'

sql_create_season_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.SEASON_INFO_TABLE} (
                                  {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                  {common_objects.TV_SHOW_ID_COLUMN} integer NOT NULL,
                                  {common_objects.SEASON_INDEX_COLUMN} integer NOT NULL,
                                  {common_objects.DESCRIPTION} text DEFAULT "",
                                  {common_objects.IMAGE_URL} text DEFAULT "",
                                  FOREIGN KEY ({common_objects.TV_SHOW_ID_COLUMN}) REFERENCES {common_objects.TV_SHOW_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                  UNIQUE({common_objects.TV_SHOW_ID_COLUMN}, {common_objects.SEASON_INDEX_COLUMN})
                               );'''

sql_insert_season_info_table = f'{INSERT_IGNORE} {common_objects.SEASON_INFO_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.TV_SHOW_ID_COLUMN}, :{common_objects.SEASON_INDEX_COLUMN}, "", "");'

sql_create_media_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.MEDIA_INFO_TABLE} (
                                 {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                 {common_objects.TV_SHOW_ID_COLUMN} integer,
                                 {common_objects.SEASON_ID_COLUMN} integer,
                                 {common_objects.MEDIA_DIRECTORY_ID_COLUMN} NOT NULL,
                                 {common_objects.MEDIA_TITLE_COLUMN} text NOT NULL,
                                 {common_objects.PATH_COLUMN} text NOT NULL UNIQUE,
                                 {common_objects.MD5SUM_COLUMN} text UNIQUE,
                                 {common_objects.DURATION_COLUMN} integer,
                                 {common_objects.PLAY_COUNT} integer DEFAULT 0,
                                 {common_objects.DESCRIPTION} text DEFAULT "",
                                 {common_objects.IMAGE_URL} text DEFAULT "",
                                 FOREIGN KEY ({common_objects.TV_SHOW_ID_COLUMN}) REFERENCES {common_objects.TV_SHOW_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                 FOREIGN KEY ({common_objects.SEASON_ID_COLUMN}) REFERENCES {common_objects.SEASON_INFO_TABLE} ({common_objects.ID_COLUMN}),
                                 FOREIGN KEY ({common_objects.MEDIA_DIRECTORY_ID_COLUMN}) REFERENCES {common_objects.MEDIA_DIRECTORY_ID_COLUMN} ({common_objects.ID_COLUMN}),
                                 UNIQUE({common_objects.MEDIA_DIRECTORY_ID_COLUMN}, {common_objects.MEDIA_TITLE_COLUMN}, {common_objects.PATH_COLUMN})
                              );'''

sql_insert_media_info_table = f'{INSERT_IGNORE} {common_objects.MEDIA_INFO_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.TV_SHOW_ID_COLUMN}, :{common_objects.SEASON_ID_COLUMN}, :{common_objects.MEDIA_DIRECTORY_ID_COLUMN}, :{common_objects.MEDIA_TITLE_COLUMN}, :{common_objects.PATH_COLUMN}, :{common_objects.MD5SUM_COLUMN}, :{common_objects.DURATION_COLUMN}, 0, "", "");'

sql_create_media_folder_path_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.MEDIA_DIRECTORY_TABLE} (
                                        {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                        {common_objects.MEDIA_TYPE_COLUMN} integer NOT NULL,
                                        {common_objects.MEDIA_DIRECTORY_PATH_COLUMN} text NOT NULL UNIQUE,
                                        {common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN} text,
                                        {common_objects.MEDIA_DIRECTORY_URL_COLUMN} text NOT NULL UNIQUE
                                     );'''

sql_insert_media_folder_path_table = f'{INSERT_IGNORE} {common_objects.MEDIA_DIRECTORY_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.MEDIA_TYPE_COLUMN}, :{common_objects.MEDIA_DIRECTORY_PATH_COLUMN}, :{common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN}, :{common_objects.MEDIA_DIRECTORY_URL_COLUMN});'

sql_create_user_info_table = f'''CREATE TABLE IF NOT EXISTS {common_objects.MEDIA_DIRECTORY_TABLE} (
                                        {common_objects.ID_COLUMN} integer PRIMARY KEY,
                                        {common_objects.MEDIA_TYPE_COLUMN} integer NOT NULL,
                                        {common_objects.MEDIA_DIRECTORY_PATH_COLUMN} text NOT NULL UNIQUE,
                                        {common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN} text,
                                        {common_objects.MEDIA_DIRECTORY_URL_COLUMN} text NOT NULL UNIQUE
                                     );'''

sql_insert_user_info_table = f'{INSERT_IGNORE} {common_objects.MEDIA_DIRECTORY_TABLE} VALUES(:{common_objects.ID_COLUMN}, :{common_objects.MEDIA_TYPE_COLUMN}, :{common_objects.MEDIA_DIRECTORY_PATH_COLUMN}, :{common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN}, :{common_objects.MEDIA_DIRECTORY_URL_COLUMN});'

# Get row ID's from various contents
GET_ID = f'SELECT {common_objects.ID_COLUMN} FROM '
GET_PLAYLIST_ID_FROM_TITLE = f'{GET_ID} {common_objects.PLAYLIST_INFO_TABLE} WHERE {common_objects.PLAYLIST_TITLE}=:{common_objects.PLAYLIST_TITLE};'
GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO = f'{GET_ID} {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN}=:{common_objects.PLAYLIST_ID_COLUMN} AND {common_objects.MEDIA_ID_COLUMN}=:{common_objects.MEDIA_ID_COLUMN} AND {common_objects.LIST_INDEX_COLUMN}=:{common_objects.LIST_INDEX_COLUMN};'
GET_TV_SHOW_ID_FROM_PLAYLIST_ID = f'{GET_ID} {common_objects.TV_SHOW_INFO_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN}=:{common_objects.PLAYLIST_ID_COLUMN};'
GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX = f'{GET_ID} {common_objects.SEASON_INFO_TABLE} WHERE {common_objects.TV_SHOW_ID_COLUMN}=:{common_objects.TV_SHOW_ID_COLUMN} AND {common_objects.SEASON_INDEX_COLUMN}=:{common_objects.SEASON_INDEX_COLUMN};'
GET_MEDIA_ID_FROM_TITLE_PATH = f'{GET_ID} {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.MEDIA_TITLE_COLUMN}=:{common_objects.MEDIA_TITLE_COLUMN} AND {common_objects.PATH_COLUMN}=:{common_objects.PATH_COLUMN};'
GET_MEDIA_ID_FROM_PATH = f'{GET_ID} {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.PATH_COLUMN}=:{common_objects.PATH_COLUMN};'

GET_MEDIA_DIRECTORY_INFO = f'SELECT * FROM {common_objects.MEDIA_DIRECTORY_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_ALL_MEDIA_DIRECTORIES = f'SELECT * FROM {common_objects.MEDIA_DIRECTORY_TABLE};'
GET_PLAYLIST_METADATA = f'SELECT * FROM {common_objects.PLAYLIST_INFO_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_PLAYLIST_LIST_METADATA = f'SELECT * FROM {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_TV_SHOW_METADATA = f'SELECT * FROM {common_objects.TV_SHOW_INFO_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_SEASON_METADATA = f'SELECT * FROM {common_objects.SEASON_INFO_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_MEDIA_METADATA = f'SELECT * FROM {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.ID_COLUMN};'
GET_MEDIA_METADATA_FROM_MEDIA_FOLDER_PATH_ID = f'SELECT * FROM {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.MEDIA_DIRECTORY_ID_COLUMN}=:{common_objects.MEDIA_DIRECTORY_ID_COLUMN};'


class DBCreator(DBConnection):

    def create_db(self):
        if self.VERSION != self.check_db_version():
            # Run db update procedure
            pass
        db_table_creation_script = ''.join(['BEGIN;', sql_create_tv_show_info_table, sql_create_season_info_table,
                                            sql_create_media_info_table, sql_create_playlist_info_table,
                                            sql_create_playlist_media_list_table, sql_create_media_folder_path_table,
                                            'COMMIT;'])
        self.create_tables(db_table_creation_script)

    def scan_media_directory(self, media_directory_info):
        if media_directory_info.get(common_objects.MEDIA_TYPE_COLUMN) == ContentType.TV.value:
            self.add_tv_show_data(media_directory_info)
        elif media_directory_info.get(common_objects.MEDIA_TYPE_COLUMN) == ContentType.MOVIE.value:
            self.add_movie_data(media_directory_info)
        else:
            print(f'ERROR: Unknown ContentType provided: {media_directory_info.get(common_objects.MEDIA_TYPE_COLUMN)}')
            print(f'INFO: Supported values {ContentType.list()}')

    def setup_media_directory(self, media_directory_info):
        if media_directory_id := self.set_media_directory_info(media_directory_info):
            media_directory_info[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_directory_id
            self.scan_media_directory(media_directory_info)
        return media_directory_id

    def scan_all_media_directories(self):
        for media_directory_info in self.get_all_media_directory_info():
            media_directory_info[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_directory_info.get(
                common_objects.ID_COLUMN)
            self.scan_media_directory(media_directory_info)

    def add_tv_show_data(self, media_directory_info):
        for tv_show in collect_tv_shows(media_directory_info):
            if tv_show.get(common_objects.PLAYLIST_TITLE):
                if self.get_row_id(GET_MEDIA_ID_FROM_PATH, (tv_show.get(common_objects.PATH_COLUMN),)):
                    continue

                tv_show[common_objects.PLAYLIST_ID_COLUMN] = self.set_playlist_metadata(tv_show)
                if not tv_show.get(common_objects.PLAYLIST_ID_COLUMN):
                    tv_show[common_objects.PLAYLIST_ID_COLUMN] = self.get_playlist_id_from_title(tv_show)

                tv_show[common_objects.TV_SHOW_ID_COLUMN] = self.set_tv_show_metadata(tv_show)
                if not tv_show.get(common_objects.TV_SHOW_ID_COLUMN):
                    tv_show[common_objects.TV_SHOW_ID_COLUMN] = self.get_tv_show_id_from_playlist_id(tv_show)

                tv_show[common_objects.SEASON_ID_COLUMN] = self.set_season_metadata(tv_show)
                if not tv_show.get(common_objects.SEASON_ID_COLUMN):
                    tv_show[common_objects.SEASON_ID_COLUMN] = self.get_season_id_from_tv_show_id_season_index(tv_show)

                if tv_show.get("full_file_path"):
                    get_extra_metadata(tv_show, title=True)

                tv_show[common_objects.MEDIA_ID_COLUMN] = self.set_media_metadata(tv_show)
                if tv_show.get(common_objects.MEDIA_ID_COLUMN):
                    self.add_media_to_playlist(tv_show)
                else:
                    print("Skipping playlist")
        print("Finished tv scan")

    def add_movie_data(self, media_directory_info):
        for movie in collect_movies(media_directory_info):
            movie[common_objects.TV_SHOW_ID_COLUMN] = None
            movie[common_objects.SEASON_ID_COLUMN] = None
            if movie.get("full_file_path"):
                get_extra_metadata(movie)
            self.set_media_metadata(movie)
        print("Finished movie scan")

    def set_media_directory_info(self, media_directory_info) -> int:
        defaulted_media_directory_info = common_objects.default_media_directory_info.copy()
        defaulted_media_directory_info.update(media_directory_info)
        return self.add_data_to_db(sql_insert_media_folder_path_table, defaulted_media_directory_info)

    def get_media_directory_info(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_DIRECTORY_INFO, {common_objects.ID_COLUMN: item_id})

    def get_all_media_directory_info(self):
        return self.get_data_from_db(GET_ALL_MEDIA_DIRECTORIES)

    def set_playlist_metadata(self, playlist_metadata) -> int:
        return self.add_data_to_db(SET_PLAYLIST_METADATA, playlist_metadata)

    def get_playlist_metadata(self, item_id: int) -> dict:
        return self.get_data_from_db_first_result(GET_PLAYLIST_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_playlist_id_from_title(self, playlist_metadata) -> int:
        return self.get_row_id(GET_PLAYLIST_ID_FROM_TITLE, playlist_metadata)

    def set_tv_show_metadata(self, tv_show_metadata) -> int:
        return self.add_data_to_db(SET_TV_SHOW_METADATA, tv_show_metadata)

    def get_tv_show_metadata(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_TV_SHOW_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_tv_show_id_from_playlist_id(self, tv_show_metadata) -> int:
        return self.get_row_id(GET_TV_SHOW_ID_FROM_PLAYLIST_ID, tv_show_metadata)

    def set_season_metadata(self, season_metadata) -> int:
        return self.add_data_to_db(sql_insert_season_info_table, season_metadata)

    def get_season_metadata(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_SEASON_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_season_id_from_tv_show_id_season_index(self, season_metadata) -> int:
        return self.get_row_id(GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX, season_metadata)

    def set_media_metadata(self, media_metadata) -> int:
        return self.add_data_to_db(sql_insert_media_info_table, media_metadata)

    def get_media_metadata(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_media_id_from_media_title_path(self, media_metadata) -> int:
        return self.get_row_id(GET_MEDIA_ID_FROM_TITLE_PATH, media_metadata)

    def get_media_metadata_from_media_folder_path_id(self, media_metadata) -> list[dict]:
        return self.get_data_from_db(GET_MEDIA_METADATA_FROM_MEDIA_FOLDER_PATH_ID, media_metadata)

    def add_media_to_playlist(self, media_metadata) -> int:
        return self.add_data_to_db(sql_insert_playlist_media_list_table, media_metadata)

    def get_playlist_entry(self, item_id) -> dict:
        return self.get_data_from_db_first_result(GET_PLAYLIST_LIST_METADATA, {common_objects.ID_COLUMN: item_id})

    def get_playlist_id_from_playlist_media_metadata(self, media_metadata) -> int:
        return self.get_row_id(GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO, media_metadata)
