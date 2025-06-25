import hashlib
import pathlib
import re
import shutil
from enum import Enum, auto

from app.database.db_getter import DBHandler
from app.database.media_metadata_collector import get_content_type, ContentType
from app.utils import config_file_handler


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
DESCRIPTION = 'description'
IMAGE_URL = 'image_url'
MEDIA_TYPE_COLUMN = 'media_type'
MEDIA_DIRECTORY_PATH_COLUMN = 'media_directory_path'
NEW_MEDIA_DIRECTORY_PATH_COLUMN = 'new_media_directory_path'
MEDIA_DIRECTORY_URL_COLUMN = 'media_directory_url'

default_media_directory_info = {
    "id": None,
    "media_type": None,
    "media_directory_path": None,
    "new_media_directory_path": None,
    "media_directory_url": None
}


class SystemMode(Enum):
    SERVER = auto()
    CLIENT = auto()


def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def get_gb(value):
    KB = 1024
    MB = 1024 * KB
    GB = 1024 * MB
    return value / GB


def get_free_disk_space(dir_path) -> int:
    return round(get_gb(shutil.disk_usage(dir_path).free))


def get_free_disk_space_percent(dir_path):
    disk_usage = shutil.disk_usage(dir_path)
    return round((disk_usage.used / disk_usage.total) * 100)


def get_system_data():
    disk_space = []
    if raw_folder := config_file_handler.load_json_file_content().get('editor_raw_folder'):
        disk_space.append({
            "free_space": get_free_disk_space(raw_folder),
            "unit": "G",
            "percent_used": get_free_disk_space_percent(raw_folder),
            "path": raw_folder
        })

    db_connection = DBHandler()
    db_connection.open()
    media_directory_info = db_connection.get_all_content_directory_info()
    db_connection.close()

    for media_directory in media_directory_info:
        media_directory_path_str = media_directory.get("content_src")
        disk_space.append(
            {
                "free_space": get_free_disk_space(media_directory_path_str),
                "unit": "G",
                "percent_used": get_free_disk_space_percent(media_directory_path_str),
                "path": media_directory_path_str
            })

    return disk_space


def build_tv_show_output_path(file_name_str):
    error_log = []
    output_path = None
    destination_dir_path = None

    (content_type, match_data) = get_content_type(f"/{file_name_str}")
    if content_type:
        destination_dir_path = build_editor_output_path(content_type.name, error_log)
    if not error_log and destination_dir_path:
        if content_type == ContentType.TV:
            if match := re.search(r"^([\w\W]+) - s(\d+)e(\d+)\.mp4$", file_name_str):
                output_path = destination_dir_path / match[1] / file_name_str
        else:
            output_path = destination_dir_path / file_name_str
        if output_path.exists():
            raise FileExistsError({"message": "File already exists", "file_name": file_name_str})
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path.as_posix()
    else:
        print(error_log)


def build_editor_output_path(media_type, error_log):
    destination_dir_path = None
    if content_src := get_free_media_drive():
        if media_type == ContentType.RAW.name:
            if raw_folder := config_file_handler.load_json_file_content().get('editor_raw_folder'):
                destination_dir_path = pathlib.Path(raw_folder).resolve()
        elif media_type == ContentType.MOVIE.name:
            destination_dir_path = pathlib.Path(f"{content_src}/movies").resolve()
        elif media_type == ContentType.TV.name:
            destination_dir_path = pathlib.Path(f"{content_src}/tv_shows").resolve()
        elif media_type == ContentType.BOOK.name:
            destination_dir_path = pathlib.Path(f"{content_src}/books").resolve()
        else:
            error_log.append({"message": "Unknown media type", "value": f"{media_type}"})
        if destination_dir_path:
            if not destination_dir_path.exists():
                error_log.append({"message": "Disk parent paths don't exist", "file_name": f"{destination_dir_path}"})
            elif not path_has_space(destination_dir_path):
                error_log.append({
                    "message": "Disk out of space", "file_name": f"{destination_dir_path}",
                    "value": get_free_disk_space(destination_dir_path)
                })
            else:
                return destination_dir_path
    else:
        error_log.append({"message": "System out of space"})


def path_has_space(dir_path):
    print(get_free_disk_space(dir_path))
    return (free_disk_space := get_free_disk_space(dir_path)) is not None and free_disk_space > DISK_SPACE_USE_LIMIT


def get_free_media_drive():
    db_connection = DBHandler()
    db_connection.open()
    for media_directory in db_connection.get_all_content_directory_info():
        if path_has_space(media_directory.get("content_src")):
            return media_directory.get("content_src")
    db_connection.close()


DISK_SPACE_USE_LIMIT = 20
