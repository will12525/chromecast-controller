import time
import queue
import pathlib
import subprocess
import threading
from json import JSONDecodeError

from datetime import datetime, timedelta
import re
from pathvalidate import ValidationError, validate_filename

import config_file_handler
from database_handler.common_objects import ContentType
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

EDITOR_PROCESSED_LOG = "editor_metadata.json"


class JobQueueFull(ValueError):
    pass


class EmptyTextFile(ValueError):
    pass


def convert_timestamp(timestamp_str, error_list):
    str_failure_modes = ['', None]
    colon_count = timestamp_str.count(":")
    h = m = s = 0
    if colon_count == 0:
        (s,) = timestamp_str.split(':')
    elif colon_count == 1:
        m, s = timestamp_str.split(':')
    elif colon_count == 2:
        h, m, s = timestamp_str.split(':')
    else:
        error_list.append({"message": "Too many colons found", "value": timestamp_str, "colon_count": colon_count})

    if h in str_failure_modes or m in str_failure_modes or s in str_failure_modes:
        error_list.append(
            {"message": "Missing timestamp value", "value": timestamp_str, "hour": h, "minute": m, "second": s})
    else:
        try:
            h = int(h)
            m = int(m)
            s = int(s)

            if h < 0 or m < 0 or s < 0:
                error_list.append(
                    {"message": "Values less than 0", "value": timestamp_str, "hour": h, "minute": m, "second": s})
            else:
                return h * 3600 + m * 60 + s
        except ValueError:
            error_list.append(
                {"message": "Values not int", "value": timestamp_str, "hour": h, "minute": m, "second": s})
    return 0


class SubclipMetadata:
    subclip_metadata_list = None
    media_title = None
    start_time = None
    end_time = None
    destination_file_path = None
    source_file_path = None
    file_name = None
    error_list = None

    def __init__(self, subclip_metadata):
        self.error_list = []
        self.subclip_metadata_list = subclip_metadata.split(',')

    def extract_int(self, extraction_int, extraction_err_msg):
        extracted_int = None
        try:
            extracted_int = int(extraction_int)
            if extracted_int < 0:
                self.error_list.append({"message": "Values less than 0", extraction_err_msg: extraction_int})
        except ValueError:
            self.error_list.append({"message": "Values not int", extraction_err_msg: extraction_int})
        return extracted_int

    def extract_str(self, extraction_str, extraction_err_msg):
        extracted_str = None
        if type(extraction_str) is not str:
            self.error_list.append({"message": f"{extraction_err_msg} is not str", extraction_err_msg: extraction_str})
        else:
            try:
                extracted_str = extraction_str.strip().replace('"', "").replace(':', "")
                validate_filename(extracted_str, platform="Linux")
            except ValidationError as e:
                error_dict = {
                    "message": f"{extraction_err_msg} {e.reason.description}", extraction_err_msg: extraction_str}
                if len(e.args) > 0 and "invalids" in e.args[0]:
                    error_dict["invalids"] = re.search(
                        r'invalids=(.*?), value=', e.args[0]).group(1).replace("'", "")
                self.error_list.append(error_dict)
        return extracted_str

    def extract_start_end_times(self, start_time, end_time):
        if start_time and end_time:
            start_time = convert_timestamp(start_time, self.error_list)
            end_time = convert_timestamp(end_time, self.error_list)
            if end_time <= start_time:
                self.error_list.append({"message": "End time >= start time"})
            self.start_time = start_time
            self.end_time = end_time
        else:
            self.error_list.append({"message": "Missing start or end time"})

    def extract_media_title(self, media_title):
        if media_title := self.extract_str(media_title, "media_title"):
            self.media_title = media_title
        else:
            self.error_list.append({"message": "Missing media title"})


