import json
import pathlib
from unittest import TestCase
import mp4_splitter
import config_file_handler
import __init__
from database_handler.common_objects import ContentType
from database_handler.db_getter import DatabaseHandler, DatabaseHandlerV2
from database_handler.db_setter import DBCreatorV2

EDITOR_PROCESSED_LOG = "editor_metadata.json"


class TestMp4Splitter(TestCase):
    default_config = config_file_handler.load_json_file_content()
    raw_folder = default_config.get('editor_raw_folder')
    raw_url = default_config.get('editor_raw_url')
    modify_output_path = default_config.get("media_folders")[0].get("content_src")
    editor_metadata_file = f"{raw_folder}editor_metadata.json"


class Test(TestMp4Splitter):

    def test_splitter_split_txt_file_content(self):
        subclip_metadata_str = "1:20:47,1:40:43"
        subclip_metadata = mp4_splitter.TvShowSubclipMetadata(subclip_metadata_str, None, None, None)
        print(subclip_metadata.start_time)
        print(subclip_metadata.end_time)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043

        subclip_metadata_str = "Hilda,episode 1,2,1,1:20:47,1:40:43"
        subclip_metadata = mp4_splitter.TvShowSubclipMetadata(subclip_metadata_str, None, None, None)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043
        assert subclip_metadata.episode_index == 1
        assert subclip_metadata.season_index == 2
        assert subclip_metadata.media_title == "episode 1"
        assert subclip_metadata.playlist_title == "Hilda"

    def test_splitter_remove_quotes(self):
        subclip_metadata_str = 'Hilda,"episode 1",2,1,1:20:47,1:40:43'
        subclip_metadata = mp4_splitter.TvShowSubclipMetadata(subclip_metadata_str, None, None, None)
        print(json.dumps(subclip_metadata.error_log, indent=4))
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043
        print(subclip_metadata.episode_index)
        assert subclip_metadata.episode_index == 1
        assert subclip_metadata.season_index == 2
        assert subclip_metadata.media_title == "episode 1"
        assert subclip_metadata.playlist_title == "Hilda"

    def test_validate_editor_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_content = [
            "Hilda,episode name,2,1,7,13:43",
            'Hilda,"episode another name",2,1,13:49,29:33',
            "Hilda,episode name,2,1,30:03,46:32",
            "Hilda,episode 2,2,2,47:26,1:02:10",
            "Hilda,episode 1,2,1,1:02:43,1:20:13"
        ]
        for txt_line in txt_file_content:
            sub_clip = mp4_splitter.convert_txt_to_sub_clip(txt_line, ContentType.TV.value, error_log, None, None,
                                                            None)
            error_log.extend(sub_clip.error_log)
            sub_clips.append(sub_clip)
        # print(json.dumps(sub_clips, indent=4))

        print(sub_clips)
        print(len(sub_clips))
        assert len(sub_clips) == len(txt_file_content)
        assert len(error_log) == 0

        for subclip in sub_clips:
            print(subclip.media_title)

    def test_validate_editor_txt_file_times(self):
        error_log = []
        sub_clips = []
        txt_file_content = [
            "7,13:43",
            "13:49,29:33",
            "30:03,46:32",
            "47:26,1:02:10",
            "1:02:43,1:20:13"
        ]
        for txt_line in txt_file_content:
            sub_clip = mp4_splitter.convert_txt_to_sub_clip(txt_line, ContentType.TV.value, error_log, None, None,
                                                            None)
            error_log.extend(sub_clip.error_log)
            sub_clips.append(sub_clip)

        print(len(sub_clips))
        assert len(sub_clips) == len(txt_file_content)
        assert len(error_log) == 0

    def test_validate_editor_txt_file_invalid(self):
        error_log = []
        sub_clips = []
        txt_file_content = [
            "7,13:43",
            "1,13:49,29:33",
            "2,1,30:03,46:32",
            "episode 1,2,1,47:26,1:02:10",
            "Hilda,episode 1,hello,1,1:02:43,1:20:13"
        ]
        for txt_line in txt_file_content:
            sub_clip = mp4_splitter.convert_txt_to_sub_clip(txt_line, ContentType.TV.value, error_log, None, None,
                                                            None)
            # error_log.extend(sub_clip.error_log)
            sub_clips.append(sub_clip)

        print(json.dumps(error_log, indent=4))
        print(len(error_log))
        print(len(sub_clips))
        assert 5 == len(sub_clips)
        assert 0 == len(error_log)

        error_log = sub_clips[1].error_log
        print(json.dumps(error_log, indent=4))

        assert error_log[0].get("message") == "Missing content"
        assert error_log[0].get("value") == "1,13:49,29:33"

        assert error_log[1].get("message") == f"Errors occurred while parsing line"
        assert error_log[1].get("value") == txt_file_content[1]

        # assert error_log[2].get("message") == "Failing line index"
        # assert error_log[2].get("value") == 1
        error_log = sub_clips[2].error_log
        print(json.dumps(error_log, indent=4))

        assert error_log[0].get("message") == "Missing content"
        assert error_log[0].get("value") == "2,1,30:03,46:32"

        assert error_log[1].get("message") == f"Errors occurred while parsing line"
        assert error_log[1].get("value") == txt_file_content[2]

        error_log = sub_clips[3].error_log
        print(json.dumps(error_log, indent=4))

        assert error_log[0].get("message") == "Missing content"
        assert error_log[0].get("value") == "episode 1,2,1,47:26,1:02:10"

        assert error_log[1].get("message") == f"Errors occurred while parsing line"
        assert error_log[1].get("value") == txt_file_content[3]

        error_log = sub_clips[4].error_log
        print(json.dumps(error_log, indent=4))

        assert error_log[0].get("message") == "Values not int"
        assert error_log[0].get("season_index") == "hello"

        assert error_log[1].get("message") == "Missing season index"

        assert error_log[2].get("message") == f"Errors occurred while parsing line"
        assert error_log[2].get("value") == txt_file_content[4]

    def test_load_txt_file_content(self):
        txt_file_name = "2024-01-31_16-32-36.txt"
        selected_txt_file_path = pathlib.Path(f"{self.raw_folder}{txt_file_name}").resolve()
        print(config_file_handler.load_txt_file_content(selected_txt_file_path))

    def test_validate_editor_cmd_list(self):
        error_log = []
        sub_clips = []
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36.txt"
        }
        media_type = ContentType.TV.value

        with DBCreatorV2() as db_connection:
            media_folder_path = db_connection.get_all_content_directory_info()[0].get("content_src")
        output_path = pathlib.Path(media_folder_path).resolve()
        txt_file = f"{self.raw_folder}{editor_metadata.get('txt_file_name')}"
        mp4_file = txt_file.replace('.txt', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(media_type, txt_file_path, output_path, sub_clips, error_log)

        # assert cmd_list
        print(sub_clips[0])
        assert 5 == len(sub_clips)
        assert 0 == len(error_log)

        current_index = mp4_splitter.ALPHANUMERIC_INDEX_A
        for sub_clip in sub_clips:
            assert type(sub_clip.media_title) is str
            assert type(sub_clip.start_time) is int
            assert type(sub_clip.end_time) is int
            assert sub_clip.source_file_path == f'{self.raw_folder}2024-01-31_16-32-36.mp4'

            current_index += 1
        # print(cmd_list)

    def test_validate_editor_cmd_list_remove_quotes(self):
        error_log = []
        sub_clips = []
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_quotes.txt"
        }
        media_type = ContentType.TV.value

        with DatabaseHandler() as db_connection:
            media_folder_path = db_connection.get_media_folder_path_from_type(media_type)
        output_path = pathlib.Path(media_folder_path).resolve()
        txt_file = f"{self.raw_folder}{editor_metadata.get('txt_file_name')}"
        mp4_file = txt_file.replace('.txt', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(media_type, txt_file_path, output_path, sub_clips, error_log)

        # assert cmd_list
        print(sub_clips[0])
        assert 5 == len(sub_clips)
        assert 0 == len(error_log)

        current_index = mp4_splitter.ALPHANUMERIC_INDEX_A
        for sub_clip in sub_clips:
            assert type(sub_clip.media_title) is str
            assert type(sub_clip.start_time) is int
            assert type(sub_clip.end_time) is int
            assert sub_clip.source_file_path == f'{self.raw_folder}2024-01-31_16-32-36_quotes.mp4'
            assert '"' not in sub_clip.media_title
            print(sub_clip.destination_file_path)
            current_index += 1
        # print(cmd_list)


class TestConvertTimestamp(TestMp4Splitter):

    def test_invalid_timestamp_strings(self):
        error_list = []
        negative_second = "1:02:-43"
        negative_minute = "1:-20:13"
        negative_hour = "-5:20:13"

        mp4_splitter.convert_timestamp(negative_second, error_list)
        print(json.dumps(error_list, indent=4))
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


class TestSubclipMetadata(TestMp4Splitter):

    def test_invalid_timestamp_strings(self):
        invalid_end_minute_timestamp = "1:02:43,1:-20:13"
        invalid_end_second_timestamp = "1:02:43,1:20:-13"
        invalid_start_second_timestamp = "1:02:-43,1:20:13"

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_end_minute_timestamp, None, None, None)
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("hour") == 1
        assert sub_clip.error_log[0].get("minute") == -20
        assert sub_clip.error_log[0].get("second") == 13

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_end_second_timestamp, None, None, None)
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("hour") == 1
        assert sub_clip.error_log[0].get("minute") == 20
        assert sub_clip.error_log[0].get("second") == -13

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_start_second_timestamp, None, None, None)
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("hour") == 1
        assert sub_clip.error_log[0].get("minute") == 2
        assert sub_clip.error_log[0].get("second") == -43

    def test_valid_full_data_strings(self):
        valid_data_set = "Hilda,Running Up That Hill,2,1,7,13:43"
        subclip_metadata = mp4_splitter.TvShowSubclipMetadata(valid_data_set, None, None, None)
        assert subclip_metadata.playlist_title == "Hilda"
        assert subclip_metadata.media_title == "Running Up That Hill"
        assert subclip_metadata.season_index == 2
        assert subclip_metadata.episode_index == 1
        assert subclip_metadata.start_time == 7
        assert subclip_metadata.end_time == 823

    def test_invalid_end_minute(self):
        invalid_negative_end_minute_timestamp = "Hilda,episode name,2,1,1:02:43,1:-20:13"
        invalid_end_minute_is_str_timestamp = "Hilda,episode name,2,1,1:02:43,1:HELLO:13"
        invalid_missing_end_minute_timestamp = "Hilda,episode name,2,1,1:02:43,1::13"

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_negative_end_minute_timestamp, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))

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
        print(json.dumps(sub_clip.error_log, indent=4))

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
        print(json.dumps(sub_clip.error_log, indent=4))

        assert sub_clip.error_log[0].get("message") == "Missing timestamp value"
        assert sub_clip.error_log[0].get("value") == "1::13"
        assert sub_clip.error_log[0].get("hour") == "1"
        assert sub_clip.error_log[0].get("minute") == ""
        assert sub_clip.error_log[0].get("second") == "13"

        assert sub_clip.error_log[1].get("message") == "End time >= start time"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_missing_end_minute_timestamp

    def test_invalid_start_second(self):
        invalid_negative_start_second_timestamp = "Hilda,Running Up That Hill,1,1,13:-49,29:33"
        invalid_start_second_is_str_timestamp = "Hilda,Running Up That Hill,1,1,13:HELLO,29:33"
        invalid_missing_start_second_timestamp = "Hilda,Running Up That Hill,1,1,13:,29:33"

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
        invalid_negative_episode_index = "Hilda,Running Up That Hill,1,-1,30:03,46:32"
        invalid_episode_index_is_str = "Hilda,Running Up That Hill,1,HELLO,13:49,29:33"
        invalid_missing_episode_index = "Hilda,Running Up That Hill,1,,13:48,29:33"

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_negative_episode_index, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))
        assert len(sub_clip.error_log) == 2
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("episode_index") == "-1"

        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[1].get("value") == invalid_negative_episode_index

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_episode_index_is_str, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values not int"
        assert sub_clip.error_log[0].get("episode_index") == "HELLO"

        assert sub_clip.error_log[1].get("message") == "Missing episode index"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_episode_index_is_str

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_episode_index, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values not int"
        assert sub_clip.error_log[0].get("episode_index") == ""
        assert sub_clip.error_log[1].get("message") == "Missing episode index"
        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_missing_episode_index

    def test_invalid_season_index(self):
        invalid_negative_season_index = "Hilda,Running Up That Hill,-1,1,30:03,46:32"
        invalid_season_index_is_str = "Hilda,Running Up That Hill,HI THERE,198,13:49,29:33"
        invalid_missing_season_index = "Hilda,Running Up That Hill,,287,13:48,29:33"

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_negative_season_index, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))
        assert len(sub_clip.error_log) == 2
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values less than 0"
        assert sub_clip.error_log[0].get("season_index") == "-1"

        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[1].get("value") == invalid_negative_season_index

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_season_index_is_str, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values not int"
        assert sub_clip.error_log[0].get("season_index") == "HI THERE"

        assert sub_clip.error_log[1].get("message") == "Missing season index"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_season_index_is_str

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_season_index, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "Values not int"
        assert sub_clip.error_log[0].get("season_index") == ""

        assert sub_clip.error_log[1].get("message") == "Missing season index"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_missing_season_index

    def test_invalid_media_title(self):
        invalid_missing_media_title = "Hilda,,7,287,13:48,29:33"
        invalid_characters_in_media_title = "Hilda,Running\/*+ Up That Hill,7,287,13:48,29:33"

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_media_title, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))
        assert sub_clip
        assert sub_clip.error_log
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict

        assert sub_clip.error_log[0].get("message") == "media_title the value must not be an empty"
        assert not sub_clip.error_log[0].get("value")
        assert sub_clip.error_log[0].get("media_title") == ""

        assert sub_clip.error_log[1].get("message") == "Missing media title"

        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_missing_media_title

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_characters_in_media_title, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))

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
        invalid_missing_playlist_title = ",Running Up That Hill,7,287,13:48,29:33"
        invalid_characters_in_playlist_title = "Hilda//*+,Running Up That Hill,7,287,13:48,29:33"

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_missing_playlist_title, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))
        assert len(sub_clip.error_log) == 3
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "playlist_title the value must not be an empty"
        assert not sub_clip.error_log[0].get("value")
        assert sub_clip.error_log[0].get("playlist_title") == ""

        assert sub_clip.error_log[1].get("message") == "Missing playlist title"

        assert type(sub_clip.error_log[2]) is dict
        assert sub_clip.error_log[2].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[2].get("value") == invalid_missing_playlist_title

        sub_clip = mp4_splitter.TvShowSubclipMetadata(invalid_characters_in_playlist_title, None, None, None)
        print(json.dumps(sub_clip.error_log, indent=4))
        assert len(sub_clip.error_log) == 2
        assert type(sub_clip.error_log[0]) is dict
        assert sub_clip.error_log[0].get("message") == "playlist_title invalid characters found"
        assert not sub_clip.error_log[0].get("value")
        assert sub_clip.error_log[0].get("playlist_title") == "Hilda//*+"
        assert sub_clip.error_log[0].get("invalids") == "(/, /)"

        assert sub_clip.error_log[1].get("message") == "Errors occurred while parsing line"
        assert sub_clip.error_log[1].get("value") == invalid_characters_in_playlist_title


