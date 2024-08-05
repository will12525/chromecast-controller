import hashlib
import pathlib
import re
import threading

import ffmpeg
import shutil

from database_handler import common_objects

DELETE = False
MOVE_FILE = True

tv_show_media_episode_index_identifier = 'e'
mp4_index_content_index_search_string = ' - s'
mp4_file_ext = '*.mp4'
txt_file_ext = '*.txt'
title_key_seperator = '_'
empty_str = ''
season_marker = 'S'
season_marker_replacement = 'Season '
episode_marker = 'E'
season_str_index = -1
tv_show_str_index = -2

default_metadata: dict = {
    common_objects.ID_COLUMN: None,
    common_objects.PLAYLIST_TITLE: None,
    common_objects.SEASON_INDEX_COLUMN: None,
    common_objects.MEDIA_DIRECTORY_ID_COLUMN: None,
    common_objects.PATH_COLUMN: None,
    common_objects.MEDIA_TITLE_COLUMN: "",
    common_objects.LIST_INDEX_COLUMN: None,
    common_objects.MD5SUM_COLUMN: None,
    common_objects.DURATION_COLUMN: None,
    common_objects.EPISODE_INDEX: None
}


# Get the new path: media_directory_info
# Get list of titles: location of media
# Get tv show metadata
# Get movie metadata
# Get new tv show metadata
# Move title txt files
# Move tv show mp4 files


def get_url(media_folder_src, media_folder_remove):
    return str(media_folder_src).replace(str(media_folder_remove), empty_str)


def get_season_name_show_title(path):
    return path.parts[tv_show_str_index], path.parts[season_str_index]


def get_playlist_list_index(season_index, episode_index):
    return (1000 * season_index) + episode_index


def convert_to_tv_show_path(media_directory_info, path_to_convert, file_name):
    tv_show_title, season = get_season_name_show_title(pathlib.Path(path_to_convert))
    season = season.replace(season_marker, season_marker_replacement)
    return pathlib.Path(media_directory_info.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN), tv_show_title, season,
                        file_name)


def move_txt_file(source_file_name, destination_file_name):
    destination_file_name.resolve().parent.mkdir(parents=True, exist_ok=True)
    if DELETE:
        source_file_name.replace(destination_file_name)
    else:
        shutil.copy(source_file_name, destination_file_name)


def move_media_file(media_folder_mp4, mp4_output_file_name, media_title):
    if MOVE_FILE:
        ffmpeg.input(str(media_folder_mp4)).output(str(mp4_output_file_name), metadata=f'title={media_title}', map=0,
                                                   c='copy').overwrite_output().run()


def get_file_hash(extra_metadata):
    with open(extra_metadata.get("full_file_path"), 'rb') as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    extra_metadata[common_objects.MD5SUM_COLUMN] = file_hash.hexdigest()


def get_ffmpeg_metadata(path, content_data):
    try:
        if ffmpeg_probe_result := ffmpeg.probe(path):
            if ffmpeg_probe_result_format := ffmpeg_probe_result.get('format'):
                runtime = ffmpeg_probe_result_format.get('duration')
                content_data["content_duration"] = round(float(runtime) / 60)
                # print(json.dumps(ffmpeg_probe_result_format, indent=4))
                if tags := ffmpeg_probe_result_format.get('tags'):
                    content_data["content_title"] = tags.get('title', '')
    except ffmpeg.Error as e:
        content_data["tags"].append({"tag_title": "broken?"})
        # print("get_ffmpeg_metadata: output")
        # print(e.stdout)
        # print("get_ffmpeg_metadata: err")
        print(f"ERROR: FFMPEG: {path}")
        print(e.stderr)
        pass


def get_extra_metadata(media_metadata, title=False):
    get_ffmpeg_metadata_thread = None

    get_file_hash_thread = threading.Thread(target=get_file_hash, args=(media_metadata,), daemon=True)
    get_file_hash_thread.start()

    if title:
        get_ffmpeg_metadata_thread = threading.Thread(target=get_ffmpeg_metadata, args=(media_metadata,), daemon=True)
        get_ffmpeg_metadata_thread.start()

    if get_file_hash_thread:
        get_file_hash_thread.join()
    if get_ffmpeg_metadata_thread:
        get_ffmpeg_metadata_thread.join()


def extract_tv_show_file_name_content(media_metadata, mp4_file_name):
    mp4_index_content_index = mp4_file_name.rindex(mp4_index_content_index_search_string)
    mp4_index_content = mp4_file_name[mp4_index_content_index + len(mp4_index_content_index_search_string):]
    mp4_episode_start_index = mp4_index_content.index(tv_show_media_episode_index_identifier)

    media_metadata[common_objects.PLAYLIST_TITLE] = mp4_file_name[:mp4_index_content_index]
    media_metadata['episode_index'] = int(mp4_index_content[mp4_episode_start_index + 1:])
    media_metadata[common_objects.SEASON_INDEX_COLUMN] = int(mp4_index_content[:mp4_episode_start_index])

    media_metadata[common_objects.LIST_INDEX_COLUMN] = get_playlist_list_index(
        media_metadata[common_objects.SEASON_INDEX_COLUMN], media_metadata['episode_index'])


default_content_data = {
    "content_directory_id": None,
    "content_title": '',
    "content_src": '',
    "description": '',
    "img_src": '',
    "content_index": '',
    "tags": [],
}
default_container_data = {
    "container_title": "",
    "description": "",
    "img_src": '',
    "content_index": None,
    "tags": [],
    "container_content": []
}


