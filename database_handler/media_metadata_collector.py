import hashlib
import pathlib
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
title_file_name = 'titles.txt'
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
    common_objects.MEDIA_TITLE_COLUMN: None,
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


def get_new_media_folder_path(media_directory_info):
    if new_media_folder_path := media_directory_info.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN):
        media_folder_path = pathlib.Path(media_directory_info.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN))
        return pathlib.Path(media_folder_path.parents[0]).joinpath(new_media_folder_path)


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


def get_title_txt_files(media_folder_path):
    media_folder_titles = {}
    for media_folder_txt_file in list(media_folder_path.rglob(txt_file_ext)):
        if (media_folder_txt_file_parent := str(media_folder_txt_file.parent)) not in media_folder_titles:
            with open(media_folder_txt_file) as file:
                media_folder_titles[media_folder_txt_file_parent] = [title.replace('"', empty_str).strip() for title in
                                                                     file]
    return media_folder_titles


def get_file_hash(media_folder_mp4, extra_metadata):
    with open(media_folder_mp4, 'rb') as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    extra_metadata[common_objects.MD5SUM_COLUMN] = file_hash.hexdigest()


def get_ffmpeg_metadata(media_folder_mp4, extra_metadata):
    if ffmpeg_probe_result := ffmpeg.probe(str(media_folder_mp4)):
        if ffmpeg_probe_result_format := ffmpeg_probe_result.get('format'):
            runtime = ffmpeg_probe_result_format.get('duration')
            extra_metadata[common_objects.DURATION_COLUMN] = round(float(runtime) / 60)
            # print(json.dumps(ffmpeg_probe_result_format, indent=4))
            if tags := ffmpeg_probe_result_format.get('tags'):
                extra_metadata[common_objects.MEDIA_TITLE_COLUMN] = tags.get('title')


def get_extra_metadata(media_folder_mp4, title=False):
    extra_metadata = {}
    get_ffmpeg_metadata_thread = None
    # print(json.dumps(ffmpeg_probe_result, indent=4))
    args = (media_folder_mp4, extra_metadata,)

    get_file_hash_thread = threading.Thread(target=get_file_hash, args=args, daemon=True)
    get_file_hash_thread.start()

    if title:
        get_ffmpeg_metadata_thread = threading.Thread(target=get_ffmpeg_metadata, args=args, daemon=True)
        get_ffmpeg_metadata_thread.start()

    if get_file_hash_thread:
        get_file_hash_thread.join()
    if get_ffmpeg_metadata_thread:
        get_ffmpeg_metadata_thread.join()

    return extra_metadata


