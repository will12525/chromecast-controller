INSERT_IGNORE = "INSERT OR IGNORE INTO"
CREATE_TABLE = "CREATE TABLE IF NOT EXISTS"

SORT_ALPHABETICAL = "GLOB '[A-Za-z]*'"

"""
SCHEMA QUERIES
"""
sql_create_version_info_table = f"""CREATE TABLE IF NOT EXISTS version_info (
                                     id integer PRIMARY KEY,
                                     version integer NOT NULL
                                  );"""
sql_insert_version_info_table = (
    "INSERT INTO version_info(version) VALUES(:version_info);"
)
version_info_query = "SELECT version FROM version_info;"

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
                                    content_directory_id integer NOT NULL,
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
                                             FOREIGN KEY (content_id) REFERENCES content (id),
                                             UNIQUE (parent_container_id, content_index, content_index)
                                         );'''
SET_CONTAINER_CONTENT_INFO_TABLE = f'{INSERT_IGNORE} container_content (parent_container_id, content_id, content_index) VALUES (:parent_container_id, :content_id, :content_index);'

CREATE_CONTAINER_CONTAINER_INFO_TABLE = f'''CREATE TABLE IF NOT EXISTS container_container (
                                             id integer PRIMARY KEY,
                                             parent_container_id integer,
                                             container_id integer,
                                             content_index integer NOT NULL,
                                             FOREIGN KEY (parent_container_id) REFERENCES container (id),
                                             FOREIGN KEY (container_id) REFERENCES container (id),
                                             UNIQUE (parent_container_id, container_id, content_index)
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

"""
MEDIA UPDATE QUERIES
"""
UPDATE_MEDIA_PLAY_COUNT = f"UPDATE content SET play_count = play_count + 1 WHERE id=:id;"
