import hashlib
import pathlib
import re
from enum import Enum, auto

import ffmpeg

MOVIE_PATTERN = r".*/([\w\W]+) \((\d{4})\)\.mp4$"
TV_PATTERN = r".*\/([\w\W]+) - s(\d+)e(\d+)\.mp4$"
BOOK_PATTERN = r".*\/([\w\W]+) - ([\w\W]+).mp4$"

mp4_file_ext = '*.mp4'
txt_file_ext = '*.txt'


class ContentType(Enum):
    MEDIA = auto()
    MOVIE = auto()
    SEASON = auto()
    TV_SHOW = auto()
    TV = auto()
    PLAYLIST = auto()
    PLAYLISTS = auto()
    BOOK = auto()
    RAW = auto()

    def get_next(self):
        if self == self.PLAYLISTS:
            return self.PLAYLIST
        if self == self.TV:
            return self.TV_SHOW
        if self == self.TV_SHOW:
            return self.SEASON
        if self == self.SEASON:
            return self.MEDIA
        if self == self.PLAYLIST:
            return self.MEDIA
        if self == self.MOVIE:
            return self.MEDIA

    def get_last(self):
        if self == self.SEASON:
            return self.TV_SHOW
        if self == self.TV_SHOW:
            return self.TV
        if self == self.PLAYLIST:
            return self.PLAYLISTS

    @classmethod
    def list(cls):
        return list(map(lambda c: c, cls))


# Get the new path: media_directory_info
# Get list of titles: location of media
# Get tv show metadata
# Get movie metadata
# Get new tv show metadata
# Move title txt files
# Move tv show mp4 files


def get_file_hash(extra_metadata):
    with open(extra_metadata.get("full_file_path"), 'rb') as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    extra_metadata['md5sum'] = file_hash.hexdigest()


def get_ffmpeg_metadata(path, content_data):
    try:
        if ffmpeg_probe_result := ffmpeg.probe(path):
            if ffmpeg_probe_result_format := ffmpeg_probe_result.get('format'):
                # runtime = ffmpeg_probe_result_format.get('duration')
                # content_data["content_duration"] = round(float(runtime) / 60)
                # print(json.dumps(ffmpeg_probe_result_format, indent=4))
                if tags := ffmpeg_probe_result_format.get('tags'):
                    content_data["content_title"] = tags.get('title', '')
    except ffmpeg.Error as e:
        content_data["tags"].append({"tag_title": "broken?"})
        # print("get_ffmpeg_metadata: output")
        # print(e.stdout)
        # print("get_ffmpeg_metadata: err")
        print(f"ERROR: FFMPEG: {path}")
        print(e.stderr)
        pass


default_content_data = {
    "content_directory_id": None,
    "content_title": '',
    "content_src": '',
    "description": '',
    "img_src": '',
    "content_index": '',
    "tags": [],
}
default_container_data = {
    "container_title": "",
    "description": "",
    "img_src": '',
    "content_index": None,
    "tags": [],
    "container_content": []
}


def file_exists_with_extensions(path, file_name) -> pathlib.Path:
    """Checks if a file exists with any of the given extensions.

    Args:
        path (Path): The base path of the file.
        file_name (str): Name of file to check.
        # extensions (list): A list of file extensions to check.

    Returns:
        bool: True if the file exists with any of the given extensions, False otherwise.
    """

    for ext in [".png", ".jpg"]:
        file_path = path / f"{file_name}{ext}"
        if file_path.exists():
            return file_path


def build_movie(content_src, mp4_file_path, match, content_data):
    parent_folder = mp4_file_path.parent
    movie_title, movie_year = match.groups()

    content_data["content_title"] = movie_title
    content_data["description"] = movie_year
    content_data["tags"] = [{"tag_title": "movie"}]
    if img_src := file_exists_with_extensions(parent_folder, mp4_file_path.name):
        content_data['img_src'] = img_src.as_posix().replace(content_src, '')


