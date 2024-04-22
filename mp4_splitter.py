import queue
import pathlib
import subprocess
import threading
from json import JSONDecodeError

from datetime import datetime
import re
from pathvalidate import ValidationError, validate_filename

import config_file_handler
from database_handler.media_metadata_collector import mp4_file_ext

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
    except ValueError:
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
            if type(media_title) is not str:
                error_dict = {"message": "Media title is not str", "string": subclip_metadata,
                              "media_title": self.media_title}
                raise InvalidMediaTitle(error_dict)
            media_title = media_title.strip().replace('"', "")
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
            if type(playlist_title) is not str:
                error_dict = {"message": "Media title is not str", "string": subclip_metadata,
                              "playlist_title": self.playlist_title}
                raise InvalidPlaylistTitle(error_dict)

            try:
                validate_filename(playlist_title, platform="Linux")
                self.playlist_title = playlist_title
            except ValidationError as e:
                error_dict = {"message": f"Media title {e.reason.description}", "string": subclip_metadata,
                              "playlist_title": self.playlist_title}
                if len(e.args) > 0 and "invalids" in e.args[0]:
                    error_dict["invalids"] = re.search(r'invalids=(.*?), value=', e.args[0]).group(1).replace("'", "")
                raise InvalidPlaylistTitle(error_dict)

    def set_cmd_metadata(self, source_file_path, destination_file_path, media_title):
        if not destination_file_path or not self.playlist_title:
            destination_file_path = source_file_path.parent

        if self.playlist_title:
            destination_file_path = destination_file_path / self.playlist_title

        if self.episode_index:
            destination_file_path = destination_file_path / f'{self.playlist_title} - s{self.season_index}e{self.episode_index}.mp4'
        else:
            destination_file_path = destination_file_path / f'{media_title}_{source_file_path.stem}.mp4'

        if destination_file_path.exists():
            raise FileExistsError({"message": "File already exists", "file_name": destination_file_path.name})

        if not self.media_title:
            self.media_title = media_title

        # self.media_title = self.media_title.strip().replace('"', "")
        self.file_name = source_file_path.stem.strip()
        self.source_file_path = str(source_file_path.as_posix()).strip()
        self.destination_file_path = str(destination_file_path.as_posix()).strip()


def get_sub_clips_as_objs(txt_file_content):
    sub_clips = []
    error_log = []
    for index, file_text in enumerate(txt_file_content):
        try:
            sub_clips.append(SubclipMetadata(file_text))
        except Exception as e:
            error_dict = e.args[0]
            error_dict["line_index"] = index
            error_log.append(error_dict)
    return sub_clips, error_log


def get_sub_clips_from_txt_file(sub_clip_file):
    sub_clip_file_path = pathlib.Path(sub_clip_file).resolve()
    if not sub_clip_file_path.exists() or not sub_clip_file_path.is_file() or not sub_clip_file_path.suffix == ".txt":
        error_dict = {"message": "Missing file", "file_name": sub_clip_file}
        raise FileNotFoundError(error_dict)

    subclip_file_content = config_file_handler.load_txt_file_content(sub_clip_file_path)
    if not subclip_file_content:
        error_dict = {"message": "Text file empty", "file_name": sub_clip_file_path.name}
        raise EmptyTextFile(error_dict)

    sub_clips, errors = get_sub_clips_as_objs(subclip_file_content)
    for error in errors:
        error.update({"file_name": sub_clip_file_path.name})
    return sub_clips, errors


