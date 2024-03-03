import argparse
import subprocess
import shutil
import os
import pathlib
import sys

ASK_QUESTION = True
"""
Convert to .exe

venv/Scripts/activate
pyinstaller mp4_splitter.py
pyinstaller --onefile --paths .\venv\Lib\site-packages mp4_splitter.py
scp .\dist\mp4_splitter.exe willow@192.168.1.200:/home/willow/workspace/mp4_splitter/

On GAIA:
scp willow@192.168.1.200:/home/willow/workspace/mp4_splitter/mp4_splitter.exe .\Desktop\
"""

SPLITTER_BASH_CMD = "/media/hdd1/plex_media/splitter/splitter.sh"
DEFAULT_MP4_FILE = "raw_file/2022-06-12_06-22-06.mp4"
DEFAULT_EPISODE_START_INDEX = 0
DEFAULT_SEASON_START_INDEX = None
# DEFAULT_TV_SHOW_NAME = "abc"
ALPHANUMERIC_INDEX_A = 97


def quit_program(message):
    print(message)
    input("Press enter to quit...")
    quit()


ERROR_SUCCESS = 0
ERROR_TXT_FILE_DOESNT_EXIST = 1
ERROR_MP4_FILE_DOESNT_EXIST = 2
ERROR_TXT_FILE_EMPTY = 3
ERROR_TXT_FILE_INVALID_CONTENT = 4
ERROR_MP4_FILE_ALREADY_EXISTS = 5


def extract_subclip(output_path, cmd_list):
    print(output_path)
    print(cmd_list)
    # output_path.mkdir(parents=True, exist_ok=True)
    # subprocess.run(cmd_list, check=True, text=True)


def load_txt_file(txt_file_path):
    with open(txt_file_path) as f:
        return f.readlines()


class InvalidTimestamp(ValueError):
    pass


class InvalidContentCount(ValueError):
    pass


class InvalidContent(ValueError):
    pass


class InvalidPlaylistTitle(ValueError):
    pass


class InvalidMediaTitle(ValueError):
    pass


class InvalidSeasonIndex(ValueError):
    pass


class InvalidEpisodeIndex(ValueError):
    pass


def convert_timestamp(timestamp_str):
    colon_count = timestamp_str.count(":")
    h = m = s = 0
    if colon_count == 0:
        (s,) = timestamp_str.split(':')
    elif colon_count == 1:
        m, s = timestamp_str.split(':')
    elif colon_count == 2:
        h, m, s = timestamp_str.split(':')
    else:
        print(f"To many colons found: {colon_count}")
        raise InvalidTimestamp
    h = int(h)
    m = int(m)
    s = int(s)

    if h < 0 or m < 0 or s < 0:
        raise InvalidTimestamp

    return h * 3600 + m * 60 + s


class SubclipMetadata:
    playlist_title = ""
    media_title = ""
    season_index = None
    episode_index = None
    start_time = ""
    end_time = ""

    def __init__(self, subclip_metadata):
        playlist_title = ""
        media_title = ""
        season_index = None
        episode_index = None
        start_time = ""
        end_time = ""
        subclip_metadata_list = subclip_metadata.split(',')
        # print(len(subclip_metadata_list))

        if len(subclip_metadata_list) == 2:
            start_time = subclip_metadata_list[0]
            end_time = subclip_metadata_list[1]
        elif len(subclip_metadata_list) == 6:
            playlist_title = subclip_metadata_list[0]
            media_title = subclip_metadata_list[1]
            season_index = subclip_metadata_list[2]
            episode_index = subclip_metadata_list[3]
            start_time = subclip_metadata_list[4]
            end_time = subclip_metadata_list[5]
        else:
            raise InvalidContentCount

        if start_time and end_time:
            self.start_time = convert_timestamp(start_time)
            self.end_time = convert_timestamp(end_time)
        if episode_index:
            try:
                self.episode_index = int(episode_index)
            except ValueError:
                raise InvalidEpisodeIndex
        if season_index:
            try:
                self.season_index = int(season_index)
            except ValueError:
                raise InvalidSeasonIndex
        if media_title:
            if type(self.media_title) != str:
                raise InvalidMediaTitle
            else:
                self.media_title = media_title
        if playlist_title:
            if type(self.playlist_title) != str:
                raise InvalidPlaylistTitle
            else:
                self.playlist_title = playlist_title

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return (f"Start: {self.start_time}, End: {self.end_time}\n"
                f"playlist_title: {self.playlist_title}, media_title: {self.media_title}\n"
                f"season_index: {self.season_index}, episode_index: {self.episode_index}")


