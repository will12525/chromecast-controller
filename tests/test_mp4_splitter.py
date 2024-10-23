import json
import pathlib
from unittest import TestCase
from . import pytest_mocks

import mp4_splitter
import config_file_handler
from database_handler.common_objects import ContentType

EDITOR_PROCESSED_LOG = "editor_metadata.json"


class TestMp4Splitter(TestCase):
    default_config = config_file_handler.load_json_file_content()
    raw_folder = default_config.get('editor_raw_folder')
    raw_url = default_config.get('editor_raw_url')
    modify_output_path = pathlib.Path(default_config.get("media_folders")[0].get("content_src")).resolve()
    editor_metadata_file = f"{raw_folder}editor_metadata.json"


class TestSplitterV2(TestMp4Splitter):
    def test_convert_raw_sub_clip(self):
        subclip_metadata = {"start_time": '1:20:47', "end_time": '1:40:43'}
        subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043

    def test_editor_validate_error_empty_json_file(self):
        file_name = "2024-01-31_16-32-36_empty.json"
        error_log = mp4_splitter.editor_validate_txt_file(file_name, self.raw_folder)
        assert len(error_log) == 1
        assert error_log[0].get("message") == "Text file empty"

    def test_convert_tv_raw_sub_clip(self):
        subclip_metadata = {"start_time": "1:20:47", "end_time": "1:40:43", "overwrite": False}
        subclip_metadata = mp4_splitter.RawSubclipMetadata(subclip_metadata, None, None)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043
        assert not subclip_metadata.error_log
        subclip_metadata = {"playlist_title": "Hilda", "media_title": "episode 1", "season_index": 2,
                            "episode_index": 1, "start_time": "1:20:47",
                            "end_time": "1:40:43", "overwrite": False}
        subclip_metadata = mp4_splitter.TvShowSubclipMetadata(subclip_metadata, None, None, None)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043
        assert subclip_metadata.episode_index == 1
        assert subclip_metadata.season_index == 2
        assert subclip_metadata.media_title == "episode 1"
        assert subclip_metadata.playlist_title == "Hilda"
        assert not subclip_metadata.error_log

    def test_convert_tv_sub_clip(self):
        subclip_metadata = {"playlist_title": "Hilda", "media_title": '"episode 1"', "season_index": 2,
                            "episode_index": 1, "start_time": "1:20:47",
                            "end_time": "1:40:43", "overwrite": False}
        subclip_metadata = mp4_splitter.TvShowSubclipMetadata(subclip_metadata, None, None, None)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043
        assert subclip_metadata.episode_index == 1
        assert subclip_metadata.season_index == 2
        assert subclip_metadata.media_title == "episode 1"
        assert subclip_metadata.playlist_title == "Hilda"
        assert not subclip_metadata.error_log

    def test_convert_tv_sub_clip_list(self):
        error_log = []
        subclip_metadata_list = [{"playlist_title": "Hilda", "media_title": "episode name", "season_index": 2,
                                  "episode_index": 1, "start_time": "7",
                                  "end_time": "13:43", "overwrite": False},
                                 {"playlist_title": "Hilda", "media_title": "episode another name", "season_index": 2,
                                  "episode_index": 1, "start_time": "13:49",
                                  "end_time": "29:33", "overwrite": False},
                                 {"playlist_title": "Hilda", "media_title": "episode name", "season_index": 2,
                                  "episode_index": 1, "start_time": "30:03",
                                  "end_time": "46:32", "overwrite": False},
                                 {"playlist_title": "Hilda", "media_title": "episode 2", "season_index": 2,
                                  "episode_index": 2, "start_time": "47:26",
                                  "end_time": "1:02:10", "overwrite": False},
                                 {"playlist_title": "Hilda", "media_title": "episode 1", "season_index": 2,
                                  "episode_index": 1, "start_time": "1:02:43",
                                  "end_time": "1:20:13", "overwrite": False}]
        for subclip_metadata in subclip_metadata_list:
            sub_clip = mp4_splitter.convert_txt_to_sub_clip(ContentType.TV.name, subclip_metadata, error_log,
                                                            None, None, None)
            assert sub_clip.subclip_metadata == subclip_metadata
            assert sub_clip.media_title == subclip_metadata.get("media_title")
            assert type(sub_clip.start_time) is int
            assert type(sub_clip.end_time) is int
            assert type(sub_clip.error_log) is list
            assert not sub_clip.overwrite
            assert len(sub_clip.error_log) == 0
            assert not sub_clip.destination_file_path
            assert not sub_clip.source_file_path
            assert not sub_clip.file_name

    def test_convert_raw_sub_clip_list(self):
        error_log = []
        subclip_metadata_list = [{"start_time": "7", "end_time": "13:43", "overwrite": False},
                                 {"start_time": "13:49", "end_time": "29:33", "overwrite": False},
                                 {"start_time": "30:03", "end_time": "46:32", "overwrite": False},
                                 {"start_time": "47:26", "end_time": "1:02:10", "overwrite": False},
                                 {"start_time": "1:02:43", "end_time": "1:20:13", "overwrite": False}]
        for subclip_metadata in subclip_metadata_list:
            sub_clip = mp4_splitter.convert_txt_to_sub_clip(ContentType.RAW.name, subclip_metadata, error_log,
                                                            None, None, None)
            assert sub_clip.subclip_metadata == subclip_metadata
            assert not sub_clip.media_title
            assert type(sub_clip.start_time) is int
            assert type(sub_clip.end_time) is int
            assert type(sub_clip.error_log) is list
            assert not sub_clip.overwrite
            assert len(sub_clip.error_log) == 0
            assert not sub_clip.destination_file_path
            assert not sub_clip.source_file_path
            assert not sub_clip.file_name

    def test_convert_raw_errors(self):
        error_log = []
        subclip_metadata = {"start_time": "7", "end_time": "13:43"}
        sub_clip = mp4_splitter.convert_txt_to_sub_clip(ContentType.RAW.name, subclip_metadata, error_log,
                                                        None, None, None)
        assert len(sub_clip.error_log) == 2
        assert sub_clip.error_log[0].get("message") == "Missing content"
        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"

    def test_load_txt_file_content(self):
        file_name = "2024-01-31_16-32-36.json"
        file_path = pathlib.Path(f"{self.raw_folder}{file_name}").resolve()
        assert file_path.exists()
        subclip_content = config_file_handler.load_json_file_content(file_path)
        assert subclip_content
        assert len(subclip_content.get("splitter_content")) == 5
        assert subclip_content.get("media_type") == ContentType.TV.name
        assert subclip_content.get("file_name")
        assert subclip_content.get("playlist_title")
        assert type(subclip_content.get("splitter_content")) is list
        for subclip in subclip_content.get("splitter_content"):
            assert type(subclip) is dict

    def test_validate_editor_cmd_list(self):
        error_log = []
        sub_clips = []
        file_name = "2024-01-31_16-32-36.json"
        file_path = pathlib.Path(f"{self.raw_folder}{file_name}").resolve()
        assert file_path.exists()
        assert self.modify_output_path.exists()
        mp4_splitter.get_sub_clips_from_txt_file(file_path, self.modify_output_path, sub_clips, error_log)
        assert 5 == len(sub_clips)
        assert not error_log

        for sub_clip in sub_clips:
            assert type(sub_clip) is mp4_splitter.TvShowSubclipMetadata
            assert type(sub_clip.playlist_title) is str
            assert type(sub_clip.media_title) is str
            assert type(sub_clip.file_name) is str
            assert type(sub_clip.source_file_path) is str
            assert str(self.modify_output_path.as_posix()) in sub_clip.source_file_path
            assert sub_clip.file_name == file_path.stem
            assert type(sub_clip.destination_file_path) is str
            assert self.modify_output_path.as_posix() in sub_clip.destination_file_path
            assert type(sub_clip.start_time) is int
            assert type(sub_clip.end_time) is int
            assert type(sub_clip.season_index) is int
            assert type(sub_clip.episode_index) is int
            assert sub_clip.source_file_path == f'{self.raw_folder}2024-01-31_16-32-36.mp4'


