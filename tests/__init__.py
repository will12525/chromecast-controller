import hashlib
import time
import random
import pathlib
from unittest.mock import patch

import config_file_handler
from database_handler import common_objects


def get_file_hash(extra_metadata):
    time_hash = hashlib.md5()
    time_hash.update(str(time.time() + random.randint(1000, 1000000)).encode("utf-8"))
    extra_metadata[common_objects.MD5SUM_COLUMN] = time_hash.hexdigest()


def get_ffmpeg_metadata(extra_metadata):
    extra_metadata[common_objects.DURATION_COLUMN] = 22
    extra_metadata[common_objects.MEDIA_TITLE_COLUMN] = ""


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
    print(output_dir)
    print(full_cmd)
    # time.sleep(sub_clip.start_time + sub_clip.end_time)
    time.sleep(2)


def patch_get_file_hash(test_class):
    patcher = patch('database_handler.media_metadata_collector.get_file_hash')
    test_class.get_file_hash = patcher.start()
    test_class.get_file_hash.side_effect = get_file_hash
    test_class.addCleanup(patcher.stop)


def patch_get_ffmpeg_metadata(test_class):
    patcher = patch('database_handler.media_metadata_collector.get_ffmpeg_metadata')
    test_class.get_ffmpeg_metadata = patcher.start()
    test_class.get_ffmpeg_metadata.side_effect = get_ffmpeg_metadata
    test_class.addCleanup(patcher.stop)


def patch_move_media_file(test_class):
    patcher = patch('database_handler.media_metadata_collector.move_media_file')
    test_class.move_media_file = patcher.start()
    test_class.addCleanup(patcher.stop)


def patch_extract_subclip(test_class):
    patcher = patch('mp4_splitter.extract_subclip')
    test_class.extract_subclip = patcher.start()
    test_class.extract_subclip.side_effect = extract_subclip
    test_class.addCleanup(patcher.stop)


def patch_collect_tv_shows(test_class):
    collect_tv_shows_metadata = config_file_handler.load_js_file("collect_tv_shows_metadata.json")

    patcher = patch('database_handler.media_metadata_collector.collect_tv_shows')
    test_class.collect_tv_shows = patcher.start()
    test_class.collect_tv_shows.return_value = collect_tv_shows_metadata
    test_class.addCleanup(patcher.stop)


def patch_collect_movies(test_class):
    collect_movies_metadata = config_file_handler.load_js_file("collect_movies_metadata.json")

    patcher = patch('database_handler.media_metadata_collector.collect_movies')
    test_class.collect_movies = patcher.start()
    test_class.collect_movies.return_value = collect_movies_metadata
    test_class.addCleanup(patcher.stop)
