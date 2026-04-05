import queue
import pathlib
import subprocess
import threading
import re
from json import JSONDecodeError
from datetime import datetime, timedelta
from pathvalidate import ValidationError, validate_filename

from app.utils import config_file_handler
from app.utils.common import ContentType
from app.database.media_metadata_collector import mp4_file_ext
from app.database.db_getter import DBHandler

"""
Convert to .exe

venv/Scripts/activate
pyinstaller mp4_splitter.py
pyinstaller --onefile --paths .\\venv\\Lib\\site-packages mp4_splitter.py
scp .\\dist\\mp4_splitter.exe willow@192.168.1.200:/home/willow/workspace/mp4_splitter/

On GAIA:
scp willow@192.168.1.200:/home/willow/workspace/mp4_splitter/mp4_splitter.exe .\\Desktop\\
"""

ALPHANUMERIC_INDEX_A = 97


class JobQueueFull(ValueError):
    pass


class EmptyTextFile(ValueError):
    pass


def check_valid_file(file_path, ext):
    if not file_path.exists() or not file_path.is_file() or not file_path.suffix == ext:
        return {"message": "Missing file", "value": str(file_path.name)}
    return {}


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


def check_content_already_exists(file_name):
    with DBHandler() as db_connection:
        for media_directory in db_connection.get_all_content_directory_info():
            return pathlib.Path(f"{media_directory.get('content_src')}/{file_name}").exists()


class SubclipMetadata:
    subclip_metadata = None
    media_title = None
    start_time = None
    end_time = None
    destination_file_path = None
    source_file_path = None
    file_name = None
    error_log = None
    overwrite = False

    def __init__(self, subclip_metadata, source_file_path=None, destination_dir_path=None, media_title=None):
        self.error_log = []
        self.subclip_metadata = subclip_metadata
        self.extract_start_end_times(self.subclip_metadata.get("start_time"), self.subclip_metadata.get("end_time"))
        if self.subclip_metadata.get("overwrite"):
            self.overwrite = True

    def set_cmd_metadata(self, source_file_path, destination_file_path):
        if destination_file_path.exists() and not self.overwrite:
            self.error_log.append({"message": "File already exists", "value": destination_file_path.name})
        else:
            self.file_name = source_file_path.stem.strip()
            self.source_file_path = str(source_file_path.as_posix()).strip()
            self.destination_file_path = str(destination_file_path.as_posix()).strip()

    def extract_int(self, extraction_int, extraction_err_msg):
        extracted_int = None
        if extraction_int is not None:
            try:
                extracted_int = int(extraction_int)
                if extracted_int < 0:
                    self.error_log.append({"message": "Values less than 0", extraction_err_msg: extraction_int})
            except ValueError:
                self.error_log.append({"message": "Values not int", extraction_err_msg: extraction_int})
        return extracted_int

    def extract_str(self, extraction_str, extraction_err_msg):
        extracted_str = None
        if type(extraction_str) is not str:
            self.error_log.append({"message": f"{extraction_err_msg} is not str", extraction_err_msg: extraction_str})
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
                self.error_log.append(error_dict)
        return extracted_str

    def extract_start_end_times(self, start_time, end_time):
        if start_time and end_time:
            start_time = convert_timestamp(start_time, self.error_log)
            end_time = convert_timestamp(end_time, self.error_log)
            if end_time <= start_time:
                self.error_log.append({"message": "End time >= start time"})
            self.start_time = start_time
            self.end_time = end_time
        else:
            self.error_log.append({"message": "Missing start or end time"})

    def extract_media_title(self, media_title):
        if media_title := self.extract_str(media_title, "media_title"):
            self.media_title = media_title
        else:
            self.error_log.append({"message": "Missing media title"})

    def __str__(self):
        return str({"media_title": self.media_title, "start_time": self.start_time, "end_time": self.end_time})


