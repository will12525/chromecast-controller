import os
import traceback


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


def collect_episodes(db_handler, playlist_id, tv_show_id, season_id, tv_show_season_path):
    # Get list of all episodes in a tv show
    if tv_show_seasons_dir_path_list := get_dir_list(tv_show_season_path):
        # Iterate over each episode in the list
        for episode_id, tv_show_season_episode_dir_name in enumerate(tv_show_seasons_dir_path_list):
            # Build a path for the tv show season episode
            tv_show_season_episode_path = f"{tv_show_season_path}{tv_show_season_episode_dir_name}"
            if os.path.exists(tv_show_season_episode_path) and os.path.isfile(tv_show_season_episode_path):
                episode_1_id = db_handler.add_media(f"Episode {(episode_id + 1)}", tv_show_season_episode_path,
                                                    season_id, tv_show_id)
                db_handler.add_media_to_playlist(playlist_id, episode_1_id)


def collect_seasons(db_handler, playlist_id, tv_show_id, tv_show_path):
    # Get list of all seasons in a tv show
    if tv_show_seasons_dir_path_list := sort_season_dir_list(tv_show_path):
        # Iterate over each season in the list
        for season_index, tv_show_season_dir_name in enumerate(tv_show_seasons_dir_path_list):
            # Get the start index for the season
            season_start_index = db_handler.get_playlist_end_index(playlist_id) + 1
            season_table_id = db_handler.add_season(tv_show_id, tv_show_season_dir_name, list_index=(season_index + 1))
            # Build a path for the tv show season
            tv_show_season_path = f"{tv_show_path}{tv_show_season_dir_name}/"
            # Get list of all episodes in a tv show
            collect_episodes(db_handler, playlist_id, tv_show_id, season_table_id, tv_show_season_path)
            season_end_index = db_handler.get_playlist_end_index(playlist_id)
            db_handler.add_start_end_season_index(season_table_id, season_start_index, season_end_index)


def collect_tv_shows(db_handler, media_folder):
    # Get list of all tv shows
    if tv_shows_dir_path_list := get_dir_list(media_folder):
        # Iterate over each tv show in the list
        for tv_show_dir_name in tv_shows_dir_path_list:
            # Build a path for the tv show
            tv_show_path = f"{media_folder}{tv_show_dir_name}/"
            if os.path.exists(tv_show_path):
                # Add show to playlist and show tracking
                playlist_id = db_handler.add_playlist(tv_show_dir_name)
                tv_show_id = db_handler.add_tv_show(playlist_id)
                collect_seasons(db_handler, playlist_id, tv_show_id, tv_show_path)