def file_exists_with_extensions(path, file_name) -> pathlib.Path:
    """Checks if a file exists with any of the given extensions.

    Args:
        path (Path): The base path of the file.
        extensions (list): A list of file extensions to check.

    Returns:
        bool: True if the file exists with any of the given extensions, False otherwise.
    """

    for ext in [".png", ".jpg"]:
        file_path = path / f"{file_name}{ext}"
        if file_path.exists():
            return file_path


def build_movie(content_src, mp4_file_path, match, content_data):
    parent_folder = mp4_file_path.parent
    movie_title, movie_year = match.groups()

    content_data["content_title"] = movie_title
    content_data["tags"] = [{"tag_title": "movie"}]
    if img_src := file_exists_with_extensions(parent_folder, mp4_file_path.name):
        content_data['img_src'] = img_src.as_posix().replace(
            content_src, '')


def build_tv_show(content_src, mp4_file_path, match, content_data):
    parent_folder = mp4_file_path.parent
    container_path = parent_folder.as_posix().replace(content_src, '')
    tv_show_title, season_index_str, episode_index_str = match.groups()
    season_index = int(season_index_str)
    episode_index = int(episode_index_str)

    content_data["content_index"] = episode_index
    content_data["tags"] = [{"tag_title": "episode"}]
    if img_src := file_exists_with_extensions(parent_folder, mp4_file_path.name):
        content_data['img_src'] = img_src.as_posix().replace(
            content_src, '')

    get_ffmpeg_metadata(mp4_file_path, content_data)

    if not content_data.get("content_title"):
        content_data["content_title"] = f"Episode {episode_index}"

    season_container_content = default_container_data.copy()
    season_container_content["container_title"] = f'Season {season_index}'
    season_container_content["content_index"] = f'{season_index}'
    season_container_content["tags"] = [{"tag_title": "season"}]
    season_container_content["container_content"] = [content_data]
    season_container_content["container_path"] = container_path
    if img_src := file_exists_with_extensions(parent_folder, season_container_content["container_title"]):
        season_container_content['img_src'] = img_src.as_posix().replace(
            content_src, '')

    tv_container_content = default_container_data.copy()
    tv_container_content["container_title"] = tv_show_title
    tv_container_content["tags"] = [{"tag_title": "tv"}, {"tag_title": "tv show"}]
    tv_container_content["container_content"] = [season_container_content]
    tv_container_content["container_path"] = container_path
    if img_src := file_exists_with_extensions(parent_folder, "cover"):
        tv_container_content['img_src'] = img_src.as_posix().replace(
            content_src, '')

    return tv_container_content


def collect_mp4_files(content_directory_info):
    movie_pattern = r".*/([\w\W]+) \((\d{4})\)\.mp4$"
    tv_pattern = r".*\/([\w\W]+) - s(\d+)e(\d+)\.mp4$"
    content_directory_src = pathlib.Path(content_directory_info.get("content_src"))
    for mp4_file_path in list(content_directory_src.rglob(mp4_file_ext)):
        container_data = None
        content_data = default_content_data.copy()
        content_data['content_directory_id'] = content_directory_info['id']
        content_data['content_src'] = mp4_file_path.as_posix().replace(content_directory_info.get("content_src"), '')
        if match := re.search(tv_pattern, str(mp4_file_path.as_posix())):
            container_data = build_tv_show(content_directory_info.get("content_src"), mp4_file_path, match,
                                           content_data)
        elif match := re.search(movie_pattern, str(mp4_file_path.as_posix())):
            build_movie(content_directory_info.get("content_src"), mp4_file_path, match, content_data)
        else:
            # print(media_folder_mp4.as_posix())
            # print(f"Unknown media type: {mp4_file_path}")
            # print(mp4_file_path.as_posix())
            continue

        if container_data:
            yield container_data
        else:
            yield content_data


def collect_tv_shows(content_directory_info):
    media_folder_path = pathlib.Path(content_directory_info.get("content_src"))
    for media_folder_mp4 in list(media_folder_path.rglob(mp4_file_ext)):
        print(media_folder_mp4)
        media_metadata = default_metadata.copy()
        media_metadata["full_file_path"] = str(media_folder_mp4.as_posix())
        media_metadata["content_directory_id"] = content_directory_info.get("id")

        try:
            media_metadata["content_url"] = get_url(media_folder_mp4, media_folder_path)
            extract_tv_show_file_name_content(media_metadata, media_folder_mp4.stem)

            yield media_metadata
        except ValueError as e:
            print(f'{e}\nNEW MEDIA ERROR: expected: <show_name> - sXXeXXX.mp4, Actual: {media_folder_mp4}')


def collect_movies(media_directory_info):
    media_folder_path = pathlib.Path(media_directory_info.get("common_objects.MEDIA_DIRECTORY_PATH_COLUMN"))

    for media_folder_mp4 in list(media_folder_path.rglob(mp4_file_ext)):
        media_metadata = default_metadata.copy()
        media_metadata["full_file_path"] = str(media_folder_mp4.as_posix())
        media_metadata[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_directory_info.get(
            common_objects.MEDIA_DIRECTORY_ID_COLUMN)

        media_metadata[common_objects.PATH_COLUMN] = get_url(media_folder_mp4, media_folder_path)
        media_metadata[common_objects.MEDIA_TITLE_COLUMN] = media_folder_mp4.stem

        yield media_metadata
