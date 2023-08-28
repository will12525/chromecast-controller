import json
import os
import traceback

"""
API FUNCTIONS
media_metadata_init()
scan_media_folder()



"""

MEDIA_METADATA_FILE = "tv_show_metadata.json"


def media_metadata_init(media_folder_path):
    # media_metadata = None
    media_metadata_file_path = f"{os.path.dirname(__file__)}/{MEDIA_METADATA_FILE}"
    print(media_metadata_file_path)
    if os.path.exists(media_metadata_file_path) and os.path.isfile(media_metadata_file_path):
        print("Loading file")
        media_metadata = load_metadata_from_file(media_metadata_file_path)
    else:
        print("Generating file")
        media_metadata = generate_tv_show_list(media_folder_path)
    return media_metadata


def load_metadata_from_file(media_metadata_file_path):
    with open(media_metadata_file_path, 'r') as f:
        media_metadata_json = json.load(f)
    return media_metadata_json


def save_metadata_to_file(tv_show_metadata_json):
    with open('tv_show_metadata.json', 'w') as f:
        json.dump(tv_show_metadata_json, f, indent=4)


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

            except ValueError:
                print(f"ERROR: {tv_show_season_name_str}")
            except Exception:
                print(f"ERROR READING: {unsorted_tv_show_season_name_list}")
                print(traceback.format_exc())

    sorted_tv_show_season_name_dict_keys = list(tv_show_season_name_dict.keys())
    sorted_tv_show_season_name_dict_keys.sort()
    return [tv_show_season_name_dict[i] for i in sorted_tv_show_season_name_dict_keys]


def generate_episode_list(tv_show_season_path):
    tv_show_season_episode_list = []
    # Get list of all episodes in a tv show
    if tv_show_seasons_dir_path_list := get_dir_list(tv_show_season_path):
        # Iterate over each episode in the list
        for idy, tv_show_season_episode_dir_name in enumerate(tv_show_seasons_dir_path_list):
            # Build a path for the tv show season episode
            tv_show_season_episode_path = f"{tv_show_season_path}{tv_show_season_episode_dir_name}"
            if os.path.exists(tv_show_season_episode_path) and os.path.isfile(tv_show_season_episode_path):
                tv_show_season_episode_list.append({"id": idy,
                                                    "name": tv_show_season_episode_dir_name,
                                                    "path": tv_show_season_episode_path})
    return tv_show_season_episode_list


def generate_season_list(tv_show_path):
    tv_show_season_list = []
    # Get list of all seasons in a tv show
    if tv_show_seasons_dir_path_list := sort_season_dir_list(tv_show_path):
        # Iterate over each season in the list
        for idy, tv_show_season_dir_name in enumerate(tv_show_seasons_dir_path_list):
            # Build a path for the tv show season
            tv_show_season_path = f"{tv_show_path}{tv_show_season_dir_name}/"
            # Get list of all episodes in a tv show
            tv_show_season_episode_list = generate_episode_list(tv_show_season_path)
            # total_episode_count += len(tv_show_season_episode_list)
            tv_show_season_list.append({"id": idy,
                                        "name": tv_show_season_dir_name,
                                        "path": tv_show_season_path,
                                        "episode_count": len(tv_show_season_episode_list),
                                        "episodes": tv_show_season_episode_list})
    return tv_show_season_list


def generate_tv_show_list(media_folder):
    media_folder_metadata_json = []
    # Get list of all tv shows
    if tv_shows_dir_path_list := get_dir_list(media_folder):
        # Iterate over each tv show in the list
        for idy, tv_show_dir_name in enumerate(tv_shows_dir_path_list):
            # Build a path for the tv show
            tv_show_path = f"{media_folder}{tv_show_dir_name}/"
            tv_show_season_list = generate_season_list(tv_show_path)
            total_episode_count = 0
            for season in tv_show_season_list:
                total_episode_count += season.get("episode_count", 0)

            media_folder_metadata_json.append({"id": idy,
                                               "name": tv_show_dir_name,
                                               "path": tv_show_path,
                                               "season_count": len(tv_show_season_list),
                                               "episode_count": total_episode_count,
                                               "seasons": tv_show_season_list})
    return media_folder_metadata_json