class MovieSubclipMetadata(SubclipMetadata):

    def __init__(self, subclip_metadata):
        super().__init__(subclip_metadata)
        if len(self.subclip_metadata_list) == 3:
            self.extract_media_title(self.subclip_metadata_list[0])
            self.extract_start_end_times(self.subclip_metadata_list[1], self.subclip_metadata_list[2])
        else:
            self.error_list.append({"message": "Missing content", "value": subclip_metadata})

        if self.error_list:
            self.error_list.append({"message": f"Errors occurred while parsing line", "value": subclip_metadata})

    def set_cmd_metadata(self, source_file_path, destination_file_path, media_title):
        if not destination_file_path or not self.media_title:
            destination_file_path = source_file_path.parent

        if self.media_title:
            destination_file_path = destination_file_path / f"{self.media_title}.mp4"

        if destination_file_path.exists():
            self.error_list.append({"message": "File already exists", "value": destination_file_path.name})
        else:
            if not self.media_title:
                self.media_title = media_title
            self.file_name = source_file_path.stem.strip()
            self.source_file_path = str(source_file_path.as_posix()).strip()
            self.destination_file_path = str(destination_file_path.as_posix()).strip()


class TvShowSubclipMetadata(SubclipMetadata):
    playlist_title = ""
    season_index = None
    episode_index = None

    def __init__(self, subclip_metadata):
        super().__init__(subclip_metadata)

        if len(self.subclip_metadata_list) == 2:
            self.extract_start_end_times(self.subclip_metadata_list[0], self.subclip_metadata_list[1])
        elif len(self.subclip_metadata_list) == 6:
            self.extract_playlist_title(self.subclip_metadata_list[0])
            self.extract_media_title(self.subclip_metadata_list[1])
            self.extract_season_index(self.subclip_metadata_list[2])
            self.extract_episode_index(self.subclip_metadata_list[3])
            self.extract_start_end_times(self.subclip_metadata_list[4], self.subclip_metadata_list[5])
        else:
            self.error_list.append({"message": "Missing content", "value": subclip_metadata})

        if self.error_list:
            self.error_list.append({"message": f"Errors occurred while parsing line", "value": subclip_metadata})

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
            self.error_list.append({"message": "File already exists", "value": destination_file_path.name})
        else:
            if not self.media_title:
                self.media_title = media_title

            self.file_name = source_file_path.stem.strip()
            self.source_file_path = str(source_file_path.as_posix()).strip()
            self.destination_file_path = str(destination_file_path.as_posix()).strip()

    def extract_playlist_title(self, playlist_title):
        if playlist_title := self.extract_str(playlist_title, "playlist_title"):
            self.playlist_title = playlist_title
        else:
            self.error_list.append({"message": "Missing playlist title"})

    def extract_season_index(self, season_index):
        if season_index := self.extract_int(season_index, "season_index"):
            self.season_index = season_index
        else:
            self.error_list.append({"message": "Missing season index"})

    def extract_episode_index(self, episode_index):
        if episode_index := self.extract_int(episode_index, "episode_index"):
            self.episode_index = episode_index
        else:
            self.error_list.append({"message": "Missing episode index"})


def get_tv_sub_clips_as_objs(txt_file_content, error_log):
    sub_clips = []
    for index, file_text in enumerate(txt_file_content):
        sub_clip = TvShowSubclipMetadata(file_text)
        if sub_clip.error_list:
            error_log.append({"message": "Failing line index", "value": index})
            error_log.extend(sub_clip.error_list)
        else:
            sub_clips.append(sub_clip)
    return sub_clips


def get_movie_sub_clips_as_objs(txt_file_content, error_log):
    sub_clips = []
    for index, file_text in enumerate(txt_file_content):
        sub_clip = MovieSubclipMetadata(file_text)
        if sub_clip.error_list:
            error_log.append({"message": "Failing line index", "value": index})
            error_log.extend(sub_clip.error_list)
        else:
            sub_clips.append(sub_clip)
    return sub_clips


def get_sub_clips_from_txt_file(sub_clip_file, error_log, content_type):
    sub_clips = []
    sub_clip_file_path = pathlib.Path(sub_clip_file).resolve()
    if not sub_clip_file_path.exists() or not sub_clip_file_path.is_file() or not sub_clip_file_path.suffix == ".txt":
        error_log.append({"message": "Missing file", "value": sub_clip_file})
    else:
        subclip_file_content = config_file_handler.load_txt_file_content(sub_clip_file_path)
        if not subclip_file_content:
            error_log.append({"message": "Text file empty", "value": sub_clip_file_path.name})
        else:
            if content_type == ContentType.TV.value:
                sub_clips = get_tv_sub_clips_as_objs(subclip_file_content, error_log)
            elif content_type == ContentType.MOVIE.value:
                sub_clips = get_movie_sub_clips_as_objs(subclip_file_content, error_log)
            else:
                error_log.append({"message": "Unsupported content type", "value": content_type})
            if error_log:
                error_log.append({"message": "Broken text file", "value": sub_clip_file_path.name})
    return sub_clips


