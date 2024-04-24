import json
import pathlib
import time
from unittest import TestCase
import mp4_splitter
import config_file_handler
import __init__

EDITOR_RAW_FOLDER = "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/"
OUTPUT_PATH = "../media_folder_modify/output"
DESTINATION_DIR = "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/test_destination_dir"


class Test(TestCase):
    def test_splitter_split_txt_file_content(self):
        subclip_metadata_str = "1:20:47,1:40:43"
        subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043

        subclip_metadata_str = "Hilda,episode 1,2,1,1:20:47,1:40:43"
        subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043
        assert subclip_metadata.episode_index == 1
        assert subclip_metadata.season_index == 2
        assert subclip_metadata.media_title == "episode 1"
        assert subclip_metadata.playlist_title == "Hilda"

    def test_splitter_remove_quotes(self):
        subclip_metadata_str = 'Hilda,"episode 1",2,1,1:20:47,1:40:43'
        subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043
        assert subclip_metadata.episode_index == 1
        assert subclip_metadata.season_index == 2
        assert subclip_metadata.media_title == "episode 1"
        assert subclip_metadata.playlist_title == "Hilda"

        # subclip_metadata.set_cmd_metadata()

        print(subclip_metadata.media_title)

    def test_validate_editor_txt_file(self):
        txt_file_content = [
            "Hilda,episode name,2,1,7,13:43",
            'Hilda,"episode another name",2,1,13:49,29:33',
            "Hilda,episode name,2,1,30:03,46:32",
            "Hilda,episode 2,2,2,47:26,1:02:10",
            "Hilda,episode 1,2,1,1:02:43,1:20:13"
        ]
        subclips, errors = mp4_splitter.get_sub_clips_as_objs(txt_file_content)
        # print(json.dumps(subclips, indent=4))

        print(subclips)
        print(len(subclips))
        assert len(subclips) == len(txt_file_content)
        assert len(errors) == 0

        for subclip in subclips:
            print(subclip.media_title)

    def test_validate_editor_txt_file_times(self):
        txt_file_content = [
            "7,13:43",
            "13:49,29:33",
            "30:03,46:32",
            "47:26,1:02:10",
            "1:02:43,1:20:13"
        ]
        subclips, errors = mp4_splitter.get_sub_clips_as_objs(txt_file_content)
        print(len(subclips))
        assert len(subclips) == len(txt_file_content)
        assert len(errors) == 0

    def test_validate_editor_txt_file_invalid(self):
        txt_file_content = [
            "7,13:43",
            "1,13:49,29:33",
            "2,1,30:03,46:32",
            "episode 1,2,1,47:26,1:02:10",
            "Hilda,episode 1,hello,1,1:02:43,1:20:13"
        ]
        # with self.assertRaises(ValueError) as context:
        subclips, errors = mp4_splitter.get_sub_clips_as_objs(txt_file_content)
        # print(subclips)
        # print(json.dumps(errors, indent=4))
        assert 1 == len(subclips)
        assert 4 == len(errors)
        for subclip in subclips:
            assert not subclip.playlist_title
            assert not subclip.media_title
            assert not subclip.season_index
            assert not subclip.episode_index
            assert 7 == subclip.start_time
            assert 823 == subclip.end_time

        assert errors[0].get("message") == "Missing content"
        assert errors[0].get("line_index") == 1
        assert errors[1].get("message") == "Missing content"
        assert errors[1].get("line_index") == 2
        assert errors[2].get("message") == "Missing content"
        assert errors[2].get("line_index") == 3
        assert errors[3].get("message") == "Values not int"
        assert errors[3].get("line_index") == 4

    def test_load_txt_file_content(self):
        txt_file_name = "2024-01-31_16-32-36.txt"
        selected_txt_file_path = pathlib.Path(f"{EDITOR_RAW_FOLDER}{txt_file_name}").resolve()
        print(config_file_handler.load_txt_file_content(selected_txt_file_path))

    def test_validate_editor_cmd_list(self):
        txt_file_name = "2024-01-31_16-32-36.txt"
        txt_process_file = f"{EDITOR_RAW_FOLDER}{txt_file_name}"
        text_path = pathlib.Path(txt_process_file).resolve()
        mp4_process_file = txt_process_file.replace('.txt', '.mp4')
        video_path = pathlib.Path(mp4_process_file).resolve()
        assert text_path
        assert video_path

        time_lines = config_file_handler.load_txt_file_content(text_path)
        # print(time_lines)
        # print(''.join(time_lines))
        assert time_lines
        sub_clips, errors = mp4_splitter.get_sub_clips_as_objs(time_lines)
        # cmd_list = mp4_splitter.get_cmd_list(sub_clips, mp4_process_file, pathlib.Path(OUTPUT_PATH).resolve())
        mp4_splitter.get_cmd_list(sub_clips, mp4_process_file, pathlib.Path(OUTPUT_PATH).resolve())
        # assert cmd_list
        print(sub_clips[0])
        assert 5 == len(sub_clips)
        assert 0 == len(errors)

        current_index = mp4_splitter.ALPHANUMERIC_INDEX_A
        for sub_clip in sub_clips:
            assert type(sub_clip.media_title) is str
            assert type(sub_clip.start_time) is int
            assert type(sub_clip.end_time) is int
            assert sub_clip.source_file_path == 'C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4'

            current_index += 1
        # print(cmd_list)

    def test_validate_editor_cmd_list_remove_quotes(self):
        txt_file_name = "2024-01-31_16-32-36_quotes.txt"
        txt_process_file = f"{EDITOR_RAW_FOLDER}{txt_file_name}"
        text_path = pathlib.Path(txt_process_file).resolve()
        mp4_process_file = txt_process_file.replace('.txt', '.mp4')
        video_path = pathlib.Path(mp4_process_file).resolve()
        assert text_path
        assert video_path

        time_lines = config_file_handler.load_txt_file_content(text_path)
        # print(time_lines)
        # print(''.join(time_lines))
        assert time_lines
        sub_clips, errors = mp4_splitter.get_sub_clips_as_objs(time_lines)
        # cmd_list = mp4_splitter.get_cmd_list(sub_clips, mp4_process_file, pathlib.Path(OUTPUT_PATH).resolve())
        mp4_splitter.get_cmd_list(sub_clips, mp4_process_file, pathlib.Path(OUTPUT_PATH).resolve())
        # assert cmd_list
        print(sub_clips[0])
        assert 5 == len(sub_clips)
        assert 0 == len(errors)

        current_index = mp4_splitter.ALPHANUMERIC_INDEX_A
        for sub_clip in sub_clips:
            assert type(sub_clip.media_title) is str
            assert type(sub_clip.start_time) is int
            assert type(sub_clip.end_time) is int
            assert sub_clip.source_file_path == 'C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36_quotes.mp4'
            assert '"' not in sub_clip.media_title
            current_index += 1
        # print(cmd_list)