def get_cmd_list(sub_clips: list[SubclipMetadata], sub_clip_file, media_output_parent_path=None, error_log=None):
    if error_log is None:
        error_log = []

    mp4_file = sub_clip_file.replace('.txt', '.mp4')
    source_file_path = pathlib.Path(mp4_file).resolve()

    if not source_file_path.exists() or not source_file_path.is_file() or not source_file_path.suffix == ".mp4":
        error_dict = {"message": "Missing file", "file_name": mp4_file}
        raise FileNotFoundError(error_dict)

    remove_sub_clips = []
    for index, sub_clip in enumerate(sub_clips):
        try:
            sub_clip.set_cmd_metadata(source_file_path, media_output_parent_path, chr(ALPHANUMERIC_INDEX_A + index))
        except FileExistsError as e:
            error_dict = e.args[0]
            error_dict["line_index"] = index
            error_log.append(error_dict)
            print(error_log)
            remove_sub_clips.append(index)
    for index in remove_sub_clips:
        sub_clips.pop(index)


def update_processed_file(editor_metadata, editor_metadata_file):
    editor_metadata_content = {}
    editor_metadata_file_path = pathlib.Path(editor_metadata_file).resolve()
    try:
        editor_metadata_content = config_file_handler.load_json_file_content(editor_metadata_file_path)
    except (FileNotFoundError, JSONDecodeError):
        pass
    editor_metadata_content[editor_metadata.get('txt_file_name')] = {"processed": True}
    config_file_handler.save_json_file_content(editor_metadata_content, editor_metadata_file)


def editor_validate_txt_file(editor_raw_folder, editor_metadata):
    txt_file_name = f"{editor_raw_folder}{editor_metadata.get('txt_file_name')}"
    try:
        return get_sub_clips_from_txt_file(txt_file_name)
    except ValueError as e:
        raise ValueError(e.args[0]) from e
    except FileNotFoundError as e:
        raise FileNotFoundError(e.args[0]) from e


def editor_process_txt_file(editor_metadata_file, editor_raw_folder, editor_metadata, media_output_parent_path,
                            editor_processor):
    sub_clip_file = f"{editor_raw_folder}{editor_metadata.get('txt_file_name')}"
    if editor_metadata.get('txt_file_content'):
        config_file_handler.save_txt_file_content(sub_clip_file, editor_metadata.get('txt_file_content'))

    try:
        sub_clips, errors = editor_validate_txt_file(editor_raw_folder, editor_metadata)
        get_cmd_list(sub_clips, sub_clip_file, media_output_parent_path, errors)
        editor_processor.add_cmds_to_queue(editor_metadata_file, sub_clips)
        update_processed_file(editor_metadata, editor_metadata_file)
        return errors
    except ValueError as e:
        raise ValueError(e.args[0]) from e
    except FileNotFoundError as e:
        raise FileNotFoundError(e.args[0]) from e
    except FileExistsError as e:
        update_processed_file(editor_metadata, editor_metadata_file)
        error_dict = e.args[0]
        error_dict["txt_file_name"] = editor_metadata.get('txt_file_name')
        raise FileExistsError(error_dict) from e


def get_editor_txt_files(editor_raw_folder):
    raw_path = pathlib.Path(editor_raw_folder).resolve()
    editor_txt_files = []
    for editor_mp4_file in list(sorted(raw_path.rglob(mp4_file_ext))):
        if "old" not in editor_mp4_file.parts:
            editor_txt_file_path = pathlib.Path(str(editor_mp4_file).replace("mp4", "txt")).resolve()
            editor_txt_file_path.touch()
            editor_txt_files.append(editor_txt_file_path)
    return editor_txt_files


def editor_save_txt_file(output_path, editor_metadata):
    config_file_handler.save_txt_file_content(txt_file_path=f"{output_path}{editor_metadata.get('txt_file_name')}",
                                              txt_file_content=editor_metadata.get('txt_file_content'))


def check_editor_txt_file_processed(editor_metadata_file, editor_txt_file_names):
    editor_txt_file_processed = []
    metadata_file = pathlib.Path(editor_metadata_file).resolve()
    metadata_file_content = config_file_handler.load_json_file_content(metadata_file)
    for editor_txt_file in editor_txt_file_names:
        if editor_txt_file in metadata_file_content:
            editor_txt_file_processed.append({
                "file_name": editor_txt_file,
                "processed": metadata_file_content.get(editor_txt_file).get("processed")
            })
        else:
            editor_txt_file_processed.append({
                "file_name": editor_txt_file,
                "processed": False
            })
    return editor_txt_file_processed


