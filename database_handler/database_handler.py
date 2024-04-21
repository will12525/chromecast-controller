import json
import pathlib

from . import DBConnection, common_objects
from .common_objects import ContentType

SEASON_TITLE_BUILDER = f"'Season' || ' ' || {common_objects.SEASON_INDEX_COLUMN} AS season_title"
SORT_ALPHABETICAL = "GLOB '[A-Za-z]*'"

# Get title lists
GET_TV_SHOW_TITLE = f'SELECT {common_objects.PLAYLIST_TITLE} FROM {common_objects.TV_SHOW_INFO_TABLE} INNER JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.PLAYLIST_ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN};'
GET_TV_SHOW_TITLES = f'SELECT {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN}, {common_objects.PLAYLIST_TITLE}, {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.DESCRIPTION}, {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.IMAGE_URL} FROM {common_objects.TV_SHOW_INFO_TABLE} INNER JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.PLAYLIST_ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} ORDER BY {common_objects.PLAYLIST_TITLE} {SORT_ALPHABETICAL} DESC, {common_objects.PLAYLIST_TITLE};'
GET_TV_SHOW_SEASON_TITLES = f'SELECT {common_objects.ID_COLUMN}, {SEASON_TITLE_BUILDER}, {common_objects.SEASON_INDEX_COLUMN}, {common_objects.SEASON_INFO_TABLE}.{common_objects.DESCRIPTION}, {common_objects.SEASON_INFO_TABLE}.{common_objects.IMAGE_URL} FROM {common_objects.SEASON_INFO_TABLE} WHERE {common_objects.TV_SHOW_ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN} ORDER BY {common_objects.SEASON_INDEX_COLUMN} ASC;'
GET_TV_SHOW_SEASON_EPISODE_TITLES = f'SELECT {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN}, {common_objects.MEDIA_TITLE_COLUMN}, {common_objects.SEASON_INFO_TABLE}.{common_objects.SEASON_INDEX_COLUMN}, {common_objects.PLAYLIST_MEDIA_LIST_TABLE}.{common_objects.LIST_INDEX_COLUMN}, {common_objects.MEDIA_INFO_TABLE}.{common_objects.PLAY_COUNT}, {common_objects.MEDIA_INFO_TABLE}.{common_objects.DESCRIPTION}, {common_objects.MEDIA_INFO_TABLE}.{common_objects.IMAGE_URL} FROM {common_objects.MEDIA_INFO_TABLE} INNER JOIN {common_objects.PLAYLIST_MEDIA_LIST_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN} = {common_objects.PLAYLIST_MEDIA_LIST_TABLE}.{common_objects.MEDIA_ID_COLUMN} LEFT JOIN {common_objects.SEASON_INFO_TABLE} ON {common_objects.SEASON_INFO_TABLE}.{common_objects.ID_COLUMN} = {common_objects.MEDIA_INFO_TABLE}.{common_objects.SEASON_ID_COLUMN} WHERE {common_objects.SEASON_ID_COLUMN} = :{common_objects.SEASON_ID_COLUMN} ORDER BY {common_objects.LIST_INDEX_COLUMN} ASC, {common_objects.MEDIA_TITLE_COLUMN};'
GET_MOVIE_TITLES = f'SELECT {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN}, {common_objects.MEDIA_TITLE_COLUMN}, {common_objects.MEDIA_INFO_TABLE}.{common_objects.DESCRIPTION}, {common_objects.MEDIA_INFO_TABLE}.{common_objects.IMAGE_URL} FROM {common_objects.MEDIA_INFO_TABLE} INNER JOIN {common_objects.MEDIA_DIRECTORY_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.MEDIA_DIRECTORY_ID_COLUMN} = {common_objects.MEDIA_DIRECTORY_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.MEDIA_DIRECTORY_TABLE}.{common_objects.MEDIA_TYPE_COLUMN} == {ContentType.MOVIE.value} ORDER BY {common_objects.MEDIA_TITLE_COLUMN} {SORT_ALPHABETICAL} DESC, {common_objects.MEDIA_TITLE_COLUMN};'
GET_PLAYLIST_TITLES = f'SELECT * FROM {common_objects.PLAYLIST_INFO_TABLE} WHERE {common_objects.ID_COLUMN} NOT IN (SELECT {common_objects.PLAYLIST_ID_COLUMN} FROM {common_objects.TV_SHOW_INFO_TABLE}) ORDER BY {common_objects.PLAYLIST_TITLE} {SORT_ALPHABETICAL} DESC;'