class TestConvertTimestamp(TestCase):

    def test_invalid_timestamp_strings(self):
        negative_second = "1:02:-43"
        negative_minute = "1:-20:13"
        negative_hour = "-5:20:13"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.convert_timestamp(negative_second)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        assert data_dict.get("string") == negative_second
        assert str(data_dict.get("second")) in negative_second
        assert data_dict.get("message") == "Values less than 0"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.convert_timestamp(negative_minute)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        assert data_dict.get("string") == negative_minute
        assert str(data_dict.get("minute")) in negative_minute
        assert data_dict.get("message") == "Values less than 0"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.convert_timestamp(negative_hour)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        assert data_dict.get("string") == negative_hour
        assert str(data_dict.get("hour")) in negative_hour
        assert data_dict.get("message") == "Values less than 0"


class TestSubclipMetadata(TestCase):

    def test_invalid_timestamp_strings(self):
        invalid_end_minute_timestamp = "1:02:43,1:-20:13"
        invalid_end_second_timestamp = "1:02:43,1:20:-13"
        invalid_start_second_timestamp = "1:02:-43,1:20:13"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_end_minute_timestamp)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Values less than 0"
        assert data_dict.get("hour") == 1
        assert data_dict.get("minute") == -20
        assert data_dict.get("second") == 13

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_end_second_timestamp)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Values less than 0"
        assert data_dict.get("hour") == 1
        assert data_dict.get("minute") == 20
        assert data_dict.get("second") == -13

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_start_second_timestamp)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Values less than 0"
        assert data_dict.get("hour") == 1
        assert data_dict.get("minute") == 2
        assert data_dict.get("second") == -43

    def test_valid_full_data_strings(self):
        valid_data_set = "Hilda,Running Up That Hill,2,1,7,13:43"
        subclip_metadata = mp4_splitter.SubclipMetadata(valid_data_set)
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

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_negative_end_minute_timestamp)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        print(data_dict)

        assert data_dict.get("message") == "Values less than 0"
        assert data_dict.get("string") == "1:-20:13"
        assert data_dict.get("hour") == 1
        assert data_dict.get("minute") == -20
        assert data_dict.get("second") == 13

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_end_minute_is_str_timestamp)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        print(data_dict)
        assert data_dict.get("message") == "Values not int"
        assert data_dict.get("hour") == 1
        assert data_dict.get("minute") == "HELLO"
        assert data_dict.get("second") == "13"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_missing_end_minute_timestamp)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Missing timestamp value"
        assert data_dict.get("hour") == "1"
        assert data_dict.get("minute") == ""
        assert data_dict.get("second") == "13"

    def test_invalid_start_second(self):
        invalid_negative_start_second_timestamp = "Hilda,Running Up That Hill,1,1,13:-49,29:33"
        invalid_start_second_is_str_timestamp = "Hilda,Running Up That Hill,1,1,13:HELLO,29:33"
        invalid_missing_start_second_timestamp = "Hilda,Running Up That Hill,1,1,13:,29:33"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_negative_start_second_timestamp)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Values less than 0"
        assert data_dict.get("string") == "13:-49"
        assert data_dict.get("hour") == 0
        assert data_dict.get("minute") == 13
        assert data_dict.get("second") == -49

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_start_second_is_str_timestamp)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Values not int"
        assert data_dict.get("hour") == 0
        assert data_dict.get("minute") == 13
        assert data_dict.get("second") == "HELLO"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_missing_start_second_timestamp)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Missing timestamp value"
        assert data_dict.get("hour") == 0
        assert data_dict.get("minute") == "13"
        assert data_dict.get("second") == ""

    def test_invalid_episode_index(self):
        invalid_negative_episode_index = "Hilda,Running Up That Hill,1,-1,30:03,46:32"
        invalid_episode_index_is_str = "Hilda,Running Up That Hill,1,HELLO,13:49,29:33"
        invalid_missing_episode_index = "Hilda,Running Up That Hill,1,,13:48,29:33"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_negative_episode_index)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Values less than 0"
        assert data_dict.get("string") == invalid_negative_episode_index
        assert data_dict.get("episode_index") == -1

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_episode_index_is_str)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Values not int"
        assert data_dict.get("string") == invalid_episode_index_is_str
        assert data_dict.get("episode_index") == "HELLO"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_missing_episode_index)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Missing episode index"
        assert data_dict.get("string") == invalid_missing_episode_index

    def test_invalid_season_index(self):
        invalid_negative_season_index = "Hilda,Running Up That Hill,-1,1,30:03,46:32"
        invalid_season_index_is_str = "Hilda,Running Up That Hill,HI THERE,198,13:49,29:33"
        invalid_missing_season_index = "Hilda,Running Up That Hill,,287,13:48,29:33"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_negative_season_index)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Values less than 0"
        assert data_dict.get("string") == invalid_negative_season_index
        assert data_dict.get("season_index") == -1

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_season_index_is_str)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Values not int"
        assert data_dict.get("string") == invalid_season_index_is_str
        assert data_dict.get("season_index") == "HI THERE"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_missing_season_index)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Missing season index"
        assert data_dict.get("string") == invalid_missing_season_index

    def test_invalid_media_title(self):
        invalid_missing_media_title = "Hilda,,7,287,13:48,29:33"
        invalid_characters_in_media_title = "Hilda,Running\/*+ Up That Hill,7,287,13:48,29:33"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_missing_media_title)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Missing media title"
        assert data_dict.get("string") == invalid_missing_media_title

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_characters_in_media_title)
        data_dict = context.exception.args[0]
        print(data_dict)
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Media title invalid characters found"
        assert data_dict.get("string") == invalid_characters_in_media_title
        assert data_dict.get("media_title") == ""
        assert data_dict.get("invalids") == "(/)"

    def test_invalid_playlist_title(self):
        invalid_missing_playlist_title = ",Running Up That Hill,7,287,13:48,29:33"
        invalid_characters_in_playlist_title = "Hilda//*+,Running Up That Hill,7,287,13:48,29:33"

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_missing_playlist_title)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Missing playlist title"
        assert data_dict.get("string") == invalid_missing_playlist_title

        with self.assertRaises(ValueError) as context:
            mp4_splitter.SubclipMetadata(invalid_characters_in_playlist_title)
        data_dict = context.exception.args[0]
        assert type(data_dict) is dict
        assert data_dict.get("message") == "Media title invalid characters found"
        assert data_dict.get("string") == invalid_characters_in_playlist_title
        assert data_dict.get("playlist_title") == ""
        assert data_dict.get("invalids") == "(/, /)"


