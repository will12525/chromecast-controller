from enum import Enum, auto
from . import DBConnection

GET_TV_SHOW_TITLE = "SELECT playlist_title FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?"
GET_MOVIE_TITLE = "SELECT id, title FROM media_info WHERE tv_show_id is NULL ORDER BY title GLOB '[A-Za-z]*' DESC, title"
GET_TV_SHOW_TITLES = "SELECT tv_show_info.id, playlist_title FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id ORDER BY playlist_title GLOB '[A-Za-z]*' DESC, playlist_title"
GET_TV_SHOW_SEASON_TITLES = "SELECT id, 'Season' || ' ' || tv_show_season_index AS title, tv_show_season_index FROM season_info WHERE tv_show_id = ? ORDER BY tv_show_season_index ASC"
GET_TV_SHOW_SEASON_EPISODE_TITLES = "SELECT media_info.id, title FROM media_info INNER JOIN playlist_media_list ON media_info.id = playlist_media_list.media_id WHERE season_id = ? ORDER BY list_index ASC, title"
GET_TV_SHOW_METADATA = "SELECT tv_show_info.id, playlist_title FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?"
GET_TV_SHOW_SEASON_COUNT = "SELECT COUNT(*) AS season_count FROM season_info WHERE tv_show_id = ?;"
GET_TV_SHOW_EPISODE_COUNT = "SELECT COUNT(*) as episode_count FROM media_info WHERE tv_show_id = ?;"
GET_TV_SHOW_SEASON_METADATA = "SELECT *, 'Season' || ' ' || tv_show_season_index AS sub_title FROM season_info INNER JOIN tv_show_info ON season_info.tv_show_id = tv_show_info.id INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE season_info.id = ?"
GET_TV_SHOW_SEASON_EPISODE_COUNT = "SELECT COUNT(*) AS episode_count FROM media_info WHERE season_id = ?;"
GET_MEDIA_METADATA = "SELECT *, 'Season' || ' ' || tv_show_season_index AS season_title, playlist_info.playlist_title as tv_show_title FROM media_info INNER JOIN media_folder_path ON media_info.media_folder_path_id = media_folder_path.id LEFT JOIN tv_show_info ON media_info.tv_show_id = tv_show_info.id LEFT JOIN playlist_info ON tv_show_info.id = playlist_info.id LEFT JOIN season_info ON media_info.season_id = season_info.id WHERE media_info.id=?"
GET_LIST_INDEX = "SELECT list_index, media_id FROM playlist_media_list WHERE playlist_id=? AND media_id=?"
GET_PLAYLIST_NEXT_MEDIA_ID = "SELECT media_id FROM playlist_media_list WHERE playlist_id=? AND list_index>? ORDER BY list_index LIMIT 1"
GET_PLAYLIST_FIRST_MEDIA_ID = "SELECT media_id FROM playlist_media_list WHERE playlist_id=? ORDER BY list_index LIMIT 1"
GET_PLAYLIST_PREVIOUS_MEDIA_ID = "SELECT media_id FROM playlist_media_list WHERE playlist_id=? AND list_index<? ORDER BY list_index DESC LIMIT 1"
GET_PLAYLIST_LAST_MEDIA_ID = "SELECT media_id FROM playlist_media_list WHERE playlist_id=? ORDER BY list_index DESC LIMIT 1"
GET_ALL_MEDIA_DIRECTORIES = "SELECT * FROM media_folder_path"
GET_MEDIA_FOLDER_PATH_FROM_ID = "SELECT * FROM media_folder_path WHERE id=?"
GET_PLAYLIST_ID_FROM_TITLE = "SELECT id FROM playlist_info WHERE playlist_title=?"
GET_TV_SHOW_ID_FROM_PLAYLIST_ID = "SELECT id FROM tv_show_info WHERE playlist_id=?"
GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX = "SELECT id FROM season_info WHERE tv_show_id=? AND tv_show_season_index=?"
GET_SEASON_LIST_INDEX_FROM_SEASON_ID = "SELECT tv_show_season_index FROM season_info WHERE id=?"
GET_MEDIA_ID_FROM_TITLE_PATH = "SELECT id FROM media_info WHERE title=? AND path=?"
GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO = "SELECT id FROM playlist_media_list WHERE playlist_id=? AND media_id=? AND list_index=?"
GET_MEDIA_ID_FROM_PATH = "SELECT id FROM media_info WHERE path=?"


class ContentType(Enum):
    MEDIA = auto()
    MOVIE = auto()
    SEASON = auto()
    TV_SHOW = auto()
    TV = auto()
    PLAYLIST = auto()