def collect_new_tv_shows(media_directory_info):
    media_folder_path = pathlib.Path(media_directory_info.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN))
    new_media_folder_path = get_new_media_folder_path(media_directory_info)

    media_folder_titles = get_title_txt_files(new_media_folder_path)
    for key in media_folder_titles:
        move_txt_file(pathlib.Path(key, title_file_name),
                      convert_to_tv_show_path(media_directory_info, key, title_file_name))

    for media_folder_mp4 in list(new_media_folder_path.rglob(mp4_file_ext)):
        playlist_title, season = get_season_name_show_title(media_folder_mp4.parent)

        try:
            season_index = int(season.replace(season_marker, empty_str))
            episode_index = int(media_folder_mp4.stem.replace(episode_marker, empty_str))
        except ValueError as e:
            print(f'{e}\nERROR: File doesnt match expected format: {media_folder_mp4}')
            continue

        mp4_show_file_name = ''.join([playlist_title, mp4_index_content_index_search_string, str(season_index),
                                      tv_show_media_episode_index_identifier, str(episode_index),
                                      media_folder_mp4.suffix])

        if media_titles := media_folder_titles.get(str(media_folder_mp4.parent)):
            if len(media_titles) >= episode_index:
                media_title = media_titles[episode_index - 1]
                mp4_output_file_name = convert_to_tv_show_path(media_directory_info, media_folder_mp4.parent,
                                                               mp4_show_file_name)

                if not mp4_output_file_name.parent.is_dir():
                    mp4_output_file_name.resolve().parent.mkdir(parents=True, exist_ok=True)

                if media_folder_mp4.is_file() and mp4_output_file_name:
                    move_media_file(media_folder_mp4, mp4_output_file_name, media_title)
                if mp4_output_file_name.is_file():
                    media_metadata = default_metadata.copy()
                    media_metadata['media_folder_mp4'] = str(media_folder_mp4)
                    media_metadata['mp4_output_file_name'] = str(mp4_output_file_name)
                    media_metadata[common_objects.ID_COLUMN] = None
                    media_metadata[common_objects.PLAYLIST_TITLE] = playlist_title
                    media_metadata[common_objects.SEASON_INDEX_COLUMN] = season_index
                    media_metadata['episode_index'] = episode_index
                    media_metadata[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_directory_info.get(
                        common_objects.MEDIA_DIRECTORY_ID_COLUMN)
                    media_metadata[common_objects.PATH_COLUMN] = get_url(mp4_output_file_name, media_folder_path)
                    media_metadata[common_objects.MEDIA_TITLE_COLUMN] = media_title
                    media_metadata[common_objects.LIST_INDEX_COLUMN] = get_playlist_list_index(season_index,
                                                                                               episode_index)

                    get_title = True
                    if media_metadata[common_objects.MEDIA_TITLE_COLUMN]:
                        get_title = False

                    media_metadata.update(get_extra_metadata(media_folder_mp4, title=get_title))

                    yield media_metadata
                    if DELETE:
                        media_folder_mp4.unlink()
        try:
            if DELETE:
                media_folder_mp4.parent.rmdir()
        except OSError as e:
            print(f'Error when removing folder: {e}')


def collect_tv_shows(media_directory_info):
    if media_directory_info.get(common_objects.NEW_MEDIA_DIRECTORY_PATH_COLUMN):
        yield from collect_new_tv_shows(media_directory_info)

    media_folder_path = pathlib.Path(media_directory_info.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN))
    # media_folder_titles = get_title_txt_files(media_folder_path)
    for media_folder_mp4 in list(media_folder_path.rglob(mp4_file_ext)):
        media_metadata = default_metadata.copy()
        media_metadata[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_directory_info.get(
            common_objects.MEDIA_DIRECTORY_ID_COLUMN)

        try:
            mp4_file_name = media_folder_mp4.stem
            mp4_index_content_index = mp4_file_name.rindex(mp4_index_content_index_search_string)
            mp4_index_content = mp4_file_name[mp4_index_content_index + len(mp4_index_content_index_search_string):]
            mp4_episode_start_index = mp4_index_content.index(tv_show_media_episode_index_identifier)

            media_metadata[common_objects.PLAYLIST_TITLE] = mp4_file_name[:mp4_index_content_index]
            media_metadata['episode_index'] = int(mp4_index_content[mp4_episode_start_index + 1:])
            media_metadata[common_objects.SEASON_INDEX_COLUMN] = int(mp4_index_content[:mp4_episode_start_index])

            # media_metadata[common_objects.MEDIA_TITLE_COLUMN] = f"Episode {media_metadata['episode_index']}"
            # if (media_folder_txt_file_parent := str(media_folder_mp4.parent)) in media_folder_titles:
            #     if len(media_folder_titles[media_folder_txt_file_parent]) >= media_metadata['episode_index']:
            #         media_metadata[common_objects.MEDIA_TITLE_COLUMN] = \
            #             media_folder_titles[media_folder_txt_file_parent][media_metadata['episode_index'] - 1]

            media_metadata[common_objects.PATH_COLUMN] = get_url(media_folder_mp4, media_folder_path)
            media_metadata[common_objects.LIST_INDEX_COLUMN] = get_playlist_list_index(
                media_metadata[common_objects.SEASON_INDEX_COLUMN], media_metadata['episode_index'])

            media_metadata.update(get_extra_metadata(media_folder_mp4, title=True))

            yield media_metadata
        except ValueError as e:
            print(f'{e}\nNEW MEDIA ERROR: expected: <show_name> - sXXeXXX.mp4, Actual: {media_folder_mp4}')


def collect_movies(media_directory_info):
    media_folder_path = pathlib.Path(media_directory_info.get(common_objects.MEDIA_DIRECTORY_PATH_COLUMN))

    for media_folder_mp4 in list(media_folder_path.rglob(mp4_file_ext)):
        media_metadata = default_metadata.copy()
        media_metadata[common_objects.MEDIA_DIRECTORY_ID_COLUMN] = media_directory_info.get(
            common_objects.MEDIA_DIRECTORY_ID_COLUMN)

        media_metadata.update(get_extra_metadata(media_folder_mp4))
        media_metadata[common_objects.PATH_COLUMN] = get_url(media_folder_mp4, media_folder_path)
        media_metadata[common_objects.MEDIA_TITLE_COLUMN] = media_folder_mp4.stem

        yield media_metadata
