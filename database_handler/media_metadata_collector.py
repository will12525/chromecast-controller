import hashlib
import pathlib
import threading

import ffmpeg
import shutil

DELETE = True

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


# Get the new path: media_directory_info
# Get list of titles: location of media
# Get tv show metadata
# Get movie metadata
# Get new tv show metadata
# Move title txt files
# Move tv show mp4 files


def get_new_media_folder_path(media_directory_info):
    if new_media_folder_path := media_directory_info.get('new_media_folder_path'):
        media_folder_path = pathlib.Path(media_directory_info.get('media_folder_path'))
        return pathlib.Path(media_folder_path.parents[0]).joinpath(new_media_folder_path)


def get_url(media_folder_src, media_folder_remove):
    return str(media_folder_src).replace(str(media_folder_remove), empty_str)


def get_season_name_show_title(path):
    return path.parts[tv_show_str_index], path.parts[season_str_index]


def convert_to_tv_show_path(media_directory_info, path_to_convert, file_name):
    tv_show_title, season = get_season_name_show_title(pathlib.Path(path_to_convert))
    season = season.replace(season_marker, season_marker_replacement)
    return pathlib.Path(media_directory_info.get('media_folder_path'), tv_show_title, season, file_name)


def move_txt_file(source_file_name, destination_file_name):
    destination_file_name.resolve().parent.mkdir(parents=True, exist_ok=True)
    if DELETE:
        source_file_name.replace(destination_file_name)
    else:
        shutil.copy(source_file_name, destination_file_name)


def get_title_txt_files(media_folder_path):
    media_folder_titles = {}
    for media_folder_txt_file in list(media_folder_path.rglob(txt_file_ext)):
        if (media_folder_txt_file_parent := str(media_folder_txt_file.parent)) not in media_folder_titles:
            with open(media_folder_txt_file) as file:
                media_folder_titles[media_folder_txt_file_parent] = [title.replace('"', empty_str).strip() for title in
                                                                     file]
    return media_folder_titles


def collect_new_tv_shows(media_directory_info):
    media_folder_path = pathlib.Path(media_directory_info.get('media_folder_path'))
    new_media_folder_path = get_new_media_folder_path(media_directory_info)

    media_folder_titles = get_title_txt_files(new_media_folder_path)
    for key in media_folder_titles:
        move_txt_file(pathlib.Path(key, title_file_name),
                      convert_to_tv_show_path(media_directory_info, key, title_file_name))

    for media_folder_mp4 in list(new_media_folder_path.rglob(mp4_file_ext)):
        mp4_show_title, season = get_season_name_show_title(media_folder_mp4.parent)

        try:
            season_index = int(season.replace(season_marker, empty_str))
            episode_index = int(media_folder_mp4.stem.replace(episode_marker, empty_str))
        except ValueError as e:
            print(f'ERROR: File doesnt match expected format: {media_folder_mp4}\n{e}')
            continue

        mp4_show_file_name = ''.join([mp4_show_title, mp4_index_content_index_search_string, str(season_index),
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
                    ffmpeg.input(str(media_folder_mp4)).output(str(mp4_output_file_name),
                                                               metadata=f'title={media_title}',
                                                               map=0,
                                                               c='copy').overwrite_output().run()
                if mp4_output_file_name.is_file():
                    yield {'media_folder_mp4': str(media_folder_mp4),
                           'mp4_output_file_name': str(mp4_output_file_name),
                           'mp4_show_title': mp4_show_title,
                           'season_index': season_index,
                           'episode_index': episode_index,
                           'mp4_file_url': get_url(mp4_output_file_name, media_folder_path),
                           'media_title': media_title
                           }
                    if DELETE:
                        media_folder_mp4.unlink()
        try:
            if DELETE:
                media_folder_mp4.parent.rmdir()
        except OSError as e:
            print(f'Error when removing folder: {e}')


def get_extra_metadata(media_folder_mp4):
    extra_metadata = {}

    # print(json.dumps(ffmpeg_probe_result, indent=4))
    def get_file_hash():
        if ffmpeg_probe_result := ffmpeg.probe(str(media_folder_mp4)):
            if ffmpeg_probe_result_format := ffmpeg_probe_result.get('format'):
                runtime = ffmpeg_probe_result_format.get('duration')
                extra_metadata['runtime_minutes'] = round(float(runtime) / 60)
                # print(json.dumps(ffmpeg_probe_result_format, indent=4))
                if tags := ffmpeg_probe_result_format.get('tags'):
                    extra_metadata['media_title'] = tags.get('title')

    def get_ffmpeg_metadata():
        with open(media_folder_mp4, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)
        extra_metadata['file_hash'] = file_hash.hexdigest()

    get_file_hash_thread = threading.Thread(target=get_file_hash, args=(), daemon=True)
    get_ffmpeg_metadata = threading.Thread(target=get_ffmpeg_metadata, args=(), daemon=True)
    get_file_hash_thread.start()
    get_ffmpeg_metadata.start()
    get_file_hash_thread.join()
    get_ffmpeg_metadata.join()

    print(extra_metadata)


def collect_tv_shows(media_directory_info):
    if 'new_media_folder_path' in media_directory_info:
        yield from collect_new_tv_shows(media_directory_info)

    media_folder_path = pathlib.Path(media_directory_info.get('media_folder_path'))
    media_folder_titles = get_title_txt_files(media_folder_path)
    for media_folder_mp4 in list(media_folder_path.rglob(mp4_file_ext)):

        try:
            mp4_file_name = media_folder_mp4.stem
            mp4_index_content_index = mp4_file_name.rindex(mp4_index_content_index_search_string)
            mp4_index_content = mp4_file_name[mp4_index_content_index + len(mp4_index_content_index_search_string):]
            mp4_episode_start_index = mp4_index_content.index(tv_show_media_episode_index_identifier)

            mp4_show_title = mp4_file_name[:mp4_index_content_index]
            episode_index = int(mp4_index_content[mp4_episode_start_index + 1:])
            season_index = int(mp4_index_content[:mp4_episode_start_index])
            media_title = f'Episode {episode_index}'
            if (media_folder_txt_file_parent := str(media_folder_mp4.parent)) in media_folder_titles:
                if len(media_folder_titles[media_folder_txt_file_parent]) >= episode_index:
                    media_title = media_folder_titles[media_folder_txt_file_parent][episode_index - 1]
            # get_extra_metadata(media_folder_mp4)
            yield {'mp4_show_title': mp4_show_title, 'season_index': season_index,
                   'episode_index': episode_index,
                   'mp4_file_url': get_url(media_folder_mp4, media_folder_path),
                   'media_title': media_title
                   }
        except ValueError as e:
            print(f"\nNEW MEDIA ERROR: expected: '<show_name> - sXXeXXX.mp4', Actual: {media_folder_mp4}\n{e}")


def collect_movies(media_directory_info):
    media_folder_path = pathlib.Path(media_directory_info.get('media_folder_path'))

    for media_folder_mp4 in list(media_folder_path.rglob(mp4_file_ext)):
        try:
            yield {'mp4_show_title': media_folder_mp4.stem,
                   'mp4_file_url': get_url(media_folder_mp4, media_folder_path)}
        except ValueError as e:
            print(f"\nNEW MEDIA ERROR: expected: '<show_name> - sXXeXXX.mp4', Actual: {media_folder_mp4}\n{e}")
