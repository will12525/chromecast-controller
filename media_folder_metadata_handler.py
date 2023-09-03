import json
import os
import traceback

"""
API FUNCTIONS
media_metadata_init(media_folder_path)
generate_tv_show_list(media folder path)
get_tv_show_metadata(media_folder_metadata, tv_show_id)
get_tv_show_season_metadata(media_folder_metadata, tv_show_id, tv_show_season_id)
get_tv_show_season_episode_metadata(media_folder_metadata, tv_show_id, tv_show_season_id, tv_show_season_episode_id)

"""

MEDIA_METADATA_VERSION = 1


class MediaFolderMetadataHandler:
    tv_show_id = 0
    tv_show_season_id = 0
    tv_show_season_episode_id = 0
    media_metadata = None

    def __init__(self, media_metadata_file, media_folder_path):
        self.media_metadata = get_media_metadata(media_metadata_file, media_folder_path)

    def set_media_metadata(self, media_metadata):
        self.media_metadata = media_metadata

    def get_media_metadata(self):
        return self.media_metadata

    def set_episode_id(self, tv_show_id, tv_show_season_id, tv_show_season_episode_id):
        if get_tv_show_season_episode_metadata(self.media_metadata, tv_show_id, tv_show_season_id,
                                               tv_show_season_episode_id):
            self.tv_show_id = tv_show_id
            self.tv_show_season_id = tv_show_season_id
            self.tv_show_season_episode_id = tv_show_season_episode_id
            return True
        return False

    def get_episode_info(self):
        return get_tv_show_season_episode_metadata(self.media_metadata,
                                                   self.tv_show_id,
                                                   self.tv_show_season_id,
                                                   self.tv_show_season_episode_id)

    def get_url(self, media_server_url):
        if self.media_metadata and (media_folder_path := self.media_metadata.get("path")):
            if current_episode := self.get_episode_info():
                if current_episode_path := current_episode.get("path"):
                    return current_episode_path.replace(media_folder_path, media_server_url)
        return None

    def increment_next_episode(self):
        if self.media_metadata:
            if not self.__increment_episode(self.media_metadata):
                self.tv_show_season_episode_id = 0
                if not self.__increment_season(self.media_metadata):
                    self.tv_show_season_id = 0

    def __increment_season(self, media_metadata):
        if get_tv_show_season_episode_metadata(
                media_metadata,
                self.tv_show_id,
                self.tv_show_season_id + 1,
                0):
            self.tv_show_season_id += 1
            self.tv_show_season_episode_id = 0
            return True
        return False

    def __increment_episode(self, media_metadata):
        if get_tv_show_season_episode_metadata(
                media_metadata,
                self.tv_show_id,
                self.tv_show_season_id,
                self.tv_show_season_episode_id + 1):
            self.tv_show_season_episode_id += 1
            return True
        return False


class EpisodeInfo:
    tv_show_id = 0
    tv_show_season_id = 0
    tv_show_season_episode_id = 0
    media_metadata = None

    def __init__(self, media_metadata_file, media_folder_path,
                 tv_show_id=0, tv_show_season_id=0, tv_show_season_episode_id=0):
        self.tv_show_id = tv_show_id
        self.tv_show_season_id = tv_show_season_id
        self.tv_show_season_episode_id = tv_show_season_episode_id
        self.media_metadata = get_media_metadata(media_metadata_file, media_folder_path)

    def get_episode_info(self):
        if self.media_metadata:
            return get_tv_show_season_episode_metadata(
                    self.media_metadata,
                    self.tv_show_id,
                    self.tv_show_season_id,
                    self.tv_show_season_episode_id)
        return None

    def get_url(self, media_server_url):
        if self.media_metadata and (media_folder_path := self.media_metadata.get("path")):
            if current_episode := self.get_episode_info():
                if current_episode_path := current_episode.get("path"):
                    return current_episode_path.replace(media_folder_path, media_server_url)
        return None

    def increment_next_episode(self):
        if not self.__increment_episode():
            if not self.__increment_season():
                self.tv_show_season_id = 0
                self.tv_show_season_episode_id = 0

    def __increment_season(self):
        if self.media_metadata:
            if get_tv_show_season_episode_metadata(
                    self.media_metadata,
                    self.tv_show_id,
                    self.tv_show_season_id + 1,
                    0):
                self.tv_show_season_id += 1
                self.tv_show_season_episode_id = 0
                return True
        return False

    def __increment_episode(self):
        if self.media_metadata:
            if get_tv_show_season_episode_metadata(
                    self.media_metadata,
                    self.tv_show_id,
                    self.tv_show_season_id,
                    self.tv_show_season_episode_id + 1):
                self.tv_show_season_episode_id += 1
                return True
        return False