def get_cmd_list(sub_clips: list[TvShowSubclipMetadata], sub_clip_file, media_output_parent_path=None, error_log=None):
    if error_log is None:
        error_log = []

    mp4_file = sub_clip_file.replace('.txt', '.mp4')
    source_file_path = pathlib.Path(mp4_file).resolve()

    if not source_file_path.exists() or not source_file_path.is_file() or not source_file_path.suffix == ".mp4":
        error_log.append({"message": "Missing file", "value": source_file_path.stem})

    for index, sub_clip in enumerate(sub_clips):
        sub_clip.set_cmd_metadata(source_file_path, media_output_parent_path, chr(ALPHANUMERIC_INDEX_A + index))
        if sub_clip.error_list:
            error_log.append({"message": "Failing line index", "value": index})
            error_log.extend(sub_clip.error_list)


def update_processed_file(txt_file_name, editor_raw_folder):
    editor_metadata_content = {}
    editor_metadata_file = f"{editor_raw_folder}{EDITOR_PROCESSED_LOG}"
    editor_metadata_file_path = pathlib.Path(editor_metadata_file).resolve()
    try:
        editor_metadata_content = config_file_handler.load_json_file_content(editor_metadata_file_path)
    except (FileNotFoundError, JSONDecodeError) as e:
        print("update_processed_file: output")
        print(e.stdout)
        print("update_processed_file: err")
        print(e.stderr)
    editor_metadata_content[txt_file_name] = {"processed": True}
    config_file_handler.save_json_file_content(editor_metadata_content, editor_metadata_file)


def editor_validate_txt_file(editor_raw_folder, editor_metadata, error_log):
    txt_file = f"{editor_raw_folder}{editor_metadata.get('txt_file_name')}"
    return get_sub_clips_from_txt_file(txt_file, error_log, editor_metadata.get("media_type"))


def editor_process_txt_file(editor_raw_folder, editor_metadata, media_output_parent_path, editor_processor):
    error_log = []
    sub_clip_file = f"{editor_raw_folder}{editor_metadata.get('txt_file_name')}"
    if editor_metadata.get('txt_file_content'):
        config_file_handler.save_txt_file_content(sub_clip_file, editor_metadata.get('txt_file_content'))

    sub_clips = editor_validate_txt_file(editor_raw_folder, editor_metadata, error_log)
    get_cmd_list(sub_clips, sub_clip_file, media_output_parent_path, error_log)
    editor_processor.add_cmds_to_queue(sub_clips)
    if not error_log:
        update_processed_file(editor_metadata.get('txt_file_name'), editor_raw_folder)

    if error_log:
        error_log.append(
            {"message": "Errors occurred while processing file", "value": editor_metadata.get('txt_file_name')})
    return error_log


def get_editor_txt_files(editor_raw_folder):
    raw_path = pathlib.Path(editor_raw_folder).resolve()
    editor_txt_files = []
    for editor_mp4_file in list(sorted(raw_path.rglob(mp4_file_ext))):
        if "old" not in editor_mp4_file.parts:
            editor_txt_file_path = pathlib.Path(str(editor_mp4_file).replace("mp4", "txt")).resolve()
            try:
                editor_txt_file_path.touch()
                editor_txt_files.append(editor_txt_file_path)
            except PermissionError as e:
                print(f"ERROR: Failed to create text file: {editor_txt_file_path}")

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