def convert_txt_file_content(txt_file_content):
    sub_clips = []
    for file_text in txt_file_content:
        try:
            sub_clips.append(SubclipMetadata(file_text))
        except ValueError as e:
            return []
    return sub_clips


def get_cmd_list(output_path, sub_clips, mp4_process_file, video_path):
    cmd_list = []
    current_index = ALPHANUMERIC_INDEX_A
    show_dir_name = ""
    season_dir_name = ""

    for index, sub_clip in enumerate(sub_clips):
        if sub_clip.season_index:
            season_dir_name = f"S{sub_clip.season_index}/"
        if sub_clip.playlist_title:
            show_dir_name = f"{sub_clip.playlist_title}/"

        file_index = chr(current_index + index)
        media_output_path = output_path / f'{show_dir_name}{season_dir_name}{file_index}_{video_path.stem}.mp4'
        if sub_clip.episode_index:
            file_index = f'E{sub_clip.episode_index}'
            media_output_path = output_path / f'{show_dir_name}{season_dir_name}{file_index}.mp4'

        episode_title = file_index
        if sub_clip.media_title:
            episode_title = sub_clip.media_title

        if media_output_path.exists():
            print(f"ERROR: File exists: {media_output_path}.")
            continue
        # print(media_output_path)
        # print(f"Splitting: {sub_clip.start_time}:{sub_clip.end_time}, {mp4_process_file} -> {episode_path}")
        cmd_list.append([SPLITTER_BASH_CMD, str(mp4_process_file), str(media_output_path), str(sub_clip.start_time),
                         str(sub_clip.end_time), str(episode_title)])
    return cmd_list


def check_txt_file_valid(txt_process_file):
    text_path = pathlib.Path(txt_process_file).resolve()
    if not text_path.exists() or not text_path.is_file() or not text_path.suffix == ".txt":
        return ERROR_TXT_FILE_DOESNT_EXIST
    time_lines = load_txt_file(text_path)

    if not time_lines:
        return ERROR_TXT_FILE_EMPTY
    try:
        convert_txt_file_content(time_lines)
    except ValueError:
        return ERROR_TXT_FILE_INVALID_CONTENT


def run_image_processor_v2(txt_process_file, destination_dir=None):
    text_path = pathlib.Path(txt_process_file).resolve()
    mp4_process_file = txt_process_file.replace('.txt', '.mp4')
    video_path = pathlib.Path(mp4_process_file).resolve()
    if not text_path.exists() or not text_path.is_file() or not text_path.suffix == ".txt":
        return ERROR_TXT_FILE_DOESNT_EXIST
    if not video_path.exists() or not video_path.is_file() or not video_path.suffix == ".mp4":
        return ERROR_MP4_FILE_DOESNT_EXIST

    time_lines = load_txt_file(text_path)

    if not time_lines:
        return ERROR_TXT_FILE_EMPTY
    try:
        sub_clips = convert_txt_file_content(time_lines)
        if not sub_clips:
            return ERROR_TXT_FILE_INVALID_CONTENT

        if not destination_dir or not sub_clips[0].playlist_title:
            destination_dir = video_path.parent
        cmd_list = get_cmd_list(destination_dir, sub_clips, mp4_process_file, video_path)

        for cmd in cmd_list:
            # print(cmd)
            extract_subclip(video_path.parent, cmd)
    except ValueError:
        return ERROR_TXT_FILE_INVALID_CONTENT
    return 0


if __name__ == "__main__":
    dirpath = "abc"
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)
    # Old way
    # main()

    # CLI Way
    parser = argparse.ArgumentParser(description='Splits mp4 files given a mp4 file with timestamp file')
    # parser.add_argument('-f', '--file', help='File to be split', required=True, dest='input_file', type=str)
    parser.add_argument('-f', help='File to be split', default=DEFAULT_MP4_FILE, dest='input_file', type=str)
    args = parser.parse_args()
    if args.input_file:
        # print(args.input_file)
        run_image_processor_v2(args.input_file)
