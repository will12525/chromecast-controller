import hashlib
import time
import random
import pathlib
from unittest.mock import patch
import os

# import app.utils.common

# import app.utils.common
from app.utils import config_file_handler

# from app.utils import common

example_config_file = {
    "mode": "SERVER",
    "editor_raw_folder": "/media/raw_files/",
    "editor_raw_url": "http://localhost:8001/",
    "server_url": "http://localhost:5001/",
    "media_folders": [
        {
            "content_src": "/media/library/",
            "content_url": "http://localhost:8000"
        },
        {
            "content_src": "/media/library_2/",
            "content_url": "http://localhost:8001"
        }
    ]
}


def get_file_hash(extra_metadata):
    time_hash = hashlib.md5()
    time_hash.update(str(time.time() + random.randint(1000, 1000000)).encode("utf-8"))
    extra_metadata['md5sum'] = time_hash.hexdigest()


def get_ffmpeg_metadata(path, extra_metadata):
    assert os.path.exists(path)
    extra_metadata["content_duration"] = 22
    extra_metadata["content_title"] = "Test Tile"


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
    destination_file = pathlib.Path(sub_clip.destination_file_path).resolve()
    # output_dir = pathlib.Path(sub_clip.destination_file_path).resolve().parent
    # time.sleep(sub_clip.start_time + sub_clip.end_time)
    time.sleep(.1)
    return {"message": "Finished splitting", "value": sub_clip.destination_file_path}


def patch_get_file_hash(test_class):
    patcher = patch('app.database.media_metadata_collector.get_file_hash')
    test_class.get_file_hash = patcher.start()
    test_class.get_file_hash.side_effect = get_file_hash
    test_class.addCleanup(patcher.stop)


def patch_get_ffmpeg_metadata(test_class):
    patcher = patch('app.database.media_metadata_collector.get_ffmpeg_metadata')
    test_class.get_ffmpeg_metadata = patcher.start()
    test_class.get_ffmpeg_metadata.side_effect = get_ffmpeg_metadata
    test_class.addCleanup(patcher.stop)


def patch_extract_subclip(test_class):
    patcher = patch('app.utils.mp4_splitter.extract_subclip')
    test_class.extract_subclip = patcher.start()
    test_class.extract_subclip.side_effect = extract_subclip
    test_class.addCleanup(patcher.stop)


def patch_get_free_disk_space(test_class):
    patcher = patch('app.utils.common.get_free_disk_space')
    test_class.get_free_disk_space = patcher.start()
    test_class.get_free_disk_space.return_value = 100
    test_class.addCleanup(patcher.stop)


def patch_update_processed_file(test_class):
    patcher = patch('app.utils.mp4_splitter.update_processed_file')
    test_class.patch_update_processed_file = patcher.start()
    test_class.addCleanup(patcher.stop)
