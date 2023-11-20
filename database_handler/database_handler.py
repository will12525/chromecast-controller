from create_database import SqliteDatabaseHandler


class DatabaseHandler:

    def __init__(self, media_folder_path):
        self.db_handler = SqliteDatabaseHandler(media_folder_path)

    def get_url(self, media_server_url, media_folder_path, media_id):
        query = "SELECT path FROM media_info WHERE id=?"
        playlist_rows = self.db_handler.get_data_from_db(query, (media_id,))
        media_url = None

        if playlist_rows:
            media_url, = playlist_rows[0]
            media_url = media_url.replace(media_folder_path, media_server_url)

        return media_url

    def get_tv_show_name(self, tv_show_id) -> str:
        query = "SELECT name FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?"
        query_result = self.db_handler.get_data_from_db(query, (tv_show_id,))
        if query_result:
            return query_result[0][0]

    def get_tv_show_name_list(self) -> list[tuple[int, str]]:
        query = "SELECT tv_show_info.id, name FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id"
        return self.db_handler.get_data_from_db(query)

    def get_tv_show_season_name_list(self, tv_show_id) -> list[str]:
        query = "SELECT id, name FROM season_info WHERE tv_show_id = ?"
        return self.db_handler.get_data_from_db(query, (tv_show_id,))

    def get_tv_show_season_episode_name_list(self, season_id) -> list[str]:
        query = "SELECT id, name FROM media_info WHERE season_id = ?"
        return self.db_handler.get_data_from_db(query, (season_id,))

    def get_tv_show_metadata(self, tv_show_id) -> dict:
        tv_show_metadata = {}
        tv_show_info_query = "SELECT tv_show_info.id, name FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?"
        season_count_query = "SELECT COUNT(*) FROM season_info WHERE tv_show_id = ?;"
        episode_count_query = "SELECT COUNT(*) FROM media_info WHERE tv_show_id = ?;"

        query_result = self.db_handler.get_data_from_db(tv_show_info_query, (tv_show_id,))
        if query_result:
            tv_show_id_name = query_result[0]
            tv_show_metadata["id"] = tv_show_id_name[0]
            tv_show_metadata["show_name"] = tv_show_id_name[1]

        query_result = self.db_handler.get_data_from_db(season_count_query, (tv_show_id,))
        if query_result:
            tv_show_metadata["season_count"] = query_result[0][0]

        query_result = self.db_handler.get_data_from_db(episode_count_query, (tv_show_id,))
        if query_result:
            tv_show_metadata["episode_count"] = query_result[0][0]

        return tv_show_metadata

    def get_tv_show_season_metadata(self, season_id) -> dict:
        tv_show_season_metadata = {}
        tv_show_info_query = "SELECT tv_show_info.id, playlist_info.name, season_info.name FROM season_info INNER JOIN tv_show_info ON season_info.tv_show_id = tv_show_info.id INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE season_info.id = ?"
        episode_count_query = "SELECT COUNT(*) FROM media_info WHERE season_id = ?;"

        query_result = self.db_handler.get_data_from_db(tv_show_info_query, (season_id,))
        if query_result:
            tv_show_id_name = query_result[0]
            tv_show_season_metadata["id"] = tv_show_id_name[0]
            tv_show_season_metadata["show_name"] = tv_show_id_name[1]

            tv_show_season_metadata["season_name"] = tv_show_id_name[2]

        query_result = self.db_handler.get_data_from_db(episode_count_query, (season_id,))
        if query_result:
            tv_show_season_metadata["episode_count"] = query_result[0][0]

        return tv_show_season_metadata
