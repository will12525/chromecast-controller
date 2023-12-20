import pathlib
import ffmpeg

tv_show_media_episode_index_identifier = "e"
mp4_index_content_index_search_string = " - s"
mp4_file_ext = "*.mp4"
txt_file_ext = "*.txt"
title_key_seperator = '_'


# Get the new path: media_path_info
# Get list of titles: location of media
# Get tv show metadata
# Get movie metadata
# Get new tv show metadata
# Move title txt files
# Move tv show mp4 files


def get_new_media_folder_path(media_path_info):
    if new_media_folder_path := media_path_info.get("new_media_folder_path"):
        media_folder_path = pathlib.Path(media_path_info.get("media_folder_path"))
        return pathlib.Path(media_folder_path.parents[0]).joinpath(new_media_folder_path)


def extract_names_from_path(media_folder_mp4):
    season_str_index = -2
    tv_show_str_index = -3
    season_name = media_folder_mp4.parts[season_str_index]
    mp4_show_title = media_folder_mp4.parts[tv_show_str_index]
    return mp4_show_title, season_name


def move_txt_file_new(source_file_name, destination_file_name):
    destination_file_name.resolve().parent.mkdir(parents=True, exist_ok=True)
    source_file_name.replace(destination_file_name)


def get_title_txt_files(media_folder_path):
    media_folder_titles = {}
    for media_folder_txt_file in list(media_folder_path.rglob(txt_file_ext)):
        if (media_folder_txt_file_parent := str(media_folder_txt_file.parent)) not in media_folder_titles:
            with open(media_folder_txt_file) as file:
                media_folder_titles[media_folder_txt_file_parent] = [title.replace('"', '').strip() for title in file]
    return media_folder_titles


def convert_to_tv_show_path(media_path_info, path_to_convert):
    path_to_convert_path = pathlib.Path(path_to_convert)
    tv_show_title = path_to_convert_path.parts[-2]
    season = path_to_convert_path.parts[-1].replace('S', 'Season ')
    return pathlib.Path(media_path_info.get("media_folder_path"), tv_show_title, season, 'titles.txt')


def collect_new_tv_shows(media_path_info):
    generated_media_metadata = []
    new_media_folder_path = get_new_media_folder_path(media_path_info)

    media_folder_titles = get_title_txt_files(new_media_folder_path)
    for key in media_folder_titles:
        move_txt_file_new(pathlib.Path(key, 'titles.txt'), convert_to_tv_show_path(media_path_info, key))

    for media_folder_mp4 in list(new_media_folder_path.rglob(mp4_file_ext)):
        mp4_show_title, season_name = extract_names_from_path(media_folder_mp4)
        season_index = season_name.replace('S', '')
        season_name = season_name.replace('S', 'Season ')

        try:
            episode_index = int(media_folder_mp4.stem.replace('E', ''))
        except ValueError as e:
            print(f"ERROR: File doesnt match expected format: {media_folder_mp4}")
            continue

        mp4_show_file_name = f"{mp4_show_title}{mp4_index_content_index_search_string}{season_index}{tv_show_media_episode_index_identifier}{episode_index}{media_folder_mp4.suffix}"

        if media_titles := media_folder_titles.get(str(media_folder_mp4.parent)):
            if len(media_titles) >= episode_index:
                media_title = media_titles[episode_index - 1]
                mp4_output_file_name = pathlib.Path(media_path_info.get("media_folder_path"), mp4_show_title,
                                                    season_name,
                                                    mp4_show_file_name)

                if media_folder_mp4.is_file() and mp4_output_file_name:
                    generated_media_metadata.append({"media_folder_mp4": str(media_folder_mp4),
                                                     "mp4_output_file_name": str(mp4_output_file_name),
                                                     "media_title": media_title})
                    ffmpeg.input(str(media_folder_mp4)).output(str(mp4_output_file_name),
                                                               metadata=f'title={media_title}',
                                                               map=0,
                                                               c='copy').overwrite_output().run()
                    media_folder_mp4.unlink()
        try:
            media_folder_mp4.parent.rmdir()
        except OSError as e:
            print(e)
    return generated_media_metadata


def collect_tv_shows(media_directory_info):
    media_directory_content = []
    if "new_media_folder_path" in media_directory_info:
        collect_new_tv_shows(media_directory_info)

    media_folder_path = pathlib.Path(media_directory_info.get("media_folder_path"))
    media_folder_titles = get_title_txt_files(media_folder_path)
    for media_folder_mp4 in list(media_folder_path.rglob(mp4_file_ext)):
        media_title = None
        mp4_show_title, season_name = extract_names_from_path(media_folder_mp4)

        # self.add_tv_show_data(media_directory_info, tv_show_list)
        # ffmpeg_probe_result = ffmpeg.probe(str(media_folder_mp4))
        # runtime = ffmpeg_probe_result["format"]["duration"]
        # media_title = ffmpeg_probe_result["format"]["tags"]["title"]
        # print(float(runtime) / 60, media_title)
        try:
            mp4_file_name = media_folder_mp4.stem
            mp4_index_content_index = mp4_file_name.rindex(mp4_index_content_index_search_string)
            mp4_index_content = mp4_file_name[mp4_index_content_index + len(mp4_index_content_index_search_string):]
            mp4_episode_start_index = mp4_index_content.index(tv_show_media_episode_index_identifier)

            episode_index = int(mp4_index_content[mp4_episode_start_index + 1:])
            if (media_folder_txt_file_parent := str(media_folder_mp4.parent)) in media_folder_titles:
                if len(media_folder_titles[media_folder_txt_file_parent]) >= episode_index:
                    media_title = media_folder_titles[media_folder_txt_file_parent][episode_index - 1]
            if not media_title:
                media_title = mp4_file_name[:mp4_index_content_index]
            media_directory_content.append({"mp4_show_title": mp4_show_title,
                                            "season_index": int(mp4_index_content[:mp4_episode_start_index]),
                                            "episode_index": episode_index,
                                            "mp4_file_url": str(media_folder_mp4).replace(str(media_folder_path), ""),
                                            "media_title": media_title
                                            })
        except ValueError as e:
            print(f"\nNEW MEDIA ERROR: expected: '<show_name> - sXXeXXX.mp4', Actual: {media_folder_mp4}")
    return media_directory_content


def collect_movies(media_directory_info):
    media_directory_content = []
    media_folder_path = pathlib.Path(media_directory_info.get("media_folder_path"))

    for media_folder_mp4 in list(media_folder_path.rglob(mp4_file_ext)):
        try:
            media_directory_content.append(
                {"mp4_show_title": media_folder_mp4.stem,
                 "mp4_file_url": str(media_folder_mp4).replace(str(media_folder_path), "")})
        except ValueError as e:
            print(f"\nNEW MEDIA ERROR: expected: '<show_name> - sXXeXXX.mp4', Actual: {media_folder_mp4}")
    return media_directory_content
