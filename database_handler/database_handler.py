from . import DBConnection, common_objects
from .common_objects import ContentType

SEASON_TITLE_BUILDER = f"'Season' || ' ' || {common_objects.SEASON_INDEX_COLUMN} AS season_title"
SORT_ALPHABETICAL = "GLOB '[A-Za-z]*'"

# Get title lists
GET_TV_SHOW_TITLE = f'SELECT {common_objects.PLAYLIST_TITLE} FROM {common_objects.TV_SHOW_INFO_TABLE} INNER JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.PLAYLIST_ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN};'
GET_TV_SHOW_TITLES = f'SELECT {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN}, {common_objects.PLAYLIST_TITLE} FROM {common_objects.TV_SHOW_INFO_TABLE} INNER JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.PLAYLIST_ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} ORDER BY playlist_title {SORT_ALPHABETICAL} DESC, playlist_title;'
GET_TV_SHOW_SEASON_TITLES = f'SELECT {common_objects.ID_COLUMN}, {SEASON_TITLE_BUILDER}, {common_objects.SEASON_INDEX_COLUMN} FROM {common_objects.SEASON_INFO_TABLE} WHERE {common_objects.TV_SHOW_ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN} ORDER BY {common_objects.SEASON_INDEX_COLUMN} ASC;'
GET_TV_SHOW_SEASON_EPISODE_TITLES = f'SELECT {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN}, {common_objects.MEDIA_TITLE_COLUMN} FROM {common_objects.MEDIA_INFO_TABLE} INNER JOIN {common_objects.PLAYLIST_MEDIA_LIST_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN} = {common_objects.PLAYLIST_MEDIA_LIST_TABLE}.{common_objects.MEDIA_ID_COLUMN} WHERE {common_objects.SEASON_ID_COLUMN} = :{common_objects.SEASON_ID_COLUMN} ORDER BY {common_objects.LIST_INDEX_COLUMN} ASC, {common_objects.MEDIA_TITLE_COLUMN};'
GET_MOVIE_TITLES = f'SELECT {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN}, {common_objects.MEDIA_TITLE_COLUMN} FROM {common_objects.MEDIA_INFO_TABLE} INNER JOIN {common_objects.MEDIA_DIRECTORY_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.MEDIA_DIRECTORY_ID_COLUMN} = {common_objects.MEDIA_DIRECTORY_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.MEDIA_DIRECTORY_TABLE}.{common_objects.MEDIA_TYPE_COLUMN} == {ContentType.MOVIE.value} ORDER BY {common_objects.MEDIA_TITLE_COLUMN} {SORT_ALPHABETICAL} DESC, {common_objects.MEDIA_TITLE_COLUMN};'

# Get content metadata
GET_TV_SHOW_METADATA = f'SELECT {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN}, {common_objects.PLAYLIST_TITLE} FROM {common_objects.TV_SHOW_INFO_TABLE} INNER JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.PLAYLIST_ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN};'
GET_TV_SHOW_SEASON_METADATA = f'SELECT *, {SEASON_TITLE_BUILDER} FROM {common_objects.SEASON_INFO_TABLE} INNER JOIN {common_objects.TV_SHOW_INFO_TABLE} ON {common_objects.SEASON_INFO_TABLE}.{common_objects.TV_SHOW_ID_COLUMN} = {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} INNER JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.PLAYLIST_ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.SEASON_INFO_TABLE}.{common_objects.ID_COLUMN} = :{common_objects.SEASON_ID_COLUMN};'
GET_MEDIA_METADATA = f'SELECT *, {SEASON_TITLE_BUILDER}, {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.PLAYLIST_TITLE} as tv_show_title FROM {common_objects.MEDIA_INFO_TABLE} INNER JOIN {common_objects.MEDIA_DIRECTORY_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.MEDIA_DIRECTORY_ID_COLUMN} = {common_objects.MEDIA_DIRECTORY_TABLE}.{common_objects.ID_COLUMN} LEFT JOIN {common_objects.TV_SHOW_INFO_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.TV_SHOW_ID_COLUMN} = {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} LEFT JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} LEFT JOIN {common_objects.SEASON_INFO_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.SEASON_ID_COLUMN} = {common_objects.SEASON_INFO_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN}=:{common_objects.MEDIA_ID_COLUMN};'