GET_PLAYLIST_MEDIA_TITLES = f'SELECT {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN}, {common_objects.MEDIA_TITLE_COLUMN}, {common_objects.PLAYLIST_MEDIA_LIST_TABLE}.{common_objects.LIST_INDEX_COLUMN}, {common_objects.MEDIA_INFO_TABLE}.{common_objects.PLAY_COUNT}, {common_objects.MEDIA_INFO_TABLE}.{common_objects.DESCRIPTION}, {common_objects.MEDIA_INFO_TABLE}.{common_objects.IMAGE_URL} FROM {common_objects.MEDIA_INFO_TABLE} INNER JOIN {common_objects.PLAYLIST_MEDIA_LIST_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN} = {common_objects.PLAYLIST_MEDIA_LIST_TABLE}.{common_objects.MEDIA_ID_COLUMN} WHERE {common_objects.PLAYLIST_ID_COLUMN} = :{common_objects.PLAYLIST_ID_COLUMN} ORDER BY {common_objects.LIST_INDEX_COLUMN} ASC;'

# Get content metadata
GET_TV_SHOW_METADATA = f'SELECT {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN}, {common_objects.PLAYLIST_TITLE}, {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.DESCRIPTION}, {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.IMAGE_URL} FROM {common_objects.TV_SHOW_INFO_TABLE} INNER JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.PLAYLIST_ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN};'
GET_TV_SHOW_SEASON_METADATA = f'SELECT *, {SEASON_TITLE_BUILDER}, {common_objects.SEASON_INFO_TABLE}.{common_objects.DESCRIPTION}, {common_objects.SEASON_INFO_TABLE}.{common_objects.IMAGE_URL} FROM {common_objects.SEASON_INFO_TABLE} INNER JOIN {common_objects.TV_SHOW_INFO_TABLE} ON {common_objects.SEASON_INFO_TABLE}.{common_objects.TV_SHOW_ID_COLUMN} = {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} INNER JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.PLAYLIST_ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.SEASON_INFO_TABLE}.{common_objects.ID_COLUMN} = :{common_objects.SEASON_ID_COLUMN};'
GET_MEDIA_METADATA = f'SELECT *, {SEASON_TITLE_BUILDER}, {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.PLAYLIST_TITLE} as tv_show_title FROM {common_objects.MEDIA_INFO_TABLE} INNER JOIN {common_objects.MEDIA_DIRECTORY_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.MEDIA_DIRECTORY_ID_COLUMN} = {common_objects.MEDIA_DIRECTORY_TABLE}.{common_objects.ID_COLUMN} LEFT JOIN {common_objects.TV_SHOW_INFO_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.TV_SHOW_ID_COLUMN} = {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} LEFT JOIN {common_objects.PLAYLIST_INFO_TABLE} ON {common_objects.TV_SHOW_INFO_TABLE}.{common_objects.ID_COLUMN} = {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} LEFT JOIN {common_objects.PLAYLIST_MEDIA_LIST_TABLE} ON {common_objects.PLAYLIST_INFO_TABLE}.{common_objects.ID_COLUMN} = {common_objects.PLAYLIST_MEDIA_LIST_TABLE}.{common_objects.PLAYLIST_ID_COLUMN} AND {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN} = {common_objects.PLAYLIST_MEDIA_LIST_TABLE}.{common_objects.MEDIA_ID_COLUMN} LEFT JOIN {common_objects.SEASON_INFO_TABLE} ON {common_objects.MEDIA_INFO_TABLE}.{common_objects.SEASON_ID_COLUMN} = {common_objects.SEASON_INFO_TABLE}.{common_objects.ID_COLUMN} WHERE {common_objects.MEDIA_INFO_TABLE}.{common_objects.ID_COLUMN}=:{common_objects.MEDIA_ID_COLUMN} ORDER BY {common_objects.PLAYLIST_MEDIA_LIST_TABLE}.{common_objects.LIST_INDEX_COLUMN} ASC;'
GET_PLAYLIST_METADATA = f'SELECT * FROM {common_objects.PLAYLIST_INFO_TABLE} WHERE {common_objects.ID_COLUMN} = :{common_objects.PLAYLIST_ID_COLUMN};'

