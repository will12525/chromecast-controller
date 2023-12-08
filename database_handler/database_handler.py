from enum import Enum, auto
from . import DBConnection


class ContentType(Enum):
    MEDIA = auto()
    TV_SHOW = auto()
    SEASON = auto()
    MOVIE = auto()
    PLAYLIST = auto()


class DatabaseHandler(DBConnection):

    def get_tv_show_title(self, tv_show_id) -> str:
        query = "SELECT title FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?"
        query_result = self.get_data_from_db(query, (tv_show_id,))
        if query_result:
            return query_result[0].get("title")

    def get_movie_title_list(self) -> list[dict]:
        query = "SELECT id, title FROM media_info WHERE tv_show_id is NULL ORDER BY title GLOB '[A-Za-z]*' DESC, title"
        return self.get_data_from_db(query)

    def get_tv_show_title_list(self) -> list[dict]:
        query = "SELECT tv_show_info.id, title FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id ORDER BY title GLOB '[A-Za-z]*' DESC, title"
        return self.get_data_from_db(query)

    def get_tv_show_season_title_list(self, tv_show_id) -> list[dict]:
        query = "SELECT id, 'Season' || ' ' || tv_show_season_index AS title, tv_show_season_index FROM season_info WHERE tv_show_id = ? ORDER BY tv_show_season_index ASC"
        return self.get_data_from_db(query, (tv_show_id,))

    def get_tv_show_season_episode_title_list(self, season_id) -> list[dict]:
        query = "SELECT media_info.id, title FROM media_info INNER JOIN playlist_media_list ON media_info.id = playlist_media_list.media_id WHERE season_id = ? ORDER BY list_index ASC, title"
        return self.get_data_from_db(query, (season_id,))

    def get_tv_show_metadata(self, tv_show_id) -> dict:
        tv_show_metadata = {}
        tv_show_info_query = "SELECT tv_show_info.id, title FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?"
        season_count_query = "SELECT COUNT(*) AS season_count FROM season_info WHERE tv_show_id = ?;"
        episode_count_query = "SELECT COUNT(*) as episode_count FROM media_info WHERE tv_show_id = ?;"

        if query_result := self.get_data_from_db(tv_show_info_query, (tv_show_id,)):
            tv_show_metadata = query_result[0]

        if query_result := self.get_data_from_db(season_count_query, (tv_show_id,)):
            tv_show_metadata.update(query_result[0])

        if query_result := self.get_data_from_db(episode_count_query, (tv_show_id,)):
            tv_show_metadata.update(query_result[0])

        return tv_show_metadata

    def get_tv_show_season_metadata(self, season_id) -> dict:
        tv_show_season_metadata = {}
        tv_show_info_query = "SELECT *, 'Season' || ' ' || tv_show_season_index AS sub_title FROM season_info INNER JOIN tv_show_info ON season_info.tv_show_id = tv_show_info.id INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE season_info.id = ?"
        episode_count_query = "SELECT COUNT(*) AS episode_count FROM media_info WHERE season_id = ?;"

        if query_result := self.get_data_from_db(tv_show_info_query, (season_id,)):
            tv_show_season_metadata.update(query_result[0])

        if query_result := self.get_data_from_db(episode_count_query, (season_id,)):
            tv_show_season_metadata.update(query_result[0])

        return tv_show_season_metadata

    def get_media_metadata(self, media_id) -> dict:
        query = "SELECT * FROM media_info INNER JOIN media_folder_path ON media_info.media_folder_path_id = media_folder_path.id LEFT JOIN tv_show_info ON media_info.tv_show_id = tv_show_info.id WHERE media_info.id=?"
        query_result = self.get_data_from_db(query, (media_id,))
        if query_result:
            media_metadata = query_result[0]
            if tv_show_id := media_metadata.get("tv_show_id"):
                media_metadata["tv_show_title"] = self.get_tv_show_title(tv_show_id)
            if season_id := media_metadata.get("season_id"):
                media_metadata["season_title"] = f"Season {self.get_season_list_index(season_id)}"
            return media_metadata

    def get_media_content(self, content_type, media_id=None):
        media_metadata = {}
        if content_type == ContentType.MEDIA and media_id:
            media_metadata.update(self.get_tv_show_season_metadata(media_id))
            media_metadata["media_list"] = self.get_tv_show_season_episode_title_list(media_id)
            media_metadata["content_type"] = ContentType.SEASON.value
        elif content_type == ContentType.SEASON and media_id:
            media_metadata.update(self.get_tv_show_metadata(media_id))
            media_metadata["media_list"] = self.get_tv_show_season_title_list(media_id)
            media_metadata["next_content_type"] = ContentType.MEDIA.value

        elif content_type == ContentType.MOVIE:
            media_metadata["media_list"] = self.get_movie_title_list()
        elif content_type == ContentType.TV_SHOW:
            media_metadata["media_list"] = self.get_tv_show_title_list()
            media_metadata["next_content_type"] = ContentType.SEASON.value
        else:
            print(f"Unknown content type provided: {content_type}")
        return media_metadata

    def get_increment_episode_metadata(self, media_id, playlist_id, query_list):
        list_index_query_result = self.get_data_from_db(query_list[0], (playlist_id, media_id,))
        if list_index_query_result:
            next_media_query_result = self.get_data_from_db(query_list[1],
                                                            (playlist_id, list_index_query_result[0].get(
                                                                "list_index"),))
            if next_media_query_result:
                return self.get_media_metadata(next_media_query_result[0].get("media_id"))
            else:
                first_media_id_query_result = self.get_data_from_db(query_list[2], (playlist_id,))
                if first_media_id_query_result:
                    return self.get_media_metadata(first_media_id_query_result[0].get("media_id"))
        else:
            print(f"get_next_media_metadata failed: {media_id}, {playlist_id}")

    def get_next_media_metadata(self, media_id, playlist_id) -> dict:
        list_index_query = "SELECT list_index, media_id FROM playlist_media_list WHERE playlist_id=? AND media_id=?"
        next_media_id_query = "SELECT media_id FROM playlist_media_list WHERE playlist_id=? AND list_index>? ORDER BY list_index LIMIT 1"
        first_media_id_query = "SELECT media_id FROM playlist_media_list WHERE playlist_id=? ORDER BY list_index LIMIT 1"
        query_list = [list_index_query, next_media_id_query, first_media_id_query]
        return self.get_increment_episode_metadata(media_id, playlist_id, query_list)

    def get_previous_media_metadata(self, media_id, playlist_id) -> dict:
        list_index_query = "SELECT list_index, media_id FROM playlist_media_list WHERE playlist_id=? AND media_id=?"
        previous_media_id_query = "SELECT media_id FROM playlist_media_list WHERE playlist_id=? AND list_index<? ORDER BY list_index DESC LIMIT 1"
        last_media_id_query = "SELECT media_id FROM playlist_media_list WHERE playlist_id=? ORDER BY list_index DESC LIMIT 1"
        query_list = [list_index_query, previous_media_id_query, last_media_id_query]
        return self.get_increment_episode_metadata(media_id, playlist_id, query_list)

    def get_all_media_directories(self) -> list:
        query = "SELECT * FROM media_folder_path"
        return self.get_data_from_db(query)

    def get_media_folder_path(self, media_path_id):
        query = "SELECT * FROM media_folder_path WHERE id=?"
        return self.get_data_from_db(query, (media_path_id,))

    def query_id(self, query: str, params: tuple):
        if query_result := self.get_data_from_db(query, params):
            return query_result[0].get("id")

    def get_playlist_id(self, playlist_title) -> int:
        query = "SELECT id FROM playlist_info WHERE title=?"
        return self.query_id(query, (playlist_title,))

    def get_tv_show_id(self, playlist_id) -> int:
        query = "SELECT id FROM tv_show_info WHERE playlist_id=?"
        return self.query_id(query, (playlist_id,))

    def get_season_id(self, tv_show_id, tv_show_season_index) -> int:
        query = "SELECT id FROM season_info WHERE tv_show_id=? AND tv_show_season_index=?"
        return self.query_id(query, (tv_show_id, tv_show_season_index))

    def get_season_list_index(self, season_id) -> int:
        query = "SELECT tv_show_season_index FROM season_info WHERE id=?"
        if query_result := self.get_data_from_db(query, (season_id,)):
            return query_result[0].get("tv_show_season_index")

    def get_media_id(self, title, path) -> int:
        query = "SELECT id FROM media_info WHERE title=? AND path=?"
        return self.query_id(query, (title, path))

    def get_playlist_media_id(self, playlist_id, media_id, list_index):
        query = "SELECT id FROM playlist_media_list WHERE playlist_id=? AND media_id=? AND list_index=?"
        return self.query_id(query, (playlist_id, media_id, list_index))

    def get_media_path_id(self, media_path):
        query = "SELECT id FROM media_info WHERE path=?"
        return self.query_id(query, (media_path,))