class TestEditor(TestMp4Splitter):
    editor_processor = mp4_splitter.SubclipProcessHandler()

    def test_editor_process_txt_file_error_invalid_file(self):
        editor_metadata = {
            'txt_file_name': "2024hi-01-31_16-32-36.txt"
        }
        media_type = ContentType.TV.value
        error_log = mp4_splitter.editor_process_txt_file(editor_metadata, media_type, self.modify_output_path,
                                                         self.editor_processor)
        print(json.dumps(error_log, indent=4))
        assert len(error_log) == 3
        assert type(error_log[0]) is dict

        assert "Text file empty" == error_log[1].get("message")
        assert editor_metadata.get("txt_file_name") in error_log[1].get("value")

        assert "Missing file" == error_log[0].get("message")
        assert "2024hi-01-31_16-32-36.mp4" == error_log[0].get("value")

        assert "Errors occurred while processing file" == error_log[2].get("message")
        assert editor_metadata.get("txt_file_name") in error_log[2].get("value")

    def test_editor_process_txt_file_error_missing_mp4(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_no_mp4.txt"
        }
        media_type = ContentType.TV.value

        error_log = mp4_splitter.editor_process_txt_file(editor_metadata, media_type,
                                                         self.modify_output_path, self.editor_processor)
        print(json.dumps(error_log, indent=4))
        assert "Missing file" == error_log[0].get("message")
        assert "2024-01-31_16-32-36_no_mp4" in error_log[0].get("value")
        assert "Errors occurred while processing file" == error_log[1].get("message")
        assert editor_metadata.get('txt_file_name') in error_log[1].get("value")

    def test_editor_process_txt_file_error_empty_file(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_empty.txt"
        }
        media_type = ContentType.TV.value
        error_log = mp4_splitter.editor_process_txt_file(editor_metadata, media_type,
                                                         self.modify_output_path, self.editor_processor)
        print(json.dumps(error_log, indent=4))
        assert type(error_log) is list
        assert len(error_log) == 2
        assert "Text file empty" == error_log[0].get("message")
        assert editor_metadata.get("txt_file_name") in error_log[0].get("value")

        assert error_log[1].get("message") == "Errors occurred while processing file"
        assert editor_metadata.get("txt_file_name") in error_log[1].get("value")

    def test_editor_process_txt_file_error_invalid_file_content(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_invalid.txt"
        }
        media_type = ContentType.TV.value

        error_log = mp4_splitter.editor_process_txt_file(editor_metadata, media_type,
                                                         self.modify_output_path, self.editor_processor)
        print(error_log)
        print(json.dumps(error_log, indent=4))
        print(len(error_log))
        assert len(error_log) == 5
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
        assert "7,13:-3" == error.get("value")

        error = error_log[3]
        assert "Failing line index" == error.get("message")
        assert 0 == error.get("value")

    def test_editor_process_txt_file_name(self):
        __init__.patch_extract_subclip(self)
        __init__.patch_update_processed_file(self)
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36.txt",
        }
        media_type = ContentType.TV.value
        mp4_splitter.editor_process_txt_file(editor_metadata, media_type,
                                             pathlib.Path(self.modify_output_path).resolve(), self.editor_processor)
        new_editor_metadata = mp4_splitter.get_editor_metadata(self.raw_folder, self.editor_processor,
                                                               process_file=EDITOR_PROCESSED_LOG)
        # print(json.dumps(new_editor_metadata, indent=4))

        assert type(new_editor_metadata) is dict
        assert 'txt_file_list' in new_editor_metadata
        assert type(new_editor_metadata.get('txt_file_list')) is list
        for txt_file in new_editor_metadata.get('txt_file_list'):
            assert type(txt_file) is dict
            assert type(txt_file.get("file_name")) is str
            assert type(txt_file.get("processed")) is bool
        assert 'selected_txt_file_title' in new_editor_metadata
        assert type(new_editor_metadata.get('selected_txt_file_title')) is str
        assert 'selected_txt_file_content' in new_editor_metadata
        assert type(new_editor_metadata.get('selected_txt_file_content')) is str
        assert 'editor_process_metadata' in new_editor_metadata
        assert type(new_editor_metadata.get('editor_process_metadata')) is dict
        process_metadata = new_editor_metadata.get('editor_process_metadata')
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
            assert 'file_name' in process_log
            assert type(process_log.get('file_name')) is str

    def test_get_editor_metadata(self):

        editor_metadata = mp4_splitter.get_editor_metadata(self.raw_folder, self.editor_processor,
                                                           process_file=EDITOR_PROCESSED_LOG)
        print(editor_metadata)
        print(json.dumps(editor_metadata, indent=4))

    def test_editor_process_txt_file(self):
        __init__.patch_extract_subclip(self)
        __init__.patch_update_processed_file(self)
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36.txt",
            'media_type': ContentType.TV.value
        }

        error_log = mp4_splitter.editor_process_txt_file(editor_metadata, ContentType.TV.value,
                                                         pathlib.Path(self.modify_output_path).resolve(),
                                                         self.editor_processor)

        assert not error_log
        editor_metadata = self.editor_processor.get_metadata()
        print(editor_metadata)
        assert editor_metadata.get("process_queue_size") == 4
        assert len(editor_metadata.get("process_queue")) == 4
        assert not editor_metadata.get("process_log")
        # time.sleep(2)
        # time.sleep(10)
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-38.txt",
            'media_type': ContentType.TV.value
        }
        error_log = mp4_splitter.editor_process_txt_file(editor_metadata, ContentType.TV.value,
                                                         pathlib.Path(self.modify_output_path).resolve(),
                                                         self.editor_processor)

        editor_metadata = self.editor_processor.get_metadata()
        print(editor_metadata)
        assert editor_metadata.get("process_queue_size") == 8
        assert len(editor_metadata.get("process_queue")) == 8
        print(error_log)
        assert error_log
        assert error_log[0] == {'message': 'Values not int', 'season_index': 'HELLO THERE'}
        assert error_log[1] == {'message': 'Missing season index'}
        assert error_log[2] == {'message': 'Errors occurred while parsing line',
                                'value': 'Hilda,episode 2,HELLO THERE,8,47:26,1:02:10'}
        assert error_log[3] == {'message': 'Failing line index', 'value': 3}

        assert error_log[4] == {'message': 'Errors occurred while processing file', 'value': '2024-01-31_16-32-38.txt'}

        while not self.editor_processor.subclip_process_queue.empty():
            editor_metadata = self.editor_processor.get_metadata()
            print(editor_metadata)
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
        print(editor_metadata)
        assert editor_metadata.get("process_queue_size") == 0
        assert len(editor_metadata.get("process_queue")) == 0

    def test_valid_txt_file(self):
        error_log = []
        sub_clips = []
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36.txt"
        }
        media_type = ContentType.TV.value

        with DBCreatorV2() as db_connection:
            media_folder_path = db_connection.get_all_content_directory_info()[0]
        output_path = pathlib.Path(media_folder_path.get("content_src")).resolve()
        txt_file = f"{self.raw_folder}{editor_metadata.get('txt_file_name')}"
        mp4_file = txt_file.replace('.txt', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(media_type, txt_file_path, output_path, sub_clips, error_log)
        assert len(error_log) == 0

    def test_empty_txt_file(self):
        error_log = []
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_empty.txt"
        }
        txt_file = f"{self.raw_folder}{editor_metadata.get('txt_file_name')}"
        sub_clips = []
        txt_file_path = pathlib.Path(txt_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(editor_metadata, txt_file_path, None, sub_clips, error_log)
        print(json.dumps(error_log, indent=4))
        assert type(error_log) is list
        assert len(error_log) == 1
        assert "Text file empty" == error_log[0].get("message")
        assert editor_metadata.get("txt_file_name") in error_log[0].get("value")

    def test_invalid_txt_file(self):
        error_log = []
        sub_clips = []
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_invalid.txt",
            'media_type': ContentType.TV.value
        }
        txt_file = f"{self.raw_folder}{editor_metadata.get('txt_file_name')}"
        txt_file_path = pathlib.Path(txt_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(editor_metadata.get("media_type"), txt_file_path, None, sub_clips,
                                                 error_log)
        error_sum = []
        for sub_clip in sub_clips:
            error_sum.extend(sub_clip.error_log)
        assert len(error_sum) == 4
        assert len(error_log) == 0
        error_log = sub_clips[0].error_log
        print(json.dumps(error_log, indent=4))
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
        assert "7,13:-3" == error.get("value")

        error = error_log[3]
        assert "Failing line index" == error.get("message")
        assert 0 == error.get("value")


class TestGetCMDList(TestMp4Splitter):

    def test_get_cmd_list(self):
        error_log = []
        sub_clips = []

        txt_file_name = "2024-01-31_16-32-36"

        media_type = ContentType.TV.value

        with DatabaseHandler() as db_connection:
            media_folder_path = db_connection.get_media_folder_path_from_type(media_type)
        output_path = pathlib.Path(media_folder_path).resolve()
        txt_file = f"{self.raw_folder}{txt_file_name}.txt"
        mp4_file = txt_file.replace('.txt', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(media_type, txt_file_path, output_path, sub_clips, error_log)

        assert len(error_log) == 0
        for sub_clip in sub_clips:
            print(sub_clip.source_file_path)
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0
        assert sub_clips[
                   0].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert sub_clips[
                   1].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert sub_clips[
                   2].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"
        assert sub_clips[
                   3].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "episode 2"
        assert sub_clips[
                   4].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "episode 1"


class TestProcessSubclipFile(TestMp4Splitter):

    def test_valid_full_content_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "2024-01-31_16-32-36"
        media_type = ContentType.TV.value

        txt_file = f"{self.raw_folder}{txt_file_name}.txt"
        mp4_file = txt_file.replace('.txt', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(media_type, txt_file_path, pathlib.Path(self.raw_folder).resolve(),
                                                 sub_clips, error_log)
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

        assert sub_clips[
                   0].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert sub_clips[
                   1].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert sub_clips[
                   2].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"
        assert sub_clips[
                   3].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "episode 2"
        assert sub_clips[
                   4].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36.mp4"
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "episode 1"

    def test_valid_movie_full_content_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "movie"
        media_type = ContentType.MOVIE.value

        txt_file = f"{self.raw_folder}{txt_file_name}.txt"
        mp4_file = txt_file.replace('.txt', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(media_type, txt_file_path, pathlib.Path(self.raw_folder).resolve(),
                                                 sub_clips, error_log)
        print(json.dumps(error_log, indent=4))
        assert len(error_log) == 0
        for sub_clip in sub_clips:
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0
        assert len(sub_clips) == 2
        assert sub_clips[
                   0].source_file_path == f"{self.raw_folder}movie.mp4"
        assert sub_clips[0].start_time == 2846
        assert sub_clips[0].end_time == 3730
        assert sub_clips[0].media_title == "This is also a movie"
        print(sub_clips[0].destination_file_path)
        assert sub_clips[
                   1].source_file_path == f"{self.raw_folder}movie.mp4"
        assert sub_clips[1].start_time == 3763
        assert sub_clips[1].end_time == 4813
        assert sub_clips[1].media_title == "This is a movie"

    def test_valid_book_full_content_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "book"
        media_type = ContentType.BOOK.value

        txt_file = f"{self.raw_folder}{txt_file_name}.txt"
        mp4_file = txt_file.replace('.txt', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(media_type, txt_file_path, pathlib.Path(self.raw_folder).resolve(),
                                                 sub_clips, error_log)
        print(json.dumps(error_log, indent=4))
        assert len(error_log) == 0
        for sub_clip in sub_clips:
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0
        assert len(sub_clips) == 2
        assert sub_clips[
                   0].source_file_path == f"{self.raw_folder}book.mp4"
        assert sub_clips[0].start_time == 2846
        assert sub_clips[0].end_time == 3730
        assert sub_clips[0].media_title == "This is a book title"
        print(sub_clips[0].destination_file_path)
        assert sub_clips[
                   1].source_file_path == f"{self.raw_folder}book.mp4"
        assert sub_clips[1].start_time == 3763
        assert sub_clips[1].end_time == 4813
        assert sub_clips[1].media_title == "Dinosaur Rawr"

    def test_valid_timing_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "2024-01-31_16-32-37"
        media_type = ContentType.TV.value
        txt_file = f"{self.raw_folder}{txt_file_name}.txt"
        mp4_file = txt_file.replace('.txt', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(media_type, txt_file_path, pathlib.Path(self.raw_folder).resolve(),
                                                 sub_clips, error_log)
        assert len(error_log) == 0
        for index, sub_clip in enumerate(sub_clips):
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0

        assert sub_clips[
                   0].source_file_path == f"{self.raw_folder}2024-01-31_16-32-37.mp4"
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "a"
        assert sub_clips[
                   1].source_file_path == f"{self.raw_folder}2024-01-31_16-32-37.mp4"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "b"
        assert sub_clips[
                   2].source_file_path == f"{self.raw_folder}2024-01-31_16-32-37.mp4"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "c"
        assert sub_clips[
                   3].source_file_path == f"{self.raw_folder}2024-01-31_16-32-37.mp4"
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "d"
        assert sub_clips[
                   4].source_file_path == f"{self.raw_folder}2024-01-31_16-32-37.mp4"
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "e"

    def test_already_exists_mp4_txt_file(self):
        error_log = []
        sub_clips = []
        txt_file_name = "2024-01-31_16-32-36_already_exists"
        media_type = ContentType.TV.value

        with DatabaseHandler() as db_connection:
            media_folder_path = db_connection.get_media_folder_path_from_type(media_type)
        txt_file = f"{self.raw_folder}{txt_file_name}.txt"
        mp4_file = txt_file.replace('.txt', '.mp4')
        txt_file_path = pathlib.Path(txt_file).resolve()
        mp4_file_path = pathlib.Path(mp4_file).resolve()

        mp4_splitter.get_sub_clips_from_txt_file(media_type, txt_file_path, pathlib.Path(self.raw_folder).resolve(),
                                                 sub_clips, error_log)

        assert len(error_log) == 0
        for sub_clip in sub_clips:
            error_log.extend(sub_clip.error_log)
        # assert type(cmd_list) is list
        # assert len(cmd_list) == 5
        print(error_log)
        assert len(error_log) == 3

        assert "File already exists" == error_log[0].get("message")
        assert "Hilda - s4e8.mp4" == error_log[0].get("value")

        assert "Errors occurred while parsing line" == error_log[1].get("message")
        assert "Hilda,episode 2,4,8,47:26,1:02:10" == error_log[1].get("value")

        assert "Failing line index" == error_log[2].get("message")
        assert 3 == error_log[2].get("value")
        # print(len(sub_clips))
        # assert len(sub_clips) == 4
        for index, sub_clip in enumerate(sub_clips):
            if index == 3:
                continue
            assert txt_file_name in sub_clip.source_file_path
            assert self.raw_folder in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0

        assert sub_clips[
                   0].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36_already_exists.mp4"
        assert sub_clips[
                   0].destination_file_path == f"{self.raw_folder}Hilda/Hilda - s2e1.mp4"
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert sub_clips[
                   1].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36_already_exists.mp4"
        assert sub_clips[
                   1].destination_file_path == f"{self.raw_folder}Hilda/Hilda - s3e1.mp4"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert sub_clips[
                   2].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36_already_exists.mp4"
        assert sub_clips[
                   2].destination_file_path == f"{self.raw_folder}Hilda/Hilda - s4e7.mp4"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"

        assert sub_clips[3].error_log
        assert len(sub_clips[3].error_log) == 3
        assert sub_clips[3].error_log[0] == {'message': 'File already exists', 'value': 'Hilda - s4e8.mp4'}

        assert sub_clips[
                   4].source_file_path == f"{self.raw_folder}2024-01-31_16-32-36_already_exists.mp4"
        assert sub_clips[
                   4].destination_file_path == f"{self.raw_folder}Hilda/Hilda - s2e3.mp4"
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "episode 1"