class MovieSubclipMetadata(SubclipMetadata):
    year = None

    def __init__(self, subclip_metadata, source_file_path, destination_dir_path, media_title=None):
        super().__init__(subclip_metadata)
        if len(self.subclip_metadata) == 5:
            self.extract_media_title(self.subclip_metadata.get("media_title"))
            self.year = self.extract_int(self.subclip_metadata.get("year"), "year")
        else:
            self.error_log.append({"message": "Missing content", "value": subclip_metadata})

        if source_file_path and destination_dir_path:
            self.set_cmd_metadata(source_file_path, destination_dir_path)

        if self.error_log:
            self.error_log.append({"message": f"Errors occurred while parsing line", "value": subclip_metadata})

    def set_cmd_metadata(self, source_file_path, destination_dir_path):
        file_name = f"{self.media_title} ({self.year}).mp4"
        if check_content_already_exists(file_name):
            self.error_log.append({"message": "File already exists", "value": file_name})

        destination_file_path = destination_dir_path / file_name
        super().set_cmd_metadata(source_file_path, destination_file_path)

    def __str__(self):
        print_obj = {"media_title": self.media_title, "year": self.year,
                     "start_time": self.start_time, "end_time": self.end_time}
        return str(print_obj)


class RawSubclipMetadata(SubclipMetadata):

    def __init__(self, subclip_metadata, source_file_path, destination_dir_path, media_title=None):
        super().__init__(subclip_metadata)
        if len(self.subclip_metadata) == 3:
            self.media_title = media_title
        else:
            self.error_log.append({"message": "Missing content", "value": subclip_metadata})

        if source_file_path:
            self.set_cmd_metadata(source_file_path, destination_dir_path)

        if self.error_log:
            self.error_log.append({"message": f"Errors occurred while parsing line", "value": subclip_metadata})

    def set_cmd_metadata(self, source_file_path, destination_dir_path=None):
        file_name = f'{self.media_title}_{source_file_path.stem}.mp4'
        destination_file_path = source_file_path.parent / file_name
        if check_content_already_exists(destination_file_path):
            self.error_log.append({"message": "File already exists", "value": file_name})

        super().set_cmd_metadata(source_file_path, destination_file_path)


class BookSubclipMetadata(SubclipMetadata):
    author = ""

    def __init__(self, subclip_metadata, source_file_path, destination_dir_path, media_title=None):
        super().__init__(subclip_metadata)
        if len(self.subclip_metadata) == 5:
            self.extract_media_title(self.subclip_metadata.get("media_title"))
            self.author = self.extract_str(self.subclip_metadata.get("author"), "author")
        else:
            self.error_log.append({"message": "Missing content", "value": subclip_metadata})

        if source_file_path and destination_dir_path:
            self.set_cmd_metadata(source_file_path, destination_dir_path)

        if self.error_log:
            self.error_log.append({"message": f"Errors occurred while parsing line", "value": subclip_metadata})

    def set_cmd_metadata(self, source_file_path, destination_dir_path):
        file_name = f"{self.media_title} - {self.author}.mp4"
        if check_content_already_exists(file_name):
            self.error_log.append({"message": "File already exists", "value": file_name})

        destination_file_path = destination_dir_path / file_name
        super().set_cmd_metadata(source_file_path, destination_file_path)

    def __str__(self):
        print_obj = {"media_title": self.media_title, "author": self.author,
                     "start_time": self.start_time, "end_time": self.end_time}
        return str(print_obj)


class TvShowSubclipMetadata(SubclipMetadata):
    playlist_title = ""
    season_index = None
    episode_index = None

    def __init__(self, subclip_metadata, source_file_path, destination_dir_path, media_title=None):
        super().__init__(subclip_metadata)
        if len(self.subclip_metadata) == 7:
            self.extract_playlist_title(self.subclip_metadata.get("playlist_title"))
            self.extract_media_title(self.subclip_metadata.get("media_title"))
            self.extract_season_index(self.subclip_metadata.get("season_index"))
            self.extract_episode_index(self.subclip_metadata.get("episode_index"))
        else:
            self.error_log.append({"message": "Missing content", "value": subclip_metadata})
        if source_file_path and destination_dir_path:
            self.set_cmd_metadata(source_file_path, destination_dir_path)

        if self.error_log:
            self.error_log.append({"message": f"Errors occurred while parsing line", "value": subclip_metadata})

    def set_cmd_metadata(self, source_file_path, destination_dir_path):
        file_name = f'{self.playlist_title}/{self.playlist_title} - s{self.season_index}e{self.episode_index}.mp4'
        if check_content_already_exists(file_name):
            self.error_log.append({"message": "File already exists", "value": file_name})

        destination_file_path = destination_dir_path / file_name
        super().set_cmd_metadata(source_file_path, destination_file_path)

    def extract_playlist_title(self, playlist_title):
        if playlist_title := self.extract_str(playlist_title, "playlist_title"):
            self.playlist_title = playlist_title
        else:
            self.error_log.append({"message": "Missing playlist title"})

    def extract_season_index(self, season_index):
        if season_index := self.extract_int(season_index, "season_index"):
            self.season_index = season_index
        else:
            self.error_log.append({"message": "Missing season index"})

    def extract_episode_index(self, episode_index):
        episode_index = self.extract_int(episode_index, "episode_index")
        if episode_index is not None:
            self.episode_index = episode_index
        else:
            self.error_log.append({"message": "Missing episode index"})

    def __str__(self):
        print_obj = {"playlist_title": self.playlist_title, "media_title": self.media_title,
                     "season_index": self.season_index, "episode_index": self.episode_index,
                     "start_time": self.start_time, "end_time": self.end_time}
        return str(print_obj)