class DatabaseHandler(DBConnection):

    def get_tv_show_title(self, content_id) -> str:
        return self.get_data_from_db_first_result(GET_TV_SHOW_TITLE, (content_id,)).get("playlist_title")

    def get_movie_titles(self) -> dict:
        return {"media_list_content_type": ContentType.MEDIA.value,
                "media_list": self.get_data_from_db(GET_MOVIE_TITLE)}

    def get_tv_show_titles(self) -> dict:
        return {"media_list_content_type": ContentType.TV_SHOW.value,
                "media_list": self.get_data_from_db(GET_TV_SHOW_TITLES)}

    def get_tv_show_season_titles(self, content_id) -> dict:
        return {"media_list_content_type": ContentType.SEASON.value,
                "media_list": self.get_data_from_db(GET_TV_SHOW_SEASON_TITLES, (content_id,))}

    def get_tv_show_season_episode_titles(self, content_id) -> dict:
        return {"media_list_content_type": ContentType.MEDIA.value,
                "media_list": self.get_data_from_db(GET_TV_SHOW_SEASON_EPISODE_TITLES, (content_id,))}

    def get_tv_show_metadata(self, content_id) -> dict:
        tv_show_metadata = {"container_content_type": ContentType.TV.value}
        tv_show_metadata.update(self.get_data_from_db_first_result(GET_TV_SHOW_METADATA, (content_id,)))
        tv_show_metadata.update(self.get_data_from_db_first_result(GET_TV_SHOW_SEASON_COUNT, (content_id,)))
        tv_show_metadata.update(self.get_data_from_db_first_result(GET_TV_SHOW_EPISODE_COUNT, (content_id,)))
        return tv_show_metadata

    def get_tv_show_season_metadata(self, content_id) -> dict:
        tv_show_season_metadata = {"container_content_type": ContentType.TV_SHOW.value}
        tv_show_season_metadata.update(self.get_data_from_db_first_result(GET_TV_SHOW_SEASON_METADATA, (content_id,)))
        tv_show_season_metadata.update(
            self.get_data_from_db_first_result(GET_TV_SHOW_SEASON_EPISODE_COUNT, (content_id,)))
        return tv_show_season_metadata

    def get_media_metadata(self, content_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_METADATA, (content_id,))

    def get_media_content(self, content_type, content_id=None):
        media_metadata = {}
        if content_type == ContentType.SEASON.value and content_id:
            media_metadata.update(self.get_tv_show_season_metadata(content_id))
            media_metadata.update(self.get_tv_show_season_episode_titles(content_id))
        elif content_type == ContentType.TV_SHOW.value and content_id:
            media_metadata.update(self.get_tv_show_metadata(content_id))
            media_metadata.update(self.get_tv_show_season_titles(content_id))

        elif content_type == ContentType.MOVIE.value:
            media_metadata.update(self.get_movie_titles())
        elif content_type == ContentType.TV.value:
            media_metadata.update(self.get_tv_show_titles())
        else:
            print(f"Unknown content type provided: {content_type}")
        return media_metadata

    def get_increment_episode_metadata(self, content_id, playlist_id, query_list):
        media_metadata = {}
        list_index = self.get_data_from_db_first_result(query_list[0], (playlist_id, content_id,)).get("list_index")
        if media_id := self.get_data_from_db_first_result(query_list[1], (playlist_id, list_index,)).get("media_id"):
            media_metadata = self.get_media_metadata(media_id)
        elif media_id := self.get_data_from_db_first_result(query_list[2], (playlist_id,)).get("media_id"):
            media_metadata = self.get_media_metadata(media_id)
        else:
            print(f"get_next_media_metadata failed: {content_id}, {playlist_id}")
        return media_metadata

    def get_next_media_metadata(self, content_id, playlist_id) -> dict:
        query_list = [GET_LIST_INDEX, GET_PLAYLIST_NEXT_MEDIA_ID, GET_PLAYLIST_FIRST_MEDIA_ID]
        return self.get_increment_episode_metadata(content_id, playlist_id, query_list)

    def get_previous_media_metadata(self, content_id, playlist_id) -> dict:
        query_list = [GET_LIST_INDEX, GET_PLAYLIST_PREVIOUS_MEDIA_ID, GET_PLAYLIST_LAST_MEDIA_ID]
        return self.get_increment_episode_metadata(content_id, playlist_id, query_list)

    def get_all_media_directories(self) -> list:
        return self.get_data_from_db(GET_ALL_MEDIA_DIRECTORIES)

    def get_media_folder_path(self, content_id):
        return self.get_data_from_db(GET_MEDIA_FOLDER_PATH_FROM_ID, (content_id,))

    def get_playlist_id(self, playlist_title) -> int:
        return self.get_row_id(GET_PLAYLIST_ID_FROM_TITLE, (playlist_title,))

    def get_tv_show_id(self, content_id) -> int:
        return self.get_row_id(GET_TV_SHOW_ID_FROM_PLAYLIST_ID, (content_id,))

    def get_season_id(self, content_id, tv_show_season_index) -> int:
        return self.get_row_id(GET_SEASON_ID_FROM_TV_SHOW_ID_SEASON_INDEX, (content_id, tv_show_season_index))

    def get_season_list_index(self, content_id) -> int:
        return self.get_data_from_db_first_result(GET_SEASON_LIST_INDEX_FROM_SEASON_ID, (content_id,)).get(
            "tv_show_season_index")

    def get_media_id(self, title, path) -> int:
        return self.get_row_id(GET_MEDIA_ID_FROM_TITLE_PATH, (title, path))

    def get_playlist_media_id(self, playlist_id, content_id, list_index):
        return self.get_row_id(GET_PLAYLIST_ID_FROM_PLAYLIST_MEDIA_INFO, (playlist_id, content_id, list_index))

    def get_media_path_id(self, media_path):
        return self.get_row_id(GET_MEDIA_ID_FROM_PATH, (media_path,))