# Get row counts
GET_TV_SHOW_SEASON_COUNT = f'SELECT COUNT(*) AS season_count FROM {common_objects.SEASON_INFO_TABLE} WHERE {common_objects.TV_SHOW_ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN};'
GET_TV_SHOW_EPISODE_COUNT = f'SELECT COUNT(*) AS episode_count FROM {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.TV_SHOW_ID_COLUMN} = :{common_objects.TV_SHOW_ID_COLUMN};'
GET_TV_SHOW_SEASON_EPISODE_COUNT = f'SELECT COUNT(*) AS episode_count FROM {common_objects.MEDIA_INFO_TABLE} WHERE {common_objects.SEASON_ID_COLUMN} = :{common_objects.SEASON_ID_COLUMN};'
GET_PLAYLIST_MEDIA_COUNT = f'SELECT COUNT(*) AS episode_count FROM {common_objects.PLAYLIST_MEDIA_LIST_TABLE} WHERE {common_objects.PLAYLIST_ID_COLUMN} = :{common_objects.PLAYLIST_ID_COLUMN};'

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
PLAYLIST_QUERY_LIST = [GET_PLAYLIST_METADATA, GET_PLAYLIST_MEDIA_COUNT]

INCREMENT_MEDIA_PLAY_COUNT = f"UPDATE {common_objects.MEDIA_INFO_TABLE} SET {common_objects.PLAY_COUNT} = {common_objects.PLAY_COUNT} + 1 WHERE id=:{common_objects.MEDIA_ID_COLUMN};"

UPDATE_TV_SHOW_METADATA = f"UPDATE {common_objects.TV_SHOW_INFO_TABLE} SET {common_objects.DESCRIPTION}=:{common_objects.DESCRIPTION}, {common_objects.IMAGE_URL}=:{common_objects.IMAGE_URL} WHERE id=:{common_objects.ID_COLUMN};"
UPDATE_SEASON_METADATA = f"UPDATE {common_objects.SEASON_INFO_TABLE} SET {common_objects.DESCRIPTION}=:{common_objects.DESCRIPTION}, {common_objects.IMAGE_URL}=:{common_objects.IMAGE_URL} WHERE id=:{common_objects.ID_COLUMN};"
UPDATE_MEDIA_METADATA = f"UPDATE {common_objects.MEDIA_INFO_TABLE} SET {common_objects.DESCRIPTION}=:{common_objects.DESCRIPTION}, {common_objects.IMAGE_URL}=:{common_objects.IMAGE_URL} WHERE id=:{common_objects.ID_COLUMN};"
UPDATE_PLAYLIST_METADATA = f"UPDATE {common_objects.PLAYLIST_INFO_TABLE} SET {common_objects.DESCRIPTION}=:{common_objects.DESCRIPTION}, {common_objects.IMAGE_URL}=:{common_objects.IMAGE_URL} WHERE id=:{common_objects.ID_COLUMN};"

NEW_MEDIA_METADATA_JSON_FILE = "new_media_metadata_file.json"

media_content_query_data = {
    ContentType.MEDIA: {'query_list': MEDIA_QUERY_LIST,
                        'requires_id': common_objects.MEDIA_ID_COLUMN},
    ContentType.SEASON: {'query_list': TV_SHOW_SEASON_MEDIA_QUERY_LIST,
                         'media_title_list_query': GET_TV_SHOW_SEASON_EPISODE_TITLES,
                         'requires_id': common_objects.SEASON_ID_COLUMN},
    ContentType.PLAYLIST: {'query_list': PLAYLIST_QUERY_LIST,
                           'media_title_list_query': GET_PLAYLIST_MEDIA_TITLES,
                           'requires_id': common_objects.PLAYLIST_ID_COLUMN},
    ContentType.TV_SHOW: {'query_list': TV_SHOW_SEASON_QUERY_LIST,
                          'media_title_list_query': GET_TV_SHOW_SEASON_TITLES,
                          'requires_id': common_objects.TV_SHOW_ID_COLUMN},
    ContentType.TV: {'media_title_list_query': GET_TV_SHOW_TITLES},
    ContentType.MOVIE: {'media_title_list_query': GET_MOVIE_TITLES},
    ContentType.PLAYLISTS: {'media_title_list_query': GET_PLAYLIST_TITLES}
}