def convert_txt_to_sub_clip(media_type, splitter_content, error_log, source_file_path, destination_dir_path,
                            media_title):
    if media_type == ContentType.RAW.name:
        return RawSubclipMetadata(splitter_content, source_file_path, destination_dir_path, media_title)
    elif media_type == ContentType.TV.name:
        return TvShowSubclipMetadata(splitter_content, source_file_path, destination_dir_path)
    elif media_type == ContentType.MOVIE.name:
        return MovieSubclipMetadata(splitter_content, source_file_path, destination_dir_path)
    elif media_type == ContentType.BOOK.name:
        return BookSubclipMetadata(splitter_content, source_file_path, destination_dir_path)
    else:
        error_log.append({"message": "Unsupported content type", "value": media_type})


def get_sub_clips_from_txt_file(file_path, destination_dir_path, sub_clips, error_log):
    file_content = {}
    source_file_path = file_path.with_suffix(".mp4")

    if error := check_valid_file(file_path, ".json"):
        error_log.append(error)
    else:
        file_content = config_file_handler.load_json_file_content(file_path)
    if error := check_valid_file(source_file_path, ".mp4"):
        error_log.append(error)

    if file_content and file_content.get("splitter_content"):
        for index, splitter_content in enumerate(file_content.get("splitter_content")):
            if playlist_title := file_content.get("playlist_title"):
                splitter_content["playlist_title"] = playlist_title
            if sub_clip := convert_txt_to_sub_clip(file_content.get("media_type"), splitter_content, error_log,
                                                   source_file_path, destination_dir_path,
                                                   chr(ALPHANUMERIC_INDEX_A + index)):
                if sub_clip.error_log:
                    error_log.extend(sub_clip.error_log)
                    sub_clip.error_log.append({"message": "Failing line index", "value": index})
                sub_clips.append(sub_clip)
    else:
        error_log.append({"message": "Text file empty", "value": file_path.name})


def editor_process_media_file(file_name, destination_dir_path, editor_thread):
    error_log = []
    sub_clips = []
    raw_folder = config_file_handler.load_json_file_content().get('editor_raw_folder')

    txt_file = f"{raw_folder}{file_name}"
    txt_file_path = pathlib.Path(txt_file).resolve()

    get_sub_clips_from_txt_file(txt_file_path, destination_dir_path, sub_clips, error_log)

    if editor_thread:
        editor_thread.add_cmds_to_queue(sub_clips, error_log)

    if error_log:
        error_log.append(
            {"message": "Errors occurred while processing file", "value": file_name})

    return error_log


def update_processed_file(txt_file_name, editor_processed_log):
    editor_metadata_content = {}
    raw_folder = config_file_handler.load_json_file_content().get('editor_raw_folder')
    editor_metadata_file = f"{raw_folder}{editor_processed_log}"
    editor_metadata_file_path = pathlib.Path(editor_metadata_file).resolve()
    try:
        editor_metadata_content = config_file_handler.load_json_file_content(editor_metadata_file_path)
    except (FileNotFoundError, JSONDecodeError) as e:
        print("update_processed_file: output")
        print(e.stdout)
        print("update_processed_file: err")
        print(e.stderr)
    editor_metadata_content[txt_file_name] = {"processed": True}
    config_file_handler.save_json_file_content(editor_metadata_file_path, editor_metadata_content)


