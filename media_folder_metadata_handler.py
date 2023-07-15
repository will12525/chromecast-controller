import json
import os
import traceback


CHROMECAST_ERR_SUCCESS = 0
CHROMECAST_ERR_NOT_A_FOLDER = 1

media_metadata_json_struct = [
    {
        "id": 0,
        "name": "name of show",
        "path": "/path/to/show",
        "season_count": 2,
        "episode_count": 4,
        "seasons": [
            {
                "id": 0,
                "name": "name",
                "path": "/path/to/season",
                "episode_count": 2,
                "episodes": [
                    {
                        "id": 0,
                        "name": "name of episode",
                        "path": "/path/to/episode"
                    },
                    {
                        "id": 1,
                        "name": "name of episode",
                        "path": "/path/to/episode"
                    }
                ]
            },
            {
                "id": 1,
                "name": "name",
                "path": "/path/to/season",
                "episode_count": 2,
                "episodes": [
                    {
                        "id": 0,
                        "name": "name of episode",
                        "path": "/path/to/episode"
                    },
                    {
                        "id": 1,
                        "name": "name of episode",
                        "path": "/path/to/episode"
                    }
                ]
            },
        ]
    },
    {
        "id": 1,
        "name": "name of show",
        "path": "/path/to/show",
        "season_count": 2,
        "episode_count": 4,
        "seasons": [
            {
                "id": 0,
                "name": "name",
                "path": "/path/to/season",
                "episode_count": 2,
                "episodes": [
                    {
                        "id": 0,
                        "name": "name of episode",
                        "path": "/path/to/episode"
                    },
                    {
                        "id": 1,
                        "name": "name of episode",
                        "path": "/path/to/episode"
                    }
                ]
            },
            {
                "id": 1,
                "name": "name",
                "path": "/path/to/season",
                "episode_count": 2,
                "episodes": [
                    {
                        "id": 0,
                        "name": "name of episode",
                        "path": "/path/to/episode"
                    },
                    {
                        "id": 1,
                        "name": "name of episode",
                        "path": "/path/to/episode"
                    }
                ]
            },
        ]
    },
]


def media_folder_entry_point():
    scan_media_folder()


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


def scan_media_folder():
    media_folder = "/media/hdd1/plex_media/tv_shows/"
    err_code = CHROMECAST_ERR_SUCCESS
    tv_show_seasons_dir_path_list = None
    tv_show_season_episodes_dir_path_list = None
    media_folder_metadata_json = []

    # Get list of all tv shows
    if tv_shows_dir_path_list := get_dir_list(media_folder):
        # Iterate over each tv show in the list
        for idx, tv_show_dir_name in enumerate(tv_shows_dir_path_list):
            # Build a path for the tv show
            tv_show_path = f"{media_folder}{tv_show_dir_name}/"
            # Get list of all seasons in a tv show
            if tv_show_seasons_dir_path_list := sort_season_dir_list(tv_show_path):
                # Iterate over each season in the list
                tv_show_season_list = []
                total_episode_count = 0
                for idy, tv_show_season_dir_name in enumerate(tv_show_seasons_dir_path_list):
                    # Build a path for the tv show season
                    tv_show_season_path = f"{tv_show_path}{tv_show_season_dir_name}/"
                    # Get list of all episodes in a tv show
                    if tv_show_seasons_dir_path_list := get_dir_list(tv_show_season_path):
                        # Iterate over each episode in the list
                        tv_show_season_episode_list = []
                        for idz, tv_show_season_episode_dir_name in enumerate(tv_show_seasons_dir_path_list):
                            # Build a path for the tv show season episode
                            tv_show_season_episode_path = f"{tv_show_season_path}{tv_show_season_episode_dir_name}"
                            if os.path.exists(tv_show_season_episode_path) and os.path.isfile(tv_show_season_episode_path):
                                tv_show_season_episode_list.append({"id": idz,
                                                                    "name": tv_show_season_episode_dir_name,
                                                                    "path": tv_show_season_episode_path})
                        total_episode_count += len(tv_show_season_episode_list)
                        tv_show_season_list.append({"id": idy,
                                                    "name": tv_show_season_dir_name,
                                                    "path": tv_show_season_path,
                                                    "episode_count": len(tv_show_season_episode_list),
                                                    "episodes": tv_show_season_episode_list})

                media_folder_metadata_json.append({"id": idx,
                                                   "name": tv_show_dir_name,
                                                   "path": tv_show_path,
                                                   "season_count": len(tv_show_season_list),
                                                   "episode_count": total_episode_count,
                                                   "seasons": tv_show_season_list})

    save_metadata_to_file(media_folder_metadata_json)



    # if os.path.exists(media_folder):
    #     tv_shows_dir_path_list = sorted(os.listdir(media_folder))
    #     for tv_show_dir_name in tv_shows_dir_path_list:
    #         tv_show_dir_path_name = f"{media_folder}{tv_show_dir_name}/"
    #         if os.path.exists(tv_show_dir_path_name) and os.path.isdir(tv_show_dir_path_name):
    #             print("-----------NEW SHOW-----------")
    #             print(tv_show_dir_name)
    #             tv_show_seasons_dir_path_list = sorted(os.listdir(tv_show_dir_path_name))
    #             print(tv_show_seasons_dir_path_list)