def get_media_metadata(media_metadata_file, media_folder_path):
    media_metadata = load_media_metadata_from_file(media_metadata_file)
    if not media_metadata or (media_metadata and media_metadata.get("version") != MEDIA_METADATA_VERSION):
        media_metadata = generate_media_metadata(media_metadata_file, media_folder_path)
    return media_metadata


def generate_media_metadata(media_metadata_file, media_folder_path):
    media_metadata = generate_tv_show_list(media_folder_path)
    save_metadata_to_file(media_metadata_file, media_metadata)
    return media_metadata


def load_media_metadata_from_file(media_metadata_file) -> [dict, None]:
    if os.path.exists(media_metadata_file) and os.path.isfile(media_metadata_file):
        with open(media_metadata_file, 'r') as f:
            return json.load(f)
    return None


def save_metadata_to_file(media_metadata_file, tv_show_metadata_json):
    with open(media_metadata_file, 'w') as f:
        json.dump(tv_show_metadata_json, f, indent=4)


def get_metadata_content_by_id(media_metadata_list, media_id):
    if 0 <= media_id < len(media_metadata_list):
        return media_metadata_list[media_id]
    return None


def get_tv_show_name_list(media_folder_metadata):
    tv_show_name_list = []
    if media_folder_metadata and (tv_show_list := media_folder_metadata.get("tv_shows")):
        for tv_show_metadata in tv_show_list:
            tv_show_name_list.append(tv_show_metadata.get("name"))
    return tv_show_name_list


def get_tv_show_season_name_list(media_folder_metadata, tv_show_id):
    tv_show_season_name_list = []
    if media_folder_metadata and (tv_show_metadata := get_tv_show_metadata(media_folder_metadata, tv_show_id)):
        for tv_show_season_metadata in tv_show_metadata.get("seasons"):
            tv_show_season_name_list.append(tv_show_season_metadata.get("name"))
    return tv_show_season_name_list


def get_tv_show_season_episode_name_list(media_folder_metadata, tv_show_id, tv_show_season_id):
    tv_show_season_episode_name_list = []
    if media_folder_metadata and (tv_show_season_metadata := get_tv_show_season_metadata(
            media_folder_metadata, tv_show_id, tv_show_season_id)):
        for tv_show_season_episode_metadata in tv_show_season_metadata.get("episodes"):
            tv_show_season_episode_name_list.append(tv_show_season_episode_metadata.get("name"))
    return tv_show_season_episode_name_list


def get_tv_show_metadata(media_folder_metadata, tv_show_id):
    if media_folder_metadata:
        return get_metadata_content_by_id(media_folder_metadata.get("tv_shows"), tv_show_id)
    return None


def get_tv_show_season_metadata(media_folder_metadata, tv_show_id, tv_show_season_id):
    if media_folder_metadata and (tv_show_metadata := get_tv_show_metadata(media_folder_metadata, tv_show_id)):
        return get_metadata_content_by_id(tv_show_metadata.get("seasons"), tv_show_season_id)
    return None


def get_tv_show_season_episode_metadata(media_folder_metadata, tv_show_id,
                                        tv_show_season_id, tv_show_season_episode_id):
    if media_folder_metadata and (tv_show_season_episode_list := get_tv_show_season_metadata(
            media_folder_metadata, tv_show_id, tv_show_season_id)):
        return get_metadata_content_by_id(tv_show_season_episode_list.get("episodes"), tv_show_season_episode_id)
    return None


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
    media_folder_metadata_json = {}
    tv_show_metadata_list = []
    # Get list of all tv shows
    if tv_shows_dir_path_list := get_dir_list(media_folder):
        # Iterate over each tv show in the list
        for idy, tv_show_dir_name in enumerate(tv_shows_dir_path_list):
            # Build a path for the tv show
            tv_show_path = f"{media_folder}{tv_show_dir_name}/"
            if os.path.exists(tv_show_path):
                tv_show_season_list = generate_season_list(tv_show_path)
                total_episode_count = 0
                for season in tv_show_season_list:
                    total_episode_count += season.get("episode_count", 0)

                tv_show_metadata_list.append({"id": idy,
                                              "name": tv_show_dir_name,
                                              "path": tv_show_path,
                                              "season_count": len(tv_show_season_list),
                                              "episode_count": total_episode_count,
                                              "seasons": tv_show_season_list})

    media_folder_metadata_json["version"] = MEDIA_METADATA_VERSION
    media_folder_metadata_json["path"] = media_folder
    media_folder_metadata_json["tv_shows"] = tv_show_metadata_list
    media_folder_metadata_json["tv_show_count"] = len(tv_show_metadata_list)
    return media_folder_metadata_json
