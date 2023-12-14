import os
import pathlib
import ffmpeg


def collect_tv_shows(media_directory_info):
    media_directory_content = []
    media_folder_path = pathlib.Path(media_directory_info.get("media_folder_path"))
    media_folder_mp4_content = list(media_folder_path.rglob("*.mp4"))
    mp4_index_content_index_search_string = " - s"
    for media_folder_mp4 in media_folder_mp4_content:

        # ffmpeg_probe_result = ffmpeg.probe(str(media_folder_mp4))
        # runtime = ffmpeg_probe_result["format"]["duration"]
        # media_title = ffmpeg_probe_result["format"]["tags"]["title"]
        # print(float(runtime) / 60, media_title)
        try:
            mp4_file_url = str(media_folder_mp4).replace(str(media_folder_path), "")
            mp4_file_name = media_folder_mp4.name
            mp4_index_content_index = mp4_file_name.rindex(mp4_index_content_index_search_string)
            mp4_index_content = mp4_file_name[mp4_index_content_index + len(
                mp4_index_content_index_search_string):-4]
            mp4_episode_start_index = mp4_index_content.index("e")
            season_index = int(mp4_index_content[:mp4_episode_start_index])
            episode_index = int(mp4_index_content[mp4_episode_start_index + 1:])
            mp4_show_title = mp4_file_name[:mp4_index_content_index]
            media_directory_content.append(
                {"mp4_show_title": mp4_show_title, "season_index": season_index, "episode_index": episode_index,
                 "mp4_file_url": str(mp4_file_url)})
        except ValueError as e:
            print(f"\nNEW MEDIA ERROR: expected: '<show_name> - sXXeXXX.mp4', Actual: {media_folder_mp4}")
    return media_directory_content


def collect_movies(media_directory_info):
    media_directory_content = []
    media_folder_path = pathlib.Path(media_directory_info.get("media_folder_path"))
    media_folder_mp4_content = list(media_folder_path.rglob("*.mp4"))
    for media_folder_mp4 in media_folder_mp4_content:
        try:
            mp4_file_url = str(media_folder_mp4).replace(str(media_folder_path), "")
            mp4_file_name = media_folder_mp4.name
            mp4_movie_title = mp4_file_name.replace(".mp4", "")
            media_directory_content.append(
                {"mp4_show_title": mp4_movie_title, "mp4_file_url": str(mp4_file_url)})
        except ValueError as e:
            print(f"\nNEW MEDIA ERROR: expected: '<show_name> - sXXeXXX.mp4', Actual: {media_folder_mp4}")
    return media_directory_content


def scan_new_media(media_path_info):
    generated_media_metadata = []
    media_folder_titles = {}

    new_media_folder_path = None

    season_str_index = -2
    tv_show_str_index = -3
    txt_file_ext = "*.txt"
    mp4_file_ext = "*.mp4"

    if media_folder_path := media_path_info.get("media_folder_path"):
        new_media_folder_path = pathlib.Path(*pathlib.Path(media_folder_path).parts[:-1]).joinpath(
            media_path_info.get("new_media_folder_path"))

    for new_media_folder_txt_file in list(new_media_folder_path.rglob(txt_file_ext)):
        media_folder_txt_parts = new_media_folder_txt_file.parts
        key = f"{media_folder_txt_parts[tv_show_str_index]}_{media_folder_txt_parts[season_str_index]}"
        if key not in media_folder_titles:
            with open(new_media_folder_txt_file) as file:
                media_folder_titles[key] = [line.rstrip() for line in file]
        else:
            print(f"ERROR: titles file already exists: {key}, {new_media_folder_txt_file}")

    for media_folder_mp4 in list(new_media_folder_path.rglob(mp4_file_ext)):
        media_metadata = {}
        season_name = media_folder_mp4.parts[season_str_index]
        show_name = media_folder_mp4.parts[tv_show_str_index]

        try:
            episode_index = int(media_folder_mp4.stem[1:])
            season_index = int(season_name[1:])
        except ValueError as e:
            print(f"ERROR: File doesnt match expected format: {media_folder_mp4}")
            continue

        key = f"{show_name}_{season_name}"
        if media_titles := media_folder_titles.get(key):
            if len(media_titles) >= episode_index and (media_title := media_folder_titles.get(key)[episode_index - 1]):
                media_metadata['mp4_show_title'] = media_title.replace('"', '').strip()

        mp4_file_url = f"/{show_name}/Season {season_index}/{show_name} - s{season_index}e{episode_index}.mp4"
        media_metadata['season_index'] = season_index
        media_metadata['episode_index'] = episode_index
        media_metadata['mp4_file_url'] = mp4_file_url

        mp4_output_file_name = pathlib.Path(f"{media_folder_path}{mp4_file_url}")
        mp4_input_file_name = str(media_folder_mp4)

        mp4_output_file_name.resolve().parent.mkdir(parents=True, exist_ok=True)

        if os.path.isfile(mp4_input_file_name):
            ffmpeg.input(mp4_input_file_name).output(str(mp4_output_file_name),
                                                     metadata=f'title={media_metadata.get("mp4_show_title", "ERROR")}',
                                                     map=0,
                                                     c='copy').overwrite_output().run()
        if os.path.isfile(mp4_output_file_name):
            generated_media_metadata.append(media_metadata)

    return generated_media_metadata