# Get row counts
GET_TV_SHOW_SEASON_COUNT = f'SELECT COUNT(*) AS season_count FROM {common_objects.SEASON_INFO_TABLE} WHERE {common_objects.TV_SHOW_ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN};'
GET_TV_SHOW_EPISODE_COUNT = f'SELECT COUNT(*) AS episode_count FROM {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.TV_SHOW_ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN};'
GET_TV_SHOW_SEASON_EPISODE_COUNT = f'SELECT COUNT(*) AS episode_count FROM {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.SEASON_ID_COLUMN} = :{common_objects.SEASON_ID_COLUMN};'

# Get media metadata from playlist
GET_PLAYLIST_NEXT_MEDIA_ID = f'SELECT {common_objects.MEDIA_ID_COLUMN} FROM {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN}=:{common_objects.PLAYLIST_ID_COLUMN} AND {common_objects.LIST_INDEX_COLUMN}>:{common_objects.LIST_INDEX_COLUMN} ORDER BY {common_objects.LIST_INDEX_COLUMN} LIMIT 1;'
GET_PLAYLIST_FIRST_MEDIA_ID = f'SELECT {common_objects.MEDIA_ID_COLUMN} FROM {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN}=:{common_objects.PLAYLIST_ID_COLUMN} ORDER BY {common_objects.LIST_INDEX_COLUMN} LIMIT 1;'
GET_PLAYLIST_PREVIOUS_MEDIA_ID = f'SELECT {common_objects.MEDIA_ID_COLUMN} FROM {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN}=:{common_objects.PLAYLIST_ID_COLUMN} AND {common_objects.LIST_INDEX_COLUMN}<:{common_objects.LIST_INDEX_COLUMN} ORDER BY {common_objects.LIST_INDEX_COLUMN} DESC LIMIT 1;'
GET_PLAYLIST_LAST_MEDIA_ID = f'SELECT {common_objects.MEDIA_ID_COLUMN} FROM {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN}=:{common_objects.PLAYLIST_ID_COLUMN} ORDER BY {common_objects.LIST_INDEX_COLUMN} DESC LIMIT 1;'

# Get list indexes
GET_LIST_INDEX = f'SELECT {common_objects.LIST_INDEX_COLUMN}, {common_objects.MEDIA_ID_COLUMN} FROM {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN}=:{common_objects.PLAYLIST_ID_COLUMN} AND {common_objects.MEDIA_ID_COLUMN}=:{common_objects.MEDIA_ID_COLUMN};'
GET_SEASON_LIST_INDEX_FROM_SEASON_ID = f'SELECT {common_objects.SEASON_INDEX_COLUMN} FROM {common_objects.SEASON_INFO_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.SEASON_ID_COLUMN};'

# Get media directory info
GET_MEDIA_FOLDER_PATH_FROM_ID = f'SELECT * FROM {common_objects.MEDIA_DIRECTORY_TABLE} WHERE {common_objects.ID_COLUMN}=:{common_objects.MEDIA_DIRECTORY_ID_COLUMN};'

# Get playlist incremented media metadata
GET_NEXT_IN_PLAYLIST_MEDIA_METADATA = [GET_LIST_INDEX, GET_PLAYLIST_NEXT_MEDIA_ID, GET_PLAYLIST_FIRST_MEDIA_ID]
GET_PREVIOUS_IN_PLAYLIST_MEDIA_METADATA = [GET_LIST_INDEX, GET_PLAYLIST_PREVIOUS_MEDIA_ID, GET_PLAYLIST_LAST_MEDIA_ID]

# Get content metadata query lists
MEDIA_QUERY_LIST = [GET_MEDIA_METADATA]
TV_SHOW_SEASON_MEDIA_QUERY_LIST = [GET_TV_SHOW_SEASON_METADATA, GET_TV_SHOW_SEASON_EPISODE_COUNT]
TV_SHOW_SEASON_QUERY_LIST = [GET_TV_SHOW_METADATA, GET_TV_SHOW_SEASON_COUNT, GET_TV_SHOW_EPISODE_COUNT]

