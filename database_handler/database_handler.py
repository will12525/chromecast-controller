from enum import Enum, auto
from . import DBConnection, MediaType, common_objects

SEASON_TITLE_BUILDER = "'Season' || ' ' || season_index AS season_title"

# Get title lists
GET_TV_SHOW_TITLE = f'SELECT {common_objects.PLAYLIST_TITLE} FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?;'
GET_TV_SHOW_TITLES = f"SELECT tv_show_info.id, {common_objects.PLAYLIST_TITLE} FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id ORDER BY playlist_title GLOB '[A-Za-z]*' DESC, playlist_title;"
GET_TV_SHOW_SEASON_TITLES = f'SELECT id, {SEASON_TITLE_BUILDER}, season_index FROM season_info WHERE tv_show_id = ? ORDER BY season_index ASC;'
GET_TV_SHOW_SEASON_EPISODE_TITLES = 'SELECT media_info.id, media_title FROM media_info INNER JOIN playlist_media_list ON media_info.id = playlist_media_list.media_id WHERE season_id = ? ORDER BY list_index ASC, media_title;'
GET_MOVIE_TITLES = f"SELECT media_info.id, media_title FROM media_info INNER JOIN media_folder_path ON media_info.media_folder_path_id = media_folder_path.id WHERE media_folder_path.media_type == {MediaType.MOVIE.value} ORDER BY media_title GLOB '[A-Za-z]*' DESC, media_title;"

# Get content metadata
GET_TV_SHOW_METADATA = f'SELECT tv_show_info.id, {common_objects.PLAYLIST_TITLE} FROM tv_show_info INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE tv_show_info.id = ?;'
GET_TV_SHOW_SEASON_METADATA = f'SELECT *, {SEASON_TITLE_BUILDER} FROM season_info INNER JOIN tv_show_info ON season_info.tv_show_id = tv_show_info.id INNER JOIN playlist_info ON tv_show_info.playlist_id = playlist_info.id WHERE season_info.id = ?;'
GET_MEDIA_METADATA = f'SELECT *, {SEASON_TITLE_BUILDER}, playlist_info.{common_objects.PLAYLIST_TITLE} as tv_show_title FROM media_info INNER JOIN media_folder_path ON media_info.media_folder_path_id = media_folder_path.id LEFT JOIN tv_show_info ON media_info.tv_show_id = tv_show_info.id LEFT JOIN playlist_info ON tv_show_info.id = playlist_info.id LEFT JOIN season_info ON media_info.season_id = season_info.id WHERE media_info.id=?;'

# Get row counts
GET_TV_SHOW_SEASON_COUNT = 'SELECT COUNT(*) AS season_count FROM season_info WHERE tv_show_id = ?;'
GET_TV_SHOW_EPISODE_COUNT = 'SELECT COUNT(*) AS episode_count FROM media_info WHERE tv_show_id = ?;'
GET_TV_SHOW_SEASON_EPISODE_COUNT = 'SELECT COUNT(*) AS episode_count FROM media_info WHERE season_id = ?;'

# Get media metadata from playlist
GET_PLAYLIST_NEXT_MEDIA_ID = 'SELECT media_id FROM playlist_media_list WHERE playlist_id=? AND list_index>? ORDER BY list_index LIMIT 1;'
GET_PLAYLIST_FIRST_MEDIA_ID = 'SELECT media_id FROM playlist_media_list WHERE playlist_id=? ORDER BY list_index LIMIT 1;'
GET_PLAYLIST_PREVIOUS_MEDIA_ID = 'SELECT media_id FROM playlist_media_list WHERE playlist_id=? AND list_index<? ORDER BY list_index DESC LIMIT 1;'
GET_PLAYLIST_LAST_MEDIA_ID = 'SELECT media_id FROM playlist_media_list WHERE playlist_id=? ORDER BY list_index DESC LIMIT 1;'

# Get list indexes
GET_LIST_INDEX = 'SELECT list_index, media_id FROM playlist_media_list WHERE playlist_id=? AND media_id=?;'
GET_SEASON_LIST_INDEX_FROM_SEASON_ID = 'SELECT season_index FROM season_info WHERE id=?;'

# Get media directory info
GET_ALL_MEDIA_DIRECTORIES = 'SELECT * FROM media_folder_path;'
GET_MEDIA_FOLDER_PATH_FROM_ID = 'SELECT * FROM media_folder_path WHERE id=?;'

# Get playlist incremented media metadata
GET_NEXT_IN_PLAYLIST_MEDIA_METADATA = [GET_LIST_INDEX, GET_PLAYLIST_NEXT_MEDIA_ID, GET_PLAYLIST_FIRST_MEDIA_ID]
GET_PREVIOUS_IN_PLAYLIST_MEDIA_METADATA = [GET_LIST_INDEX, GET_PLAYLIST_PREVIOUS_MEDIA_ID, GET_PLAYLIST_LAST_MEDIA_ID]

