# Table names
from enum import Enum, auto

PLAYLIST_INFO_TABLE = 'playlist_info'
PLAYLIST_MEDIA_LIST_TABLE = 'playlist_media_list'
TV_SHOW_INFO_TABLE = 'tv_show_info'
SEASON_INFO_TABLE = 'season_info'
MEDIA_INFO_TABLE = 'media_info'
MEDIA_DIRECTORY_TABLE = 'media_directory_info'


class MediaDirectoryInfo:
    media_directory_id = None


# Table columns
# Table ID columns
ID_COLUMN = 'id'
PLAYLIST_ID_COLUMN = 'playlist_id'
TV_SHOW_ID_COLUMN = 'tv_show_id'
SEASON_ID_COLUMN = 'season_id'
MEDIA_ID_COLUMN = 'media_id'
MEDIA_DIRECTORY_ID_COLUMN = 'media_directory_id'

# Table data columns
PLAYLIST_TITLE = 'playlist_title'
LIST_INDEX_COLUMN = 'list_index'
SEASON_INDEX_COLUMN = 'season_index'
EPISODE_INDEX = 'episode_index'
MEDIA_TITLE_COLUMN = 'media_title'
PATH_COLUMN = 'path'
MD5SUM_COLUMN = 'md5sum'
DURATION_COLUMN = 'duration'
PLAY_COUNT = 'play_count'
MEDIA_TYPE_COLUMN = 'media_type'
MEDIA_DIRECTORY_PATH_COLUMN = 'media_directory_path'
NEW_MEDIA_DIRECTORY_PATH_COLUMN = 'new_media_directory_path'
MEDIA_DIRECTORY_URL_COLUMN = 'media_directory_url'


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

    @classmethod
    def list(cls):
        return list(map(lambda c: c, cls))


class DBType(Enum):
    PHYSICAL = auto()
    MEMORY = auto()
