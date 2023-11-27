import os
import traceback
import pathlib


def get_dir_list(dir_path):
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        return sorted(os.listdir(dir_path))


def sort_season_dir_list(tv_show_path):
    unsorted_tv_show_season_name_list = get_dir_list(tv_show_path)
    tv_show_season_name_dict = {}
    title_str = "n "
    for tv_show_season_name_str in unsorted_tv_show_season_name_list:
        if title_str in tv_show_season_name_str:
            try:
                tv_show_season_name_id_str = tv_show_season_name_str[
                                             tv_show_season_name_str.index(title_str) + len(title_str):
                                             ]
                tv_show_season_name_id_int = int(tv_show_season_name_id_str) + -1

                tv_show_season_name_dict[tv_show_season_name_id_int] = tv_show_season_name_str

            except ValueError as e:
                print(f"ERROR: {tv_show_season_name_str}\n{e}")
            except Exception as e:
                print(f"ERROR READING: {unsorted_tv_show_season_name_list}\n{e}")
                print(traceback.format_exc())

    sorted_tv_show_season_name_dict_keys = list(tv_show_season_name_dict.keys())
    sorted_tv_show_season_name_dict_keys.sort()
    return [tv_show_season_name_dict[i] for i in sorted_tv_show_season_name_dict_keys]


def collect_episodes(db_handler, playlist_id, tv_show_id, season_info_id, media_folder_path_id, tv_show_season_path,
                     media_folder_base):
    # Get list of all episodes in a tv show
    if tv_show_seasons_dir_path_list := get_dir_list(tv_show_season_path):
        # Iterate over each episode in the list
        for episode_id, tv_show_season_episode_dir_name in enumerate(tv_show_seasons_dir_path_list):
            # Build a path for the tv show season episode
            tv_show_season_episode_path = f"{tv_show_season_path}{tv_show_season_episode_dir_name}"
            if os.path.exists(tv_show_season_episode_path) and os.path.isfile(tv_show_season_episode_path):
                tv_show_url = tv_show_season_episode_path.replace(media_folder_base, "")
                episode_1_id = db_handler.add_media(f"Episode {(episode_id + 1)}", media_folder_path_id,
                                                    tv_show_url,
                                                    season_info_id, tv_show_id)
                db_handler.add_media_to_playlist(playlist_id, season_info_id, episode_1_id)


def collect_seasons(db_handler, playlist_id, tv_show_id, media_folder_path_id, tv_show_path, media_folder_base):
    # Get list of all seasons in a tv show
    if tv_show_seasons_dir_path_list := sort_season_dir_list(tv_show_path):
        # Iterate over each season in the list
        for season_index, tv_show_season_dir_name in enumerate(tv_show_seasons_dir_path_list):
            # Get the start index for the season
            season_info_id = db_handler.add_season(playlist_id, tv_show_id, tv_show_season_dir_name,
                                                   list_index=(season_index + 1))
            # Build a path for the tv show season
            tv_show_season_path = f"{tv_show_path}{tv_show_season_dir_name}/"
            # Get list of all episodes in a tv show
            collect_episodes(db_handler, playlist_id, tv_show_id, season_info_id, media_folder_path_id,
                             tv_show_season_path, media_folder_base)


def collect_tv_shows(db_handler, media_folder_path_id, media_folder_base):
    # Get list of all tv shows
    if tv_shows_dir_path_list := get_dir_list(media_folder_base):
        # Iterate over each tv show in the list
        for tv_show_dir_name in tv_shows_dir_path_list:
            # Build a path for the tv show
            tv_show_path = f"{media_folder_base}{tv_show_dir_name}/"
            if os.path.exists(tv_show_path):
                # Add show to playlist and show tracking
                (playlist_id, tv_show_id) = db_handler.add_tv_show(tv_show_dir_name)
                collect_seasons(db_handler, playlist_id, tv_show_id, media_folder_path_id, tv_show_path,
                                media_folder_base)


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