# Get content metadata query lists
MEDIA_QUERY_LIST = [GET_MEDIA_METADATA]
TV_SHOW_SEASON_MEDIA_QUERY_LIST = [GET_TV_SHOW_SEASON_METADATA, GET_TV_SHOW_SEASON_EPISODE_COUNT]
TV_SHOW_SEASON_QUERY_LIST = [GET_TV_SHOW_METADATA, GET_TV_SHOW_SEASON_COUNT, GET_TV_SHOW_EPISODE_COUNT]


class ContentType(Enum):
    MEDIA = auto()
    MOVIE = auto()
    SEASON = auto()
    TV_SHOW = auto()
    TV = auto()
    PLAYLIST = auto()

    def get_next(self):
        if self == self.TV:
            return self.TV_SHOW
        if self == self.TV_SHOW:
            return self.SEASON
        if self == self.SEASON:
            return self.MEDIA
        if self == self.MOVIE:
            return self.MEDIA

    def get_last(self):
        if self == self.SEASON:
            return self.TV_SHOW
        if self == self.TV_SHOW:
            return self.TV


media_content_query_data = {
    ContentType.MEDIA: {'query_list': MEDIA_QUERY_LIST,
                        'require_id': True},
    ContentType.SEASON: {'query_list': TV_SHOW_SEASON_MEDIA_QUERY_LIST,
                         'media_title_list_query': GET_TV_SHOW_SEASON_EPISODE_TITLES,
                         'require_id': True},
    ContentType.TV_SHOW: {'query_list': TV_SHOW_SEASON_QUERY_LIST,
                          'media_title_list_query': GET_TV_SHOW_SEASON_TITLES,
                          'require_id': True},
    ContentType.TV: {'media_title_list_query': GET_TV_SHOW_TITLES},
    ContentType.MOVIE: {'media_title_list_query': GET_MOVIE_TITLES}
}


class DatabaseHandler(DBConnection):

    def get_content_title_list(self, content_type, query, params=()) -> dict:
        return {'media_list_content_type': content_type.value,
                'media_list': self.get_data_from_db(query, params)}

    def get_media_content(self, content_type_id, content_id=None) -> dict:
        params = ()
        media_metadata = {}
        content_type = None
        content_data = None

        if content_type_id <= len(ContentType):
            content_type = ContentType(content_type_id)

        if content_type:
            content_data = media_content_query_data.get(content_type)

        if content_data:
            if content_data.get('require_id'):
                if content_id:
                    params = (content_id,)
                else:
                    print(f'Requires ID for query: {content_type}')
                    return {}

            if container_content_type := content_type.get_last():
                media_metadata['container_content_type'] = container_content_type.value
            for query in content_data.get('query_list', []):
                media_metadata.update(self.get_data_from_db_first_result(query, params))
            if media_title_list_query := content_data.get('media_title_list_query'):
                media_metadata.update(
                    self.get_content_title_list(content_type.get_next(), media_title_list_query, params))
            return media_metadata

        else:
            print(f'Unknown content type requested: {content_type_id}')

        return {}

    def get_increment_episode_metadata(self, query_list, content_id, playlist_id) -> dict:
        result_content = ['list_index', 'media_id']
        media_metadata = {}
        list_index = self.get_row_item(query_list[0], (playlist_id, content_id,), result_content[0])
        media_id = self.get_row_item(query_list[1], (playlist_id, list_index,), result_content[1])
        if media_id:
            return self.get_media_content(ContentType.MEDIA.value, media_id)
        elif media_id := self.get_row_item(query_list[2], (playlist_id,), result_content[1]):
            return self.get_media_content(ContentType.MEDIA.value, media_id)
        else:
            print(f'get_next_media_metadata failed: {content_id}, {playlist_id}')
            return media_metadata

    def get_next_in_playlist_media_metadata(self, content_id, playlist_id) -> dict:
        return self.get_increment_episode_metadata(GET_NEXT_IN_PLAYLIST_MEDIA_METADATA, content_id, playlist_id)

    def get_previous_in_playlist_media_metadata(self, content_id, playlist_id) -> dict:
        return self.get_increment_episode_metadata(GET_PREVIOUS_IN_PLAYLIST_MEDIA_METADATA, content_id, playlist_id)

    def get_media_folder_path(self, content_id) -> dict:
        return self.get_data_from_db_first_result(GET_MEDIA_FOLDER_PATH_FROM_ID, (content_id,))

    def get_season_list_index(self, content_id) -> int:
        return self.get_row_item(GET_SEASON_LIST_INDEX_FROM_SEASON_ID, (content_id,), 'season_index')

    def get_tv_show_title(self, content_id) -> str:
        return self.get_row_item(GET_TV_SHOW_TITLE, (content_id,), common_objects.PLAYLIST_TITLE)
