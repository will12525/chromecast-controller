import os
import pathlib
import ffmpeg


def get_dir_list(dir_path):
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        return sorted(os.listdir(dir_path))


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


def recursive_mp4_search(media_folder_path, file_name):
    ret_list = []
    if os.path.exists(media_folder_path):
        if os.path.isdir(media_folder_path):
            for sub_dir in os.listdir(media_folder_path):
                ret_list.extend(recursive_mp4_search(f"{media_folder_path}/{sub_dir}", sub_dir))
        elif ".mp4" == pathlib.Path(media_folder_path).suffix:
            ret_list.append({"path": media_folder_path, "title": file_name})
        else:
            print(f"Unknown file type: {media_folder_path}")
    return ret_list


def collect_movies(media_folder):
    movie_path_list = []
    # Get list of all tv shows
    if movie_dir_path_list := get_dir_list(media_folder):
        # Iterate over each tv show in the list
        for movie_dir_name in movie_dir_path_list:
            # Build a path for the tv show
            movie_path = f"{media_folder}{movie_dir_name}"
            movie_path_list.extend(recursive_mp4_search(movie_path, movie_dir_name))
    return movie_path_list