def load_js_file(filename):
    if filename:
        file_path = pathlib.Path(filename)
        if file_path.is_file():
            with open(filename, mode='r') as f_in:
                try:
                    return json.load(f_in)
                except ValueError:
                    pass
    return {}


def save_js_file(filename, content):
    with open(filename, mode='w') as f_out:
        f_out.write(json.dumps(content, indent=4))


class DatabaseHandler(DBConnection):

    def get_content_list(self, content_type, params=()) -> dict:
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
                # if common_objects.ID_COLUMN in params_dict:
                #     params_dict[content_data.get('requires_id')] = params_dict.get(common_objects.ID_COLUMN)
                # else:
                #     return {}
                return {}
            media_metadata['content_type'] = content_type.value

            if container_content_type := content_type.get_last():
                media_metadata['container_content_type'] = container_content_type.value

            for query in content_data.get('query_list', []):
                media_metadata.update(self.get_data_from_db_first_result(query, params_dict))
            media_metadata.update(self.get_content_list(content_type, params_dict))

            if media_metadata.get(common_objects.SEASON_INDEX_COLUMN) and media_metadata.get(
                    common_objects.LIST_INDEX_COLUMN):
                media_metadata[common_objects.LIST_INDEX_COLUMN] = media_metadata[common_objects.LIST_INDEX_COLUMN] - \
                                                                   media_metadata[
                                                                       common_objects.SEASON_INDEX_COLUMN] * 1000
            for media_item in media_metadata.get("media_list", []):
                if media_item.get(common_objects.LIST_INDEX_COLUMN) and media_item.get(
                        common_objects.LIST_INDEX_COLUMN) >= 1000:
                    media_item[common_objects.LIST_INDEX_COLUMN] = media_item[common_objects.LIST_INDEX_COLUMN] % 1000

        else:
            print(f'Unknown content type requested: {content_type}')

        return media_metadata

    def get_increment_episode_metadata(self, query_list, data) -> dict:
        """

        :param query_list:
        :param data: dict {media_id, playlist_id}
        :return: media_metadata
        """
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
        """

        :param data: dict {media_id, playlist_id}
        :return:
        """
        return self.get_increment_episode_metadata(GET_NEXT_IN_PLAYLIST_MEDIA_METADATA, data)

    def get_previous_in_playlist_media_metadata(self, data) -> dict:
        """

        :param data: dict {media_id, playlist_id}
        :return:
        """
        return self.get_increment_episode_metadata(GET_PREVIOUS_IN_PLAYLIST_MEDIA_METADATA, data)

    def get_media_folder_path(self, content_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_FOLDER_PATH_FROM_ID, (content_id,))

    def get_season_list_index(self, params) -> int:
        return self.get_row_item(GET_SEASON_LIST_INDEX_FROM_SEASON_ID, params, common_objects.SEASON_INDEX_COLUMN)

    def get_tv_show_title(self, params) -> str:
        return self.get_row_item(GET_TV_SHOW_TITLE, params, common_objects.PLAYLIST_TITLE)

    def update_play_count(self, params):
        self.add_data_to_db(INCREMENT_MEDIA_PLAY_COUNT, params)

    def update_media_metadata(self, params):
        if params.get('content_type') == ContentType.MEDIA.value:
            self.add_data_to_db(UPDATE_MEDIA_METADATA, params)
        elif params.get('content_type') == ContentType.SEASON.value:
            self.add_data_to_db(UPDATE_SEASON_METADATA, params)
        elif params.get('content_type') == ContentType.TV_SHOW.value:
            self.add_data_to_db(UPDATE_TV_SHOW_METADATA, params)
        elif params.get('content_type') == ContentType.PLAYLIST.value:
            self.add_data_to_db(UPDATE_PLAYLIST_METADATA, params)
        else:
            print(f"Unknown content type: {params}")
