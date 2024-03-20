import argparse
import json
import queue
import shutil
import os
import pathlib
import subprocess
import threading
from json import JSONDecodeError

import time
from datetime import datetime
import re
from pathvalidate import ValidationError, validate_filename

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
ALPHANUMERIC_INDEX_A = 97

ERROR_SUCCESS = 0
ERROR_TXT_FILE_DOESNT_EXIST = 1
ERROR_MP4_FILE_DOESNT_EXIST = 2
ERROR_TXT_FILE_EMPTY = 3
ERROR_TXT_FILE_INVALID_CONTENT = 4
ERROR_MP4_FILE_ALREADY_EXISTS = 5


class JobQueueFull(ValueError):
    pass


class EmptyTextFile(ValueError):
    pass


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
        error_dict = {"message": "Too many colons found", "string": timestamp_str, "colon_count": colon_count}
        raise InvalidTimestamp(error_dict)

    if h in ['', None] or m in ['', None] or s in ['', None]:
        error_dict = {"message": "Missing timestamp value", "string": timestamp_str, "hour": h, "minute": m,
                      "second": s}
        raise InvalidTimestamp(error_dict)

    try:
        h = int(h)
        m = int(m)
        s = int(s)
    except ValueError as e:
        error_dict = {"message": "Values not int", "string": timestamp_str, "hour": h, "minute": m, "second": s}
        raise InvalidTimestamp(error_dict)

    if h < 0 or m < 0 or s < 0:
        error_dict = {"message": "Values less than 0", "string": timestamp_str, "hour": h, "minute": m, "second": s}
        raise InvalidTimestamp(error_dict)

    return h * 3600 + m * 60 + s


class SubclipMetadata:
    playlist_title = ""
    media_title = ""
    season_index = None
    episode_index = None
    start_time = ""
    end_time = ""
    destination_file_path = None
    source_file_path = None
    file_name = None

    def __init__(self, subclip_metadata):
        playlist_title = ""
        media_title = ""
        season_index = None
        episode_index = None
        start_time = ""
        end_time = ""
        subclip_metadata_list = subclip_metadata.split(',')

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
            if not playlist_title:
                error_dict = {"message": "Missing playlist title", "string": subclip_metadata}
                raise InvalidPlaylistTitle(error_dict)
            if not media_title:
                error_dict = {"message": "Missing media title", "string": subclip_metadata}
                raise InvalidMediaTitle(error_dict)
            if not season_index:
                error_dict = {"message": "Missing season index", "string": subclip_metadata}
                raise InvalidSeasonIndex(error_dict)
            if not episode_index:
                error_dict = {"message": "Missing episode index", "string": subclip_metadata}
                raise InvalidEpisodeIndex(error_dict)
            if not start_time or not end_time:
                error_dict = {"message": "Missing start or end time", "string": subclip_metadata}
                raise InvalidTimestamp(error_dict)
        else:
            error_dict = {"message": "Missing content", "string": subclip_metadata}
            raise InvalidContentCount(error_dict)

        if start_time and end_time:
            start_time = convert_timestamp(start_time)
            end_time = convert_timestamp(end_time)
            if end_time <= start_time:
                error_dict = {"message": "End time >= start time", "string": subclip_metadata, "start_time": start_time,
                              "end_time": end_time}
                raise InvalidTimestamp(error_dict)
            self.start_time = start_time
            self.end_time = end_time
        if episode_index:
            try:
                self.episode_index = int(episode_index)
            except ValueError:
                error_dict = {"message": "Values not int", "string": subclip_metadata, "episode_index": episode_index}
                raise InvalidEpisodeIndex(error_dict)

            if self.episode_index < 0:
                error_dict = {"message": "Values less than 0", "string": subclip_metadata,
                              "episode_index": self.episode_index}
                raise InvalidEpisodeIndex(error_dict)

        if season_index:
            try:
                self.season_index = int(season_index)
            except ValueError:
                error_dict = {"message": "Values not int", "string": subclip_metadata, "season_index": season_index}
                raise InvalidSeasonIndex(error_dict)

            if self.season_index < 0:
                error_dict = {"message": "Values less than 0", "string": subclip_metadata,
                              "season_index": self.season_index}
                raise InvalidSeasonIndex(error_dict)

        if media_title:
            if type(media_title) != str:
                error_dict = {"message": "Media title is not str", "string": subclip_metadata,
                              "media_title": self.media_title}
                raise InvalidMediaTitle(error_dict)

            try:
                validate_filename(media_title, platform="Linux")
            except ValidationError as e:
                error_dict = {"message": f"Media title {e.reason.description}", "string": subclip_metadata,
                              "media_title": self.media_title}
                if len(e.args) > 0 and "invalids" in e.args[0]:
                    error_dict["invalids"] = re.search(r'invalids=(.*?), value=', e.args[0]).group(1).replace("'", "")
                raise InvalidMediaTitle(error_dict)
            self.media_title = media_title

        if playlist_title:
            if type(playlist_title) != str:
                error_dict = {"message": "Media title is not str", "string": subclip_metadata,
                              "playlist_title": self.playlist_title}
                raise InvalidPlaylistTitle(error_dict)

            try:
                validate_filename(playlist_title, platform="Linux")
            except ValidationError as e:
                error_dict = {"message": f"Media title {e.reason.description}", "string": subclip_metadata,
                              "playlist_title": self.playlist_title}
                if len(e.args) > 0 and "invalids" in e.args[0]:
                    error_dict["invalids"] = re.search(r'invalids=(.*?), value=', e.args[0]).group(1).replace("'", "")
                raise InvalidPlaylistTitle(error_dict)
            self.playlist_title = playlist_title

    def set_cmd_metadata(self, source_file_path, destination_file_path, media_title=""):
        if not destination_file_path or not self.playlist_title:
            destination_file_path = source_file_path.parent

        if self.playlist_title:
            destination_file_path = destination_file_path / self.playlist_title

        if self.season_index:
            destination_file_path = destination_file_path / f"Season {self.season_index}"

        if self.episode_index:
            destination_file_path = destination_file_path / f'{self.playlist_title} - s{self.season_index}e{self.episode_index}.mp4'
        else:
            destination_file_path = destination_file_path / f'{media_title}_{source_file_path.stem}.mp4'

        if destination_file_path.exists():
            raise FileExistsError({"message": "File already exists", "expected_path": str(destination_file_path.stem)})

        if not self.media_title:
            self.media_title = media_title

        self.media_title = self.media_title.strip().replace('"', "")
        self.file_name = source_file_path.stem.strip()
        self.source_file_path = str(source_file_path.as_posix()).strip()
        self.destination_file_path = str(destination_file_path.as_posix()).strip()

    def get_cmd(self):
        return [SPLITTER_BASH_CMD, self.source_file_path, self.destination_file_path, str(self.start_time),
                str(self.end_time), self.media_title]