class TestEditor(TestCase):
    OUTPUT_PATH = "../media_folder_modify/output"
    EDITOR_RAW_FOLDER = "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/"
    EDITOR_METADATA_FILE = f"{EDITOR_RAW_FOLDER}editor_metadata.json"
    editor_processor = mp4_splitter.SubclipProcessHandler()

    def test_editor_process_txt_file_error_invalid_file(self):
        editor_metadata = {
            'txt_file_name': "2024hi-01-31_16-32-36.txt"
        }
        with self.assertRaises(ValueError) as context:
            mp4_splitter.editor_process_txt_file(self.EDITOR_RAW_FOLDER, editor_metadata, self.OUTPUT_PATH,
                                                 self.editor_processor)
        error_dict = context.exception.args[0]
        assert type(error_dict) is dict
        assert "Text file empty" == error_dict.get("message")
        print(error_dict)
        assert editor_metadata.get("txt_file_name") in error_dict.get("file_name")

    def test_editor_process_txt_file_error_missing_mp4(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_no_mp4.txt"
        }
        with self.assertRaises(FileNotFoundError) as context:
            mp4_splitter.editor_process_txt_file(self.EDITOR_RAW_FOLDER, editor_metadata, self.OUTPUT_PATH,
                                                 self.editor_processor)
        error_dict = context.exception.args[0]
        print(error_dict)
        assert type(error_dict) is dict
        assert "Missing file" == error_dict.get("message")
        assert "chromecast-controller/editor_raw_files/2024-01-31_16-32-36_no_mp4.mp4" in error_dict.get(
            "file_name")

    def test_editor_process_txt_file_error_empty_file(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_empty.txt"
        }
        with self.assertRaises(ValueError) as context:
            mp4_splitter.editor_process_txt_file(self.EDITOR_RAW_FOLDER, editor_metadata,
                                                 self.OUTPUT_PATH, self.editor_processor)
        error_dict = context.exception.args[0]
        print(error_dict)
        assert type(error_dict) is dict
        assert "Text file empty" == error_dict.get("message")
        assert editor_metadata.get("txt_file_name") in error_dict.get("file_name")

    def test_editor_process_txt_file_error_invalid_file_content(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_invalid.txt"
        }
        # with self.assertRaises(ValueError) as context:
        errors = mp4_splitter.editor_process_txt_file(self.EDITOR_RAW_FOLDER,
                                                      editor_metadata, self.OUTPUT_PATH, self.editor_processor)
        # print(json.dumps(errors, indent=4))
        assert len(errors) == 1
        error_dict = errors[0]
        # error_dict = context.exception.args[0]
        assert type(error_dict) is dict
        assert "Values less than 0" == error_dict.get("message")
        assert "13:-3" == error_dict.get("string")
        assert 0 == error_dict.get("hour")
        assert 13 == error_dict.get("minute")
        assert -3 == error_dict.get("second")
        assert 0 == error_dict.get("line_index")
        assert editor_metadata.get("txt_file_name") in error_dict.get("file_name")

    def test_editor_process_txt_file_name(self):
        __init__.patch_extract_subclip(self)
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36.txt"
        }
        mp4_splitter.editor_process_txt_file(self.EDITOR_RAW_FOLDER, editor_metadata,
                                             pathlib.Path(self.OUTPUT_PATH).resolve(), self.editor_processor)
        new_editor_metadata = mp4_splitter.get_editor_metadata(self.EDITOR_RAW_FOLDER, self.editor_processor)
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
        assert 'process_time' in process_metadata
        assert type(process_metadata.get('process_time')) is str
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

        editor_metadata = mp4_splitter.get_editor_metadata(self.EDITOR_RAW_FOLDER, self.editor_processor)
        print(editor_metadata)
        print(json.dumps(editor_metadata, indent=4))

    def test_editor_process_txt_file(self):
        __init__.patch_extract_subclip(self)
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36.txt"
        }

        mp4_splitter.editor_process_txt_file(self.EDITOR_RAW_FOLDER, editor_metadata,
                                             pathlib.Path(self.OUTPUT_PATH).resolve(), self.editor_processor)
        # time.sleep(2)
        print(self.editor_processor.get_metadata())
        # time.sleep(10)
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-38.txt"
        }
        mp4_splitter.editor_process_txt_file(self.EDITOR_RAW_FOLDER, editor_metadata,
                                             pathlib.Path(self.OUTPUT_PATH).resolve(), self.editor_processor)
        # time.sleep(10)
        print(self.editor_processor.get_metadata())
        for i in range(20):
            print(json.dumps(self.editor_processor.get_metadata(), indent=4))
            time.sleep(1)
        # error_code = self.backend_handler.editor_process_txt_file(editor_metadata,
        #                                                           pathlib.Path(self.OUTPUT_PATH).resolve())

    def test_valid_txt_file(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36.txt"
        }
        sub_clips, errors = mp4_splitter.editor_validate_txt_file(self.EDITOR_RAW_FOLDER, editor_metadata)
        assert len(errors) == 0

    def test_empty_txt_file(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_empty.txt"
        }
        with self.assertRaises(ValueError) as context:
            sub_clips, errors = mp4_splitter.editor_validate_txt_file(self.EDITOR_RAW_FOLDER, editor_metadata)
        error_dict = context.exception.args[0]
        print(error_dict)
        assert type(error_dict) is dict
        assert "Text file empty" == error_dict.get("message")
        assert not error_dict.get("string")
        assert not error_dict.get("hour")
        assert not error_dict.get("minute")
        assert not error_dict.get("second")
        assert not error_dict.get("line_index")
        assert editor_metadata.get("txt_file_name") in error_dict.get("file_name")

    def test_invalid_txt_file(self):
        editor_metadata = {
            'txt_file_name': "2024-01-31_16-32-36_invalid.txt"
        }

        # with self.assertRaises(ValueError) as context:
        sub_clips, errors = mp4_splitter.editor_validate_txt_file(self.EDITOR_RAW_FOLDER, editor_metadata)
        # error_dict = context.exception.args[0]
        # print(error_dict)
        print(json.dumps(errors, indent=4))
        assert len(errors) == 1
        error_dict = errors[0]
        assert type(error_dict) is dict
        assert "Values less than 0" == error_dict.get("message")
        assert "13:-3" == error_dict.get("string")
        assert 0 == error_dict.get("hour")
        assert 13 == error_dict.get("minute")
        assert -3 == error_dict.get("second")
        assert 0 == error_dict.get("line_index")
        assert editor_metadata.get("txt_file_name") in error_dict.get("file_name")