media_content_query_data = {
    ContentType.MEDIA: {'query_list': MEDIA_QUERY_LIST,
                        'requires_id': common_objects.MEDIA_ID_COLUMN},
    ContentType.SEASON: {'query_list': TV_SHOW_SEASON_MEDIA_QUERY_LIST,
                         'media_title_list_query': GET_TV_SHOW_SEASON_EPISODE_TITLES,
                         'requires_id': common_objects.SEASON_ID_COLUMN},
    ContentType.TV_SHOW: {'query_list': TV_SHOW_SEASON_QUERY_LIST,
                          'media_title_list_query': GET_TV_SHOW_SEASON_TITLES,
                          'requires_id': common_objects.TV_SHOW_ID_COLUMN},
    ContentType.TV: {'media_title_list_query': GET_TV_SHOW_TITLES},
    ContentType.MOVIE: {'media_title_list_query': GET_MOVIE_TITLES}
}


class DatabaseHandler(DBConnection):

    def get_content_title_list(self, content_type, params=()) -> dict:
        if media_content_query := media_content_query_data.get(content_type):
            if media_content_query := media_content_query.get('media_title_list_query'):
                return {'media_list_content_type': content_type.get_next().value,
                        'media_list': self.get_data_from_db(media_content_query, params)}
        return {}

    def get_media_content(self, content_type, params_dict=None) -> dict:
        if params_dict is None:
            params_dict = {}
        media_metadata = {}

        if content_data := media_content_query_data.get(content_type):
            if 'requires_id' in content_data and not content_data.get('requires_id') in params_dict:
                return {}

            if container_content_type := content_type.get_last():
                media_metadata['container_content_type'] = container_content_type.value

            for query in content_data.get('query_list', []):
                media_metadata.update(self.get_data_from_db_first_result(query, params_dict))

            media_metadata.update(self.get_content_title_list(content_type, params_dict))

        else:
            print(f'Unknown content type requested: {content_type}')

        return media_metadata

    def get_increment_episode_metadata(self, query_list, data) -> dict:
        '''

        :param query_list:
        :param data: dict {media_id, playlist_id}
        :return: media_metadata
        '''
        if not data.get(common_objects.PLAYLIST_ID_COLUMN) or not data.get(common_objects.MEDIA_ID_COLUMN):
            print("ERROR: get_increment_episode_metadata requires data: dict {media_id, playlist_id}")
            print(f"ERROR: get_increment_episode_metadata provided: {data}")
            return {}
        data.update(self.get_data_from_db_first_result(query_list[0], data))
        if media_id := self.get_data_from_db_first_result(query_list[1], data):
            return self.get_media_content(content_type=ContentType.MEDIA, params_dict=media_id)
        elif media_id := self.get_data_from_db_first_result(query_list[2], data):
            return self.get_media_content(content_type=ContentType.MEDIA, params_dict=media_id)
        else:
            print(f'get_next_media_metadata failed: {data}')
            return {}

    def get_next_in_playlist_media_metadata(self, data) -> dict:
        '''

        :param data: dict {media_id, playlist_id}
        :return:
        '''
        return self.get_increment_episode_metadata(GET_NEXT_IN_PLAYLIST_MEDIA_METADATA, data)

    def get_previous_in_playlist_media_metadata(self, data) -> dict:
        '''

        :param data: dict {media_id, playlist_id}
        :return:
        '''
        return self.get_increment_episode_metadata(GET_PREVIOUS_IN_PLAYLIST_MEDIA_METADATA, data)

    def get_media_folder_path(self, content_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_FOLDER_PATH_FROM_ID, (content_id,))

    def get_season_list_index(self, params) -> int:
        return self.get_row_item(GET_SEASON_LIST_INDEX_FROM_SEASON_ID, params, common_objects.SEASON_INDEX_COLUMN)

    def get_tv_show_title(self, params) -> str:
        return self.get_row_item(GET_TV_SHOW_TITLE, params, common_objects.PLAYLIST_TITLE)
