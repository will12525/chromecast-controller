from .create_database import SqliteDatabaseHandler


class DatabaseHandler:

    def __init__(self, media_paths=None):
        self.db_handler = SqliteDatabaseHandler(media_paths)

    def close(self):
        if self.db_handler:
            self.db_handler.close()

    def get_tv_show_name(self, tv_show_id) -> str:
        query = "SELECT name FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?"
        query_result = self.db_handler.get_data_from_db(query, (tv_show_id,))
        if query_result:
            return query_result[0].get("name")

    def get_movie_name_list(self) -> list[dict]:
        query = "SELECT id, name FROM media_info WHERE tv_show_id is NULL"
        return self.db_handler.get_data_from_db(query)

    def get_tv_show_name_list(self) -> list[dict]:
        query = "SELECT tv_show_info.id, name FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id"
        return self.db_handler.get_data_from_db(query)

    def get_tv_show_season_name_list(self, tv_show_id) -> list[dict]:
        query = "SELECT id, name FROM season_info WHERE tv_show_id = ?"
        return self.db_handler.get_data_from_db(query, (tv_show_id,))

    def get_tv_show_season_episode_name_list(self, season_id) -> list[dict]:
        query = "SELECT id, name FROM media_info WHERE season_id = ?"
        return self.db_handler.get_data_from_db(query, (season_id,))

    def get_tv_show_metadata(self, tv_show_id) -> dict:
        tv_show_metadata = {}
        tv_show_info_query = "SELECT tv_show_info.id, name FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?"
        season_count_query = "SELECT COUNT(*) AS season_count FROM season_info WHERE tv_show_id = ?;"
        episode_count_query = "SELECT COUNT(*) as episode_count FROM media_info WHERE tv_show_id = ?;"

        query_result = self.db_handler.get_data_from_db(tv_show_info_query, (tv_show_id,))
        if query_result:
            tv_show_metadata = query_result[0]

        query_result = self.db_handler.get_data_from_db(season_count_query, (tv_show_id,))
        if query_result:
            tv_show_metadata.update(query_result[0])

        query_result = self.db_handler.get_data_from_db(episode_count_query, (tv_show_id,))
        if query_result:
            tv_show_metadata.update(query_result[0])

        return tv_show_metadata

    def get_tv_show_season_metadata(self, season_id) -> dict:
        tv_show_season_metadata = {}
        tv_show_info_query = "SELECT *, playlist_info.name AS tv_show_name FROM season_info INNER JOIN tv_show_info ON season_info.tv_show_id = tv_show_info.id INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE season_info.id = ?"
        episode_count_query = "SELECT COUNT(*) AS episode_count FROM media_info WHERE season_id = ?;"

        tv_show_season_metadata.update(self.db_handler.get_data_from_db(tv_show_info_query, (season_id,))[0])

        tv_show_season_metadata.update(self.db_handler.get_data_from_db(episode_count_query, (season_id,))[0])

        return tv_show_season_metadata

    def get_media_metadata(self, media_id) -> dict:
        query = "SELECT * FROM media_info INNER JOIN media_folder_path ON media_info.media_folder_path_id = media_folder_path.id INNER JOIN tv_show_info ON media_info.tv_show_id = tv_show_info.id WHERE media_info.id=?"
        query_data = self.db_handler.get_data_from_db(query, (media_id,))
        if query_data:
            return query_data[0]

    def get_next_media_metadata(self, media_id, playlist_id) -> dict:
        list_index_query = "SELECT list_index FROM playlist_media_list WHERE playlist_id=? AND media_id=?"
        next_media_query = "SELECT media_id FROM playlist_media_list WHERE playlist_id=? AND list_index=?"
        list_index_query_result = self.db_handler.get_data_from_db(list_index_query, (playlist_id, media_id,))
        if list_index_query_result:
            next_media_query_result = self.db_handler.get_data_from_db(next_media_query,
                                                                       (playlist_id, list_index_query_result[0].get(
                                                                           "list_index") + 1,))
            if next_media_query_result:
                return self.get_media_metadata(next_media_query_result[0].get("media_id"))
            else:
                # Reset to first media in list
                next_media_query_result = self.db_handler.get_data_from_db(next_media_query, (playlist_id, 1,))
                if next_media_query_result:
                    return self.get_media_metadata(next_media_query_result[0].get("media_id"))
        else:
            print("Empty query")