class TestSubclipMetadata(TestMp4Splitter):

    def test_invalid_timestamp_strings(self):
        invalid_end_minute_timestamp = {"start_time": "1:02:43", "end_time": "1:-20:13"}
        invalid_end_second_timestamp = {"start_time": "1:02:43", "end_time": "1:20:-13"}
        invalid_start_second_timestamp = {"start_time": "1:02:-43", "end_time": "1:20:13"}

        sub_clip = mp4_splitter.RawSubclipMetadata(invalid_end_minute_timestamp, None, None)
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("hour") == 1
        assert sub_clip.error_log[0].get("minute") == -20
        assert sub_clip.error_log[0].get("second") == 13

        sub_clip = mp4_splitter.RawSubclipMetadata(invalid_end_second_timestamp, None, None)
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("hour") == 1
        assert sub_clip.error_log[0].get("minute") == 20
        assert sub_clip.error_log[0].get("second") == -13

        sub_clip = mp4_splitter.RawSubclipMetadata(invalid_start_second_timestamp, None, None)
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("hour") == 1
        assert sub_clip.error_log[0].get("minute") == 2
        assert sub_clip.error_log[0].get("second") == -43

    def test_valid_full_data_strings(self):
        subclip_metadata = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                            "season_index": 2, "episode_index": 1,
                            "start_time": "7", "end_time": "13:43", "overwrite": False}
        subclip = mp4_splitter.TvShowSubclipMetadata(subclip_metadata, None, None, None)
        assert subclip.playlist_title == subclip_metadata.get("playlist_title")
        assert subclip.media_title == subclip_metadata.get("media_title")
        assert subclip.season_index == subclip_metadata.get("season_index")
        assert subclip.episode_index == subclip_metadata.get("episode_index")
        assert subclip.start_time == mp4_splitter.convert_timestamp(subclip_metadata.get("start_time"), [])
        assert subclip.end_time == mp4_splitter.convert_timestamp(subclip_metadata.get("end_time"), [])
        assert not subclip.overwrite

    def test_invalid_end_minute(self):
        invalid_negative_end_minute_timestamp = {"playlist_title": "Hilda", "media_title": "episode name",
                                                 "season_index": 2, "episode_index": 1,
                                                 "start_time": "1:02:43", "end_time": "1:-20:13", "overwrite": False}
        invalid_end_minute_is_str_timestamp = {"playlist_title": "Hilda", "media_title": "episode name",
                                               "season_index": 2, "episode_index": 1,
                                               "start_time": "1:02:43", "end_time": "1:HELLO:13", "overwrite": False}
        invalid_missing_end_minute_timestamp = {"playlist_title": "Hilda", "media_title": "episode name",
                                                "season_index": 2, "episode_index": 1,
                                                "start_time": "1:02:43", "end_time": "1::13", "overwrite": False}

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_negative_end_minute_timestamp, None, None, None)

        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict

        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("value") == "1:-20:13"
        assert sub_clip.error_log[0].get("hour") == 1
        assert sub_clip.error_log[0].get("minute") == -20
        assert sub_clip.error_log[0].get("second") == 13

        assert sub_clip.error_log[1].get("message") == "End time >= start time"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_negative_end_minute_timestamp

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_end_minute_is_str_timestamp, None, None, None)
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict

        assert sub_clip.error_log[0].get("message") == "Values not int"
        assert sub_clip.error_log[0].get("value") == "1:HELLO:13"
        assert sub_clip.error_log[0].get("hour") == 1
        assert sub_clip.error_log[0].get("minute") == "HELLO"
        assert sub_clip.error_log[0].get("second") == "13"

        assert sub_clip.error_log[1].get("message") == "End time >= start time"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_end_minute_is_str_timestamp

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_end_minute_timestamp, None, None, None)
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict

        assert sub_clip.error_log[0].get("message") == "Missing timestamp value"
        assert sub_clip.error_log[0].get("value") == "1::13"
        assert sub_clip.error_log[0].get("hour") == "1"
        assert sub_clip.error_log[0].get("minute") == ""
        assert sub_clip.error_log[0].get("second") == "13"

        assert sub_clip.error_log[1].get("message") == "End time >= start time"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_missing_end_minute_timestamp

    def test_invalid_start_second(self):
        invalid_negative_start_second_timestamp = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                                                   "season_index": 1, "episode_index": 1,
                                                   "start_time": "13:-49", "end_time": "29:33", "overwrite": False}
        invalid_start_second_is_str_timestamp = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                                                 "season_index": 1, "episode_index": 1,
                                                 "start_time": "13:HELLO", "end_time": "29:33", "overwrite": False}
        invalid_missing_start_second_timestamp = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                                                  "season_index": 1, "episode_index": 1,
                                                  "start_time": "13:", "end_time": "29:33", "overwrite": False}

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_negative_start_second_timestamp, None, None, None)
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("value") == "13:-49"
        assert sub_clip.error_log[0].get("hour") == 0
        assert sub_clip.error_log[0].get("minute") == 13
        assert sub_clip.error_log[0].get("second") == -49

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_start_second_is_str_timestamp, None, None, None)
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values not int"
        assert sub_clip.error_log[0].get("hour") == 0
        assert sub_clip.error_log[0].get("minute") == 13
        assert sub_clip.error_log[0].get("second") == "HELLO"

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_start_second_timestamp, None, None, None)
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Missing timestamp value"
        assert sub_clip.error_log[0].get("hour") == 0
        assert sub_clip.error_log[0].get("minute") == "13"
        assert sub_clip.error_log[0].get("second") == ""

    def test_invalid_episode_index(self):
        invalid_negative_episode_index = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                                          "season_index": 1, "episode_index": -1,
                                          "start_time": "30:03", "end_time": "46:32", "overwrite": False}
        invalid_episode_index_is_str = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                                        "season_index": 1, "episode_index": "HELLO",
                                        "start_time": "13:49", "end_time": "29:33", "overwrite": False}
        invalid_missing_episode_index = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                                         "season_index": 1, "episode_index": None,
                                         "start_time": "13:48", "end_time": "29:33", "overwrite": False}

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_negative_episode_index, None, None, None)
        assert len(sub_clip.error_log) == 2
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("episode_index") == -1

        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[1].get("value") == invalid_negative_episode_index

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_episode_index_is_str, None, None, None)
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values not int"
        assert sub_clip.error_log[0].get("episode_index") == "HELLO"

        assert sub_clip.error_log[1].get("message") == "Missing episode index"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_episode_index_is_str

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_episode_index, None, None, None)
        assert len(sub_clip.error_log) == 2
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Missing episode index"
        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[1].get("value") == invalid_missing_episode_index

    def test_invalid_season_index(self):
        invalid_negative_season_index = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                                         "season_index": -1, "episode_index": 1,
                                         "start_time": "30:03", "end_time": "46:32", "overwrite": False}
        invalid_season_index_is_str = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                                       "season_index": "HI THERE", "episode_index": 198,
                                       "start_time": "13:49", "end_time": "29:33", "overwrite": False}
        invalid_missing_season_index = {"playlist_title": "Hilda", "media_title": "Running Up That Hill",
                                        "season_index": None, "episode_index": 287,
                                        "start_time": "13:48", "end_time": "29:33", "overwrite": False}

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_negative_season_index, None, None, None)
        assert len(sub_clip.error_log) == 2
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("season_index") == -1

        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[1].get("value") == invalid_negative_season_index

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_season_index_is_str, None, None, None)
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values not int"
        assert sub_clip.error_log[0].get("season_index") == "HI THERE"

        assert sub_clip.error_log[1].get("message") == "Missing season index"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_season_index_is_str

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_season_index, None, None, None)
        assert len(sub_clip.error_log) == 2
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Missing season index"

        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[1].get("value") == invalid_missing_season_index

    def test_invalid_media_title(self):
        invalid_missing_media_title = {"playlist_title": "Hilda", "media_title": None,
                                       "season_index": 7, "episode_index": 287,
                                       "start_time": "13:48", "end_time": "29:33", "overwrite": False}
        invalid_characters_in_media_title = {"playlist_title": "Hilda", "media_title": "Running\/*+ Up That Hill",
                                             "season_index": 7, "episode_index": 287,
                                             "start_time": "13:48", "end_time": "29:33", "overwrite": False}

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_media_title, None, None, None)
        assert sub_clip
        assert sub_clip.error_log
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict

        assert sub_clip.error_log[0].get("message") == "media_title is not str"
        assert not sub_clip.error_log[0].get("value")
        assert sub_clip.error_log[0].get("media_title") is None

        assert sub_clip.error_log[1].get("message") == "Missing media title"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_missing_media_title

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_characters_in_media_title, None, None, None)

        assert sub_clip
        assert sub_clip.error_log
        assert len(sub_clip.error_log) == 2
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "media_title invalid characters found"
        assert not sub_clip.error_log[0].get("value")
        assert sub_clip.error_log[0].get("media_title") == "Running\/*+ Up That Hill"
        assert sub_clip.error_log[0].get("invalids") == "(/)"

        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[1].get("value") == invalid_characters_in_media_title

    def test_invalid_playlist_title(self):
        invalid_missing_playlist_title = {"playlist_title": None, "media_title": "Running Up That Hill",
                                          "season_index": 7, "episode_index": 287,
                                          "start_time": "13:48", "end_time": "29:33", "overwrite": False}
        invalid_characters_in_playlist_title = {"playlist_title": "Hilda//*+", "media_title": "Running Up That Hill",
                                                "season_index": 7, "episode_index": 287,
                                                "start_time": "13:48", "end_time": "29:33", "overwrite": False}

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_playlist_title, None, None, None)
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "playlist_title is not str"
        assert not sub_clip.error_log[0].get("value")
        assert sub_clip.error_log[0].get("playlist_title") is None

        assert sub_clip.error_log[1].get("message") == "Missing playlist title"

        assert type(sub_clip.error_log[2]) is dict
        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_missing_playlist_title

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_characters_in_playlist_title, None, None, None)
        assert len(sub_clip.error_log) == 2
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "playlist_title invalid characters found"
        assert not sub_clip.error_log[0].get("value")
        assert sub_clip.error_log[0].get("playlist_title") == "Hilda//*+"
        assert sub_clip.error_log[0].get("invalids") == "(/, /)"

        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[1].get("value") == invalid_characters_in_playlist_title