def build_book(content_src, mp4_file_path, match, content_data):
    parent_folder = mp4_file_path.parent
    book_title, book_author = match.groups()

    content_data["content_title"] = book_title
    content_data["description"] = book_author
    content_data["tags"] = [{"tag_title": "book"}]
    if img_src := file_exists_with_extensions(parent_folder, mp4_file_path.name):
        content_data['img_src'] = img_src.as_posix().replace(content_src, '')


def build_tv_show(content_src, mp4_file_path, match, content_data):
    parent_folder = mp4_file_path.parent
    container_path = parent_folder.as_posix().replace(content_src, '')
    tv_show_title, season_index_str, episode_index_str = match.groups()
    season_index = int(season_index_str)
    episode_index = int(episode_index_str)

    content_data["content_index"] = episode_index
    content_data["tags"] = [{"tag_title": "episode"}]
    if img_src := file_exists_with_extensions(parent_folder, mp4_file_path.name):
        content_data['img_src'] = img_src.as_posix().replace(content_src, '')
    if mp4_file_path.exists():
        get_ffmpeg_metadata(mp4_file_path, content_data)

    if not content_data.get("content_title"):
        content_data["content_title"] = f"Episode {episode_index}"

    season_container_content = default_container_data.copy()
    season_container_content["container_title"] = f'Season {season_index}'
    season_container_content["content_index"] = f'{season_index}'
    season_container_content["tags"] = [{"tag_title": "season"}]
    season_container_content["container_content"] = [content_data]
    season_container_content["container_path"] = container_path
    if img_src := file_exists_with_extensions(parent_folder, season_container_content["container_title"]):
        season_container_content['img_src'] = img_src.as_posix().replace(content_src, '')

    tv_container_content = default_container_data.copy()
    tv_container_content["container_title"] = tv_show_title
    tv_container_content["tags"] = [{"tag_title": "tv"}, {"tag_title": "tv show"}]
    tv_container_content["container_content"] = [season_container_content]
    tv_container_content["container_path"] = container_path
    if img_src := file_exists_with_extensions(parent_folder, tv_show_title):
        tv_container_content['img_src'] = img_src.as_posix().replace(content_src, '')
    elif img_src := file_exists_with_extensions(parent_folder, "cover"):
        tv_container_content['img_src'] = img_src.as_posix().replace(content_src, '')

    return tv_container_content


def get_content_type(file_name):
    content_type = None
    mp4_file_path_posix = pathlib.Path(file_name).as_posix()
    if match := re.search(TV_PATTERN, mp4_file_path_posix):
        content_type = ContentType.TV
    elif match := re.search(MOVIE_PATTERN, mp4_file_path_posix):
        content_type = ContentType.MOVIE
    elif match := re.search(BOOK_PATTERN, mp4_file_path_posix):
        content_type = ContentType.BOOK
    else:
        print(f"Unknown content type: {file_name}")
    return content_type, match


def collect_mp4_files(content_directory_info):
    content_directory_src = pathlib.Path(content_directory_info.get("content_src"))
    content_directory_src_posix = content_directory_src.as_posix()
    for mp4_file_path in list(content_directory_src.rglob(mp4_file_ext)):
        print(mp4_file_path)
        mp4_file_path_posix = mp4_file_path.as_posix()
        (content_type, match) = get_content_type(mp4_file_path.as_posix())
        container_data = None
        content_data = default_content_data.copy()
        content_data['content_directory_id'] = content_directory_info['id']
        content_data['content_src'] = mp4_file_path_posix.replace(content_directory_src_posix, '')
        if ContentType.TV == content_type:
            container_data = build_tv_show(content_directory_src_posix, mp4_file_path, match, content_data)
        elif ContentType.MOVIE == content_type:
            build_movie(content_directory_src_posix, mp4_file_path, match, content_data)
        elif ContentType.BOOK == content_type:
            build_book(content_directory_src_posix, mp4_file_path, match, content_data)
        else:
            # print(media_folder_mp4.as_posix())
            print(f"Unknown media type: {mp4_file_path}")
            # print(mp4_file_path.as_posix())
            continue

        if container_data:
            yield container_data
        else:
            yield content_data