class TestGetCMDList(TestCase):

    def test_get_cmd_list(self):
        txt_file_name = "2024-01-31_16-32-36"
        subclip_file = f"{EDITOR_RAW_FOLDER}{txt_file_name}.txt"
        sub_clips, errors = mp4_splitter.get_sub_clips_from_txt_file(subclip_file)
        destination_dir = pathlib.Path(DESTINATION_DIR).resolve()
        # cmd_list = mp4_splitter.get_cmd_list(sub_clips, subclip_file, destination_dir)
        mp4_splitter.get_cmd_list(sub_clips, subclip_file, destination_dir)
        assert len(errors) == 0
        for sub_clip in sub_clips:
            assert txt_file_name in sub_clip.source_file_path
            assert EDITOR_RAW_FOLDER in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0
        assert sub_clips[
                   0].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert sub_clips[
                   1].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert sub_clips[
                   2].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"
        assert sub_clips[
                   3].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "episode 2"
        assert sub_clips[
                   4].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "episode 1"


class TestProcessSubclipFile(TestCase):

    def test_valid_full_content_txt_file(self):
        txt_file_name = "2024-01-31_16-32-36"
        txt_file_str_path = f"{EDITOR_RAW_FOLDER}{txt_file_name}.txt"
        sub_clips, errors = mp4_splitter.get_sub_clips_from_txt_file(txt_file_str_path)
        mp4_splitter.get_cmd_list(sub_clips, txt_file_str_path)
        # assert type(cmd_list) is list
        # assert len(cmd_list) == 5
        assert len(errors) == 0
        for sub_clip in sub_clips:
            assert txt_file_name in sub_clip.source_file_path
            assert EDITOR_RAW_FOLDER in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0

        assert sub_clips[
                   0].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert sub_clips[
                   1].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert sub_clips[
                   2].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"
        assert sub_clips[
                   3].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "episode 2"
        assert sub_clips[
                   4].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "episode 1"

    def test_valid_timing_txt_file(self):
        txt_file_name = "2024-01-31_16-32-37"
        txt_file_str_path = f"{EDITOR_RAW_FOLDER}{txt_file_name}.txt"
        sub_clips, errors = mp4_splitter.get_sub_clips_from_txt_file(txt_file_str_path)
        mp4_splitter.get_cmd_list(sub_clips, txt_file_str_path)
        assert len(errors) == 0
        for index, sub_clip in enumerate(sub_clips):
            assert txt_file_name in sub_clip.source_file_path
            assert EDITOR_RAW_FOLDER in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0

        assert sub_clips[
                   0].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "a"
        assert sub_clips[
                   1].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "b"
        assert sub_clips[
                   2].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "c"
        assert sub_clips[
                   3].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert sub_clips[3].start_time == 2846
        assert sub_clips[3].end_time == 3730
        assert sub_clips[3].media_title == "d"
        assert sub_clips[
                   4].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert sub_clips[4].start_time == 3763
        assert sub_clips[4].end_time == 4813
        assert sub_clips[4].media_title == "e"

    def test_already_exists_mp4_txt_file(self):
        txt_file_name = "2024-01-31_16-32-36_already_exists"
        txt_file_str_path = f"{EDITOR_RAW_FOLDER}{txt_file_name}.txt"
        sub_clips, errors = mp4_splitter.get_sub_clips_from_txt_file(txt_file_str_path)
        assert len(errors) == 0
        mp4_splitter.get_cmd_list(sub_clips, txt_file_str_path, error_log=errors)
        for sub_clip in sub_clips:
            print(sub_clip.destination_file_path)
        # assert type(cmd_list) is list
        # assert len(cmd_list) == 5
        print(errors)
        assert len(errors) == 1
        # print(len(sub_clips))
        # assert len(sub_clips) == 4
        for index, sub_clip in enumerate(sub_clips):
            assert txt_file_name in sub_clip.source_file_path
            assert EDITOR_RAW_FOLDER in sub_clip.source_file_path
            assert type(int(sub_clip.start_time)) is int
            assert type(int(sub_clip.end_time)) is int
            assert int(sub_clip.start_time) >= 0
            assert int(sub_clip.end_time) >= 0

        assert sub_clips[
                   0].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36_already_exists.mp4"
        assert sub_clips[
                   0].destination_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/Hilda/Hilda - s2e1.mp4"
        assert sub_clips[0].start_time == 7
        assert sub_clips[0].end_time == 823
        assert sub_clips[0].media_title == "episode name"
        assert sub_clips[
                   1].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36_already_exists.mp4"
        assert sub_clips[
                   1].destination_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/Hilda/Hilda - s3e1.mp4"
        assert sub_clips[1].start_time == 829
        assert sub_clips[1].end_time == 1773
        assert sub_clips[1].media_title == "episode another name"
        assert sub_clips[
                   2].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36_already_exists.mp4"
        assert sub_clips[
                   2].destination_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/Hilda/Hilda - s4e7.mp4"
        assert sub_clips[2].start_time == 1803
        assert sub_clips[2].end_time == 2792
        assert sub_clips[2].media_title == "episode name"
        assert sub_clips[
                   3].source_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36_already_exists.mp4"
        assert sub_clips[
                   3].destination_file_path == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/Hilda/Hilda - s2e3.mp4"
        assert sub_clips[3].start_time == 3763
        assert sub_clips[3].end_time == 4813
        assert sub_clips[3].media_title == "episode 1"