class TestConvertTimestamp(TestMp4Splitter):

    def test_invalid_timestamp_strings(self):
        error_list = []
        negative_second = "1:02:-43"
        negative_minute = "1:-20:13"
        negative_hour = "-5:20:13"

        mp4_splitter.convert_timestamp(negative_second, error_list)
        assert len(error_list) == 1

        assert type(error_list[0]) is dict
        assert error_list[0].get("value") == negative_second
        assert str(error_list[0].get("second")) in negative_second
        assert error_list[0].get("message") == "Values less than 0"

        error_list = []
        mp4_splitter.convert_timestamp(negative_minute, error_list)
        assert len(error_list) == 1
        assert type(error_list[0]) is dict
        assert error_list[0].get("value") == negative_minute
        assert str(error_list[0].get("minute")) in negative_minute
        assert error_list[0].get("message") == "Values less than 0"

        error_list = []
        mp4_splitter.convert_timestamp(negative_hour, error_list)
        assert len(error_list) == 1
        assert type(error_list[0]) is dict
        assert error_list[0].get("value") == negative_hour
        assert str(error_list[0].get("hour")) in negative_hour
        assert error_list[0].get("message") == "Values less than 0"


class TestEditor(TestMp4Splitter):
    editor_processor = mp4_splitter.SubclipProcessHandler()

    def test_editor_process_txt_file_error_invalid_file(self):
        file_name = "2024hi-01-31_16-32-36.json"
        error_log = mp4_splitter.editor_process_txt_file(file_name, self.modify_output_path, self.editor_processor)
        assert len(error_log) == 3
        assert type(error_log[0]) is dict

        assert "Text file empty" == error_log[1].get("message")
        assert file_name in error_log[1].get("value")

        assert "Missing file" == error_log[0].get("message")
        assert "2024hi-01-31_16-32-36.mp4" == error_log[0].get("value")

        assert "Errors occurred while processing file" == error_log[2].get("message")
        assert file_name in error_log[2].get("value")

    def test_editor_process_txt_file_error_missing_mp4(self):
        file_name = "2024-01-31_16-32-36_no_mp4.json"

        error_log = mp4_splitter.editor_process_txt_file(file_name, self.modify_output_path, self.editor_processor)
        assert "Missing file" == error_log[0].get("message")
        assert "2024-01-31_16-32-36_no_mp4" in error_log[0].get("value")
        assert "Errors occurred while processing file" == error_log[1].get("message")
        assert file_name in error_log[1].get("value")

    def test_editor_process_txt_file_error_empty_file(self):
        file_name = "2024-01-31_16-32-36_empty.json"
        error_log = mp4_splitter.editor_process_txt_file(file_name, self.modify_output_path,
                                                         self.editor_processor)
        assert type(error_log) is list
        assert len(error_log) == 2
        assert "Text file empty" == error_log[0].get("message")
        assert file_name in error_log[0].get("value")

        assert error_log[1].get("message") == "Errors occurred while processing file"
        assert file_name in error_log[1].get("value")

    def test_editor_process_txt_file_error_invalid_file_content(self):
        file_name = "2024-01-31_16-32-36_invalid.json"
        error_log = mp4_splitter.editor_process_txt_file(file_name, self.modify_output_path, self.editor_processor)
        assert len(error_log) == 4
        assert type(error_log[0]) is dict

        error = error_log[0]
        assert "Values less than 0" == error.get("message")
        assert "13:-3" == error.get("value")
        assert 0 == error.get("hour")
        assert 13 == error.get("minute")
        assert -3 == error.get("second")

        error = error_log[1]
        assert "End time >= start time" == error.get("message")

        error = error_log[2]
        assert "Errors occurred while parsing line" == error.get("message")

        error = error_log[3]
        assert "Errors occurred while processing file" == error.get("message")
        assert file_name == error.get("value")

    def test_editor_process_txt_file_name(self):
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)
        file_name = "2024-01-31_16-32-36.json"

        mp4_splitter.editor_process_txt_file(file_name, self.modify_output_path, self.editor_processor)
        editor_metadata = mp4_splitter.get_editor_metadata(self.raw_folder, self.editor_processor,
                                                           process_file=EDITOR_PROCESSED_LOG)

        assert type(editor_metadata) is dict
        assert 'txt_file_list' in editor_metadata
        assert type(editor_metadata.get('txt_file_list')) is list
        for txt_file in editor_metadata.get('txt_file_list'):
            assert type(txt_file) is dict
            assert type(txt_file.get("file_name")) is str
            assert type(txt_file.get("processed")) is bool
        assert 'selected_txt_file_title' in editor_metadata
        assert type(editor_metadata.get('selected_txt_file_title')) is str
        assert 'selected_editor_file_content' in editor_metadata
        assert type(editor_metadata.get('selected_editor_file_content')) is dict
        assert 'editor_process_metadata' in editor_metadata
        assert type(editor_metadata.get('editor_process_metadata')) is dict
        process_metadata = editor_metadata.get('editor_process_metadata')
        assert 'process_name' in process_metadata
        assert type(process_metadata.get('process_name')) is str
        assert 'process_end_time' in process_metadata
        assert type(process_metadata.get('process_end_time')) is str
        assert 'process_queue_size' in process_metadata
        assert type(process_metadata.get('process_queue_size')) is int
        assert 'process_log' in process_metadata
        assert type(process_metadata.get('process_log')) is list
        for process_log in process_metadata.get('process_log'):
            assert type(process_log) is dict
            assert 'message' in process_log
            assert type(process_log.get('message')) is str
            assert 'value' in process_log
            assert type(process_log.get('value')) is str

    def test_get_editor_metadata(self):

        editor_metadata = mp4_splitter.get_editor_metadata(self.raw_folder, self.editor_processor,
                                                           process_file=EDITOR_PROCESSED_LOG)
        assert editor_metadata
        assert type(editor_metadata) is dict
        print(json.dumps(editor_metadata.get("editor_process_metadata"), indent=4))

    def test_editor_process_get_metadata(self):
        editor_metadata = self.editor_processor.get_metadata()
        assert editor_metadata
        assert type(editor_metadata) is dict
        print(json.dumps(editor_metadata, indent=4))

    def test_editor_process_txt_file(self):
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)
        file_name_36 = "2024-01-31_16-32-36.json"
        file_name_38 = "2024-01-31_16-32-38.json"
        process_already_in_queue_error = {
            "message": "Destination path already in queue",
            "value": "/Hilda/Hilda - s2e1.mp4"
        }
        error_log = mp4_splitter.editor_process_txt_file(file_name_36, self.modify_output_path, self.editor_processor)

        assert not error_log
        editor_metadata = self.editor_processor.get_metadata()
        assert editor_metadata.get("process_queue_size") == 1
        assert len(editor_metadata.get("process_queue")) == 1
        assert len(editor_metadata.get("process_log")) == 3
        assert editor_metadata.get("process_log")[0].get("message") == process_already_in_queue_error.get("message")
        assert editor_metadata.get("process_log")[1].get("message") == process_already_in_queue_error.get("message")
        assert editor_metadata.get("process_log")[2].get("message") == process_already_in_queue_error.get("message")
        assert process_already_in_queue_error.get("value") in editor_metadata.get("process_log")[0].get("value")
        assert process_already_in_queue_error.get("value") in editor_metadata.get("process_log")[1].get("value")
        assert process_already_in_queue_error.get("value") in editor_metadata.get("process_log")[2].get("value")

        error_log = mp4_splitter.editor_process_txt_file(file_name_38, self.modify_output_path, self.editor_processor)
        editor_metadata = self.editor_processor.get_metadata()
        assert editor_metadata.get("process_queue_size") == 5
        assert len(editor_metadata.get("process_queue")) == 5
        assert not editor_metadata.get("process_log")
        assert error_log
        assert error_log[0] == {'message': 'Values not int', 'season_index': 'HELLO THERE'}
        assert error_log[1] == {'message': 'Missing season index'}
        assert error_log[2].get("message") == 'Errors occurred while parsing line'
        assert error_log[3] == {"message": "Errors occurred while processing file",
                                "value": "2024-01-31_16-32-38.json"}

        while not self.editor_processor.subclip_process_queue.empty():
            editor_metadata = self.editor_processor.get_metadata()
            assert type(editor_metadata) is dict
            assert 'process_name' in editor_metadata
            assert type(editor_metadata.get('process_name')) is str

            assert 'process_end_time' in editor_metadata
            assert type(editor_metadata.get('process_end_time')) is str

            assert 'percent_complete' in editor_metadata
            assert type(editor_metadata.get('percent_complete')) is int

            assert 'process_queue_size' in editor_metadata
            assert type(editor_metadata.get('process_queue_size')) is int

            assert 'process_log' in editor_metadata
            assert type(editor_metadata.get('process_log')) is list

            assert 'process_queue' in editor_metadata
            assert type(editor_metadata.get('process_queue')) is list

        editor_metadata = self.editor_processor.get_metadata()
        assert editor_metadata.get("process_queue_size") == 0
        assert len(editor_metadata.get("process_queue")) == 0

    def test_valid_txt_file(self):
        error_log = []
        sub_clips = []
        editor_metadata = {
            'file_name': "2024-01-31_16-32-36.json"
        }

        output_path = pathlib.Path(self.modify_output_path).resolve()
        txt_file = f"{self.raw_folder}{editor_metadata.get('file_name')}"
        txt_file_path = pathlib.Path(txt_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, output_path, sub_clips, error_log)
        assert len(error_log) == 0

    def test_empty_txt_file(self):
        error_log = []
        editor_metadata = {
            'file_name': "2024-01-31_16-32-36_empty.json"
        }
        txt_file = f"{self.raw_folder}{editor_metadata.get('file_name')}"
        sub_clips = []
        txt_file_path = pathlib.Path(txt_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, None, sub_clips, error_log)
        assert type(error_log) is list
        assert len(error_log) == 1
        assert "Text file empty" == error_log[0].get("message")
        assert editor_metadata.get("file_name") in error_log[0].get("value")

    def test_invalid_txt_file(self):
        error_log = []
        sub_clips = []
        editor_metadata = {
            'file_name': "2024-01-31_16-32-36_invalid.json",
            'media_type': ContentType.TV.value
        }
        txt_file = f"{self.raw_folder}{editor_metadata.get('file_name')}"
        txt_file_path = pathlib.Path(txt_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, None, sub_clips, error_log)
        assert len(error_log) == 3
        error_log = sub_clips[0].error_log
        assert type(error_log[0]) is dict
        error = error_log[0]
        assert "Values less than 0" == error.get("message")
        assert "13:-3" == error.get("value")
        assert 0 == error.get("hour")
        assert 13 == error.get("minute")
        assert -3 == error.get("second")

        error = error_log[1]
        assert "End time >= start time" == error.get("message")

        error = error_log[2]
        assert "Errors occurred while parsing line" == error.get("message")