def get_editor_metadata(editor_raw_folder, editor_processor, selected_txt_file=None, raw_url=None):
    selected_index = 0
    editor_metadata = {}
    local_play_url = ""
    editor_txt_files = get_editor_txt_files(editor_raw_folder)
    editor_txt_file_names = [editor_txt_file.as_posix().replace(editor_raw_folder, "") for editor_txt_file in
                             editor_txt_files]

    if editor_txt_file_names:
        if not selected_txt_file or selected_txt_file not in editor_txt_file_names:
            selected_txt_file = editor_txt_file_names[selected_index]

        selected_txt_file_path = pathlib.Path(f"{editor_raw_folder}{selected_txt_file}").resolve()

        if raw_url:
            local_play_url = f"{raw_url}{selected_txt_file.replace('.txt', '.mp4')}"

        editor_metadata = {
            "txt_file_list": check_editor_txt_file_processed(f"{editor_raw_folder}{EDITOR_PROCESSED_LOG}",
                                                             editor_txt_file_names),
            "selected_txt_file_title": selected_txt_file,
            "selected_txt_file_content": ''.join(config_file_handler.load_txt_file_content(selected_txt_file_path)),
            "editor_process_metadata": editor_processor.get_metadata(),
            "local_play_url": local_play_url
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
    if not sub_clip.destination_file_path:
        return {"message": "Missing destination path:", "value": f"{sub_clip.media_title}"}

    destination_file = pathlib.Path(sub_clip.destination_file_path).resolve()

    if destination_file.is_file():
        return {"message": "Media already exists:", "value": f"{sub_clip.media_title}, {sub_clip.file_name}"}

    output_dir = destination_file.parent
    # print(f"Sleeping {sub_clip.end_time}")
    # time.sleep(5)
    # print(cmd)
    print(output_dir)
    print(full_cmd)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(full_cmd, check=True, text=True, capture_output=True)
    print("INFO: Splitter extract_subclip")
    print(result.stdout)
    print(result.stderr)
    return {"message": "Finished splitting", "value": sub_clip.destination_file_path}


class SubclipProcessHandler(threading.Thread):
    subclip_process_queue_size = 30
    subclip_process_queue = queue.Queue()
    log_queue = queue.Queue()
    current_sub_clip = None
    process_start = 0

    def run(self):
        while not self.subclip_process_queue.empty():
            self.process_start = datetime.now()
            self.current_sub_clip = self.subclip_process_queue.get()
            try:
                self.log_queue.put(extract_subclip(self.current_sub_clip))
            except subprocess.CalledProcessError:
                self.log_queue.put({"message": "Error encountered while splitting",
                                    "value": self.current_sub_clip.destination_file_path})

        self.current_sub_clip = None

    def check_valid_sub_clip(self, sub_clip):
        if sub_clip.error_list:
            print({"message": "Has error list", "value": sub_clip.error_list})
            return False

        if not sub_clip.destination_file_path:
            print({"message": "Missing destination path:", "value": f"{sub_clip.media_title}"})
            return False

        if pathlib.Path(sub_clip.destination_file_path).resolve().is_file():
            print({"message": "Error is file", "value": self.current_sub_clip.destination_file_path})
            return False

        for process_queue_sub_clip in list(self.subclip_process_queue.queue):
            if sub_clip.destination_file_path == process_queue_sub_clip.destination_file_path:
                print({"message": "Destination path in queue", "value": sub_clip.destination_file_path})
                return False
        return True

    def add_cmds_to_queue(self, sub_clips):
        if self.subclip_process_queue.qsize() > self.subclip_process_queue_size:
            raise JobQueueFull({"message": "Job queue full"})
        for sub_clip in sub_clips:
            if self.check_valid_sub_clip(sub_clip):
                self.subclip_process_queue.put(sub_clip)
        if not self.is_alive():
            threading.Thread.__init__(self, daemon=True)
            self.start()

    def get_metadata(self):
        process_name = "Split queue empty"
        process_end_time = 0
        percent_complete = 0
        process_log = []
        process_queue = []
        if self.current_sub_clip:
            process_name = f"{self.current_sub_clip.media_title}, {self.current_sub_clip.file_name}"
            process_time = datetime.now() - self.process_start
            if self.current_sub_clip.end_time > 0:
                process_end_time += int(process_time.total_seconds()) - self.current_sub_clip.end_time
                percent_complete = int((int(process_time.total_seconds()) / self.current_sub_clip.end_time) * 100)

        while not self.log_queue.empty():
            process_log.append(self.log_queue.get())

        for sub_clip in list(self.subclip_process_queue.queue):
            process_queue.append(f"{sub_clip.media_title}, {sub_clip.file_name}")
            process_end_time += sub_clip.end_time

        process_end_time = datetime.now() + timedelta(seconds=process_end_time)

        return {
            "process_name": process_name,
            "process_end_time": process_end_time.strftime("%d %H:%M:%S"),
            "percent_complete": percent_complete,
            "process_queue_size": self.subclip_process_queue.qsize(),
            "process_log": process_log,
            "process_queue": process_queue
        }