def get_editor_metadata(editor_metadata_file, editor_raw_folder, editor_processor, selected_txt_file=None):
    selected_index = 0
    editor_metadata = {}
    editor_txt_files = get_editor_txt_files(editor_raw_folder)
    editor_txt_file_names = [editor_txt_file.as_posix().replace(editor_raw_folder, "") for editor_txt_file in
                             editor_txt_files]

    if editor_txt_file_names:
        if not selected_txt_file or selected_txt_file not in editor_txt_file_names:
            selected_txt_file = editor_txt_file_names[selected_index]

        selected_txt_file_path = pathlib.Path(f"{editor_raw_folder}{selected_txt_file}").resolve()

        editor_metadata = {
            "txt_file_list": check_editor_txt_file_processed(editor_metadata_file, editor_txt_file_names),
            "selected_txt_file_title": selected_txt_file,
            "selected_txt_file_content": ''.join(config_file_handler.load_txt_file_content(selected_txt_file_path)),
            "editor_process_metadata": editor_processor.get_metadata()
        }

    return editor_metadata


def extract_subclip(sub_clip):
    full_cmd = ['ffmpeg',
                '-ss', str(sub_clip.start_time),
                '-to', str(sub_clip.end_time),
                '-i', sub_clip.source_file_path,
                '-filter:a', 'asetpts=PTS-STARTPTS',
                '-filter:v', 'setpts=PTS-STARTPTS',
                '-c:a', 'aac',
                '-metadata', f"title={sub_clip.media_title}",
                sub_clip.destination_file_path]
    output_dir = pathlib.Path(sub_clip.destination_file_path).resolve().parent
    # time.sleep(1)
    # print(cmd)
    print(output_dir)
    print(full_cmd)
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(full_cmd, check=True, text=True)


class CmdData:
    metadata_file_path = ""
    cmd = None

    def __init__(self, metadata_file_path, cmd):
        self.metadata_file_path = metadata_file_path
        self.cmd = cmd


class SubclipProcessHandler(threading.Thread):
    subclip_process_queue_size = 30
    subclip_process_queue = queue.Queue()
    log_queue = queue.Queue()
    current_cmd = None
    process_start = 0

    def run(self):
        while not self.subclip_process_queue.empty():
            self.process_start = datetime.now()
            current_cmd = self.subclip_process_queue.get()
            self.current_cmd = current_cmd.cmd
            try:
                extract_subclip(self.current_cmd)
                self.log_queue.put(
                    {"message": "Finished splitting", "file_name": self.current_cmd.destination_file_path})
            except subprocess.CalledProcessError:
                self.log_queue.put(
                    {"message": "Error encountered while splitting",
                     "file_name": self.current_cmd.destination_file_path})

        self.current_cmd = None

    def add_cmds_to_queue(self, metadata_file_path, sub_clips):
        if self.subclip_process_queue.qsize() > self.subclip_process_queue_size:
            raise JobQueueFull({"message": "Job queue full"})
        for cmd in sub_clips:
            self.subclip_process_queue.put(CmdData(metadata_file_path, cmd))
        if not self.is_alive():
            threading.Thread.__init__(self, daemon=True)
            self.start()

    def get_metadata(self):
        process_name = "Split queue empty"
        process_time = "0"
        process_log = []
        if self.current_cmd:
            process_name = f"{self.current_cmd.media_title}, {self.current_cmd.file_name}"
            process_time = str(datetime.now() - self.process_start)

        while not self.log_queue.empty():
            process_log.append(self.log_queue.get())

        return {
            "process_name": process_name,
            "process_time": process_time,
            "process_queue_size": self.subclip_process_queue.qsize(),
            "process_log": process_log
        }