def get_txt_file_content(txt_file_path):
    with open(txt_file_path, 'r') as f:
        return f.readlines()


def get_subclips_as_objs(txt_file_content):
    sub_clips = []
    for index, file_text in enumerate(txt_file_content):
        try:
            sub_clips.append(SubclipMetadata(file_text))
        except Exception as e:
            error_dict = e.args[0]
            error_dict["line_index"] = index
            raise ValueError(error_dict) from e
    return sub_clips


def get_sub_clips_from_txt_file(sub_clip_file):
    sub_clip_file_path = pathlib.Path(sub_clip_file).resolve()
    if not sub_clip_file_path.exists() or not sub_clip_file_path.is_file() or not sub_clip_file_path.suffix == ".txt":
        error_dict = {"message": "Missing file", "file_name": sub_clip_file, "expected_path": str(sub_clip_file_path)}
        raise FileNotFoundError(error_dict)

    subclip_file_content = get_txt_file_content(sub_clip_file_path)
    if not subclip_file_content:
        error_dict = {"message": "Text file empty", "file_name": sub_clip_file,
                      "expected_path": str(sub_clip_file_path)}
        raise EmptyTextFile(error_dict)
    try:
        return get_subclips_as_objs(subclip_file_content)
    except ValueError as e:
        error_dict = e.args[0]
        error_dict["file_name"] = sub_clip_file
        raise ValueError(error_dict) from e


def get_cmd_list(sub_clips: list[SubclipMetadata], sub_clip_file, media_output_parent_path=None):
    mp4_file = sub_clip_file.replace('.txt', '.mp4')
    source_file_path = pathlib.Path(mp4_file).resolve()

    if not source_file_path.exists() or not source_file_path.is_file() or not source_file_path.suffix == ".mp4":
        error_dict = {"message": "Missing file", "file_name": mp4_file, "expected_path": str(source_file_path)}
        raise FileNotFoundError(error_dict)

    for index, sub_clip in enumerate(sub_clips):
        sub_clip.set_cmd_metadata(source_file_path, media_output_parent_path, chr(ALPHANUMERIC_INDEX_A + index))


def extract_subclip(sub_clip):
    cmd = sub_clip.get_cmd()
    output_dir = pathlib.Path(cmd[2]).resolve().parent
    # time.sleep(1)
    print(cmd)
    print(output_dir)
    # output_dir.mkdir(parents=True, exist_ok=True)
    # subprocess.run(cmd, check=True, text=True)


class CmdData:
    metadata_file_path = ""
    cmd = None

    def __init__(self, metadata_file_path, cmd):
        self.metadata_file_path = metadata_file_path
        self.cmd = cmd


class SubclipProcessHandler(threading.Thread):
    subclip_process_queue = queue.Queue()
    current_cmd = None
    process_start = 0

    def run(self):
        while not self.subclip_process_queue.empty():
            self.process_start = datetime.now()
            current_cmd = self.subclip_process_queue.get()
            self.current_cmd = current_cmd.cmd
            extract_subclip(self.current_cmd)

        self.current_cmd = None

    def add_cmds_to_queue(self, metadata_file_path, cmd_list):
        if self.subclip_process_queue.qsize() > 10:
            raise JobQueueFull({"message": "Job queue full"})
        for cmd in cmd_list:
            self.subclip_process_queue.put(CmdData(metadata_file_path, cmd))
        if not self.is_alive():
            threading.Thread.__init__(self, daemon=True)
            self.start()

    def get_metadata(self):
        process_name = "Split queue empty"
        process_time = 0
        if current_cmd := self.current_cmd:
            process_name = current_cmd.media_title
            process_time = str(datetime.now() - self.process_start)

        return {
            "process_name": process_name,
            "process_time": process_time,
            "process_queue_size": self.subclip_process_queue.qsize()
        }


def main(sub_clip_file):
    try:
        sub_clips = get_sub_clips_from_txt_file(sub_clip_file)
        cmd_list = get_cmd_list(sub_clips, sub_clip_file)
        for cmd in cmd_list:
            extract_subclip(cmd)
        return cmd_list
    except ValueError as e:
        raise ValueError(e.args[0]) from e
    except FileNotFoundError as e:
        raise FileNotFoundError(e.args[0]) from e


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
        main(args.input_file)