def editor_validate_txt_file(file_name, destination_dir_path):
    error_log = []
    sub_clips = []
    raw_folder = config_file_handler.load_json_file_content().get('editor_raw_folder')
    file_sub_path = f"{raw_folder}{file_name}"
    file_path = pathlib.Path(file_sub_path).resolve()

    get_sub_clips_from_txt_file(file_path, destination_dir_path, sub_clips, error_log)

    return error_log


def get_editor_files(editor_raw_folder):
    raw_path = pathlib.Path(editor_raw_folder).resolve()
    editor_files = []
    for editor_mp4_file in list(sorted(raw_path.rglob(mp4_file_ext))):
        if "old" not in editor_mp4_file.parts:
            editor_file_path = pathlib.Path(str(editor_mp4_file).replace("mp4", "json")).resolve()
            try:
                editor_file_path.touch()
                editor_files.append(editor_file_path)
            except PermissionError:
                print(f"ERROR: Failed to create text file: {editor_file_path}")
    return editor_files


def check_editor_file_processed(editor_metadata_file, editor_file_names):
    editor_txt_file_processed = []
    metadata_file = pathlib.Path(editor_metadata_file).resolve()
    metadata_file_content = config_file_handler.load_json_file_content(metadata_file)
    for editor_file in editor_file_names:
        if editor_file in metadata_file_content:
            editor_txt_file_processed.append({
                "file_name": editor_file,
                "processed": metadata_file_content.get(editor_file).get("processed")
            })
        else:
            editor_txt_file_processed.append({
                "file_name": editor_file,
                "processed": False
            })
    return editor_txt_file_processed


def get_editor_metadata(editor_raw_folder, editor_thread, selected_editor_file=None, raw_url=None,
                        process_file=None):
    selected_index = 0
    editor_metadata = {}
    local_play_url = ""
    editor_file_names = [editor_file.as_posix().replace(editor_raw_folder, "") for editor_file in
                         get_editor_files(editor_raw_folder)]

    if editor_file_names:
        if not selected_editor_file or selected_editor_file not in editor_file_names:
            selected_editor_file = editor_file_names[selected_index]

        selected_file_path = pathlib.Path(f"{editor_raw_folder}{selected_editor_file}").resolve()

        if raw_url:
            local_play_url = f"{raw_url}{selected_editor_file.replace('.json', '.mp4')}"

        editor_metadata = {
            "txt_file_list": check_editor_file_processed(f"{editor_raw_folder}{process_file}",
                                                         editor_file_names),
            "selected_txt_file_title": selected_editor_file,
            "selected_editor_file_content": config_file_handler.load_json_file_content(selected_file_path),
            "editor_process_metadata": editor_thread.get_metadata(),
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
                '-y',
                sub_clip.destination_file_path]
    if not sub_clip.destination_file_path:
        return {"message": "Missing destination path:", "value": f"{sub_clip.media_title}"}

    destination_file = pathlib.Path(sub_clip.destination_file_path).resolve()

    if destination_file.is_file() and not sub_clip.overwrite:
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


class SubclipThreadHandler(threading.Thread):
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
        if sub_clip.error_log:
            return False

        if not sub_clip.destination_file_path:
            self.log_queue.put({"message": "Missing destination path:", "value": f"{sub_clip.media_title}"})
            return False

        if pathlib.Path(sub_clip.destination_file_path).resolve().is_file() and not sub_clip.overwrite:
            self.log_queue.put(
                {"message": "Destination file already exists", "value": self.current_sub_clip.destination_file_path})
            return False

        for process_queue_sub_clip in list(self.subclip_process_queue.queue):
            if sub_clip.destination_file_path == process_queue_sub_clip.destination_file_path:
                self.log_queue.put(
                    {"message": "Destination path already in queue", "value": sub_clip.destination_file_path})
                return False
        return True

    def add_cmds_to_queue(self, sub_clips, error_log):
        if self.subclip_process_queue.qsize() > self.subclip_process_queue_size:
            error_log.append({"message": "Job queue full"})
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
            "process_end_time": process_end_time.strftime("%d %I:%M:%S %p"),
            "percent_complete": percent_complete,
            "process_queue_size": self.subclip_process_queue.qsize(),
            "process_log": process_log,
            "process_queue": process_queue
        }