class TestGetCMDList(TestMp4Splitter):

    def test_get_cmd_list(self):
        error_log = []
        sub_clips = []

        txt_file_name = "2024-01-31_16-32-36"

        output_path = pathlib.Path(self.modify_output_path).resolve()
        assert output_path.exists()
        txt_file = f"{self.raw_folder}{txt_file_name}.json"
        mp4_file = txt_file.replace('.json', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()
        assert txt_file_path.exists()
        assert mp4_file_path.exists()

        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, output_path, sub_clips, error_log)
        assert len(error_log) == 0
        for sub_clip in sub_clips:
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert sub_clip.source_file_path == mp4_file_path.as_posix()
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "episode 2"
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "episode 1"


class TestProcessSubclipFile(TestMp4Splitter):

    def test_valid_full_content_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "2024-01-31_16-32-36"

        output_path = pathlib.Path(self.modify_output_path).resolve()
        assert output_path.exists()
        txt_file = f"{self.raw_folder}{txt_file_name}.json"
        mp4_file = txt_file.replace('.json', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()
        assert txt_file_path.exists()
        assert mp4_file_path.exists()

        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, output_path, sub_clips, error_log)

        # assert type(cmd_list) is list
        # assert len(cmd_list) == 5
        assert len(error_log) == 0
        for sub_clip in sub_clips:
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0

        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "episode 2"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "episode 1"

    def test_valid_full_content_txt_file_zero(self):
        error_log = []
        sub_clips = []
        txt_file_name = "2024-01-31_16-32-36_zero"

        output_path = pathlib.Path(self.modify_output_path).resolve()
        assert output_path.exists()
        txt_file = f"{self.raw_folder}{txt_file_name}.json"
        mp4_file = txt_file.replace('.json', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()
        assert txt_file_path.exists()
        assert mp4_file_path.exists()

        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, output_path, sub_clips, error_log)
        assert len(error_log) == 0
        for sub_clip in sub_clips:
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0

        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert "/Hilda/Hilda - s2e0.mp4" in sub_clips[
            0].destination_file_path
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert "/Hilda/Hilda - s2e2.mp4" in sub_clips[
            1].destination_file_path
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "episode 2"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "episode 1"

    def test_valid_movie_full_content_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "movie"

        output_path = pathlib.Path(self.modify_output_path).resolve()
        assert output_path.exists()
        txt_file = f"{self.raw_folder}{txt_file_name}.json"
        mp4_file = txt_file.replace('.json', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()
        assert txt_file_path.exists()
        assert mp4_file_path.exists()

        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, output_path, sub_clips, error_log)

        assert len(error_log) == 0
        for sub_clip in sub_clips:
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0
        assert len(sub_clips) == 2
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[0].start_time == 2846
        assert sub_clips[0].end_time == 3730
        assert sub_clips[0].media_title == "This is also a movie"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[1].start_time == 3763
        assert sub_clips[1].end_time == 4813
        assert sub_clips[1].media_title == "This is a movie"

    def test_valid_book_full_content_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "book"

        output_path = pathlib.Path(self.modify_output_path).resolve()
        assert output_path.exists()
        txt_file = f"{self.raw_folder}{txt_file_name}.json"
        mp4_file = txt_file.replace('.json', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()
        assert txt_file_path.exists()
        assert mp4_file_path.exists()

        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, output_path, sub_clips, error_log)

        assert len(error_log) == 0
        for sub_clip in sub_clips:
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert sub_clip.source_file_path == mp4_file_path.as_posix()
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0
        assert len(sub_clips) == 2
        assert sub_clips[0].start_time == 2846
        assert sub_clips[0].end_time == 3730
        assert sub_clips[0].media_title == "This is a book title"
        assert sub_clips[1].start_time == 3763
        assert sub_clips[1].end_time == 4813
        assert sub_clips[1].media_title == "Dinosaur Rawr"

    def test_valid_timing_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "2024-01-31_16-32-37"

        output_path = pathlib.Path(self.modify_output_path).resolve()
        assert output_path.exists()
        txt_file = f"{self.raw_folder}{txt_file_name}.json"
        mp4_file = txt_file.replace('.json', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()
        assert txt_file_path.exists()
        assert mp4_file_path.exists()
        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, output_path, sub_clips, error_log)

        assert len(error_log) == 0
        for index, sub_clip in enumerate(sub_clips):
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0

        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "a"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "b"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "c"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "d"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "e"

    def test_already_exists_mp4_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "2024-01-31_16-32-36_already_exists"

        output_path = pathlib.Path(self.raw_folder).resolve()
        assert output_path.exists()
        txt_file = f"{self.raw_folder}{txt_file_name}.json"
        mp4_file = txt_file.replace('.json', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()
        assert txt_file_path.exists()
        assert mp4_file_path.exists()
        mp4_splitter.get_sub_clips_from_txt_file(txt_file_path, output_path, sub_clips, error_log)

        assert len(error_log) == 2

        assert "File already exists" == error_log[0].get("message")
        assert "Hilda - s4e8.mp4" == error_log[0].get("value")

        assert "Errors occurred while parsing line" == error_log[1].get("message")

        for index, sub_clip in enumerate(sub_clips):
            if index == 3:
                assert not sub_clip.destination_file_path
                continue
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0

        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[0].destination_file_path == f"{self.raw_folder}Hilda/Hilda - s2e1.mp4"
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[1].destination_file_path == f"{self.raw_folder}Hilda/Hilda - s3e1.mp4"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[2].destination_file_path == f"{self.raw_folder}Hilda/Hilda - s4e7.mp4"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"

        assert sub_clips[3].error_log
        assert len(sub_clips[3].error_log) == 3
        assert sub_clips[3].error_log[0] == {'message': 'File already exists', 'value': 'Hilda - s4e8.mp4'}

        assert sub_clips[0].source_file_path == mp4_file_path.as_posix()
        assert sub_clips[4].destination_file_path == f"{self.raw_folder}Hilda/Hilda - s2e3.mp4"
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "episode 1"
