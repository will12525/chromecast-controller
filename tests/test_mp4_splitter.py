import json
import pathlib
from unittest import TestCase
import mp4_splitter

EDITOR_RAW_FOLDER = "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/"
OUTPUT_PATH = "../media_folder_modify/output"
DESTINATION_DIR = "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/test_destination_dir"


class Test(TestCase):
    def test_splitter_split_txt_file_content(self):
        subclip_metadata_str = "1:20:47,1:40:43"
        subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        assert subclip_metadata.start_time == str(4847)
        assert subclip_metadata.end_time == str(6043)

        subclip_metadata_str = "Hilda,episode 1,2,1,1:20:47,1:40:43"
        subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        assert subclip_metadata.start_time == str(4847)
        assert subclip_metadata.end_time == str(6043)
        assert subclip_metadata.episode_index == 1
        assert subclip_metadata.season_index == 2
        assert subclip_metadata.media_title == "episode 1"
        assert subclip_metadata.playlist_title == "Hilda"

    def test_validate_editor_txt_file(self):
        txt_file_content = [
            "Hilda,episode name,2,1,7,13:43",
            "Hilda,episode another name,2,1,13:49,29:33",
            "Hilda,episode name,2,1,30:03,46:32",
            "Hilda,episode 2,2,2,47:26,1:02:10",
            "Hilda,episode 1,2,1,1:02:43,1:20:13"
        ]
        subclips = mp4_splitter.get_subclips_as_objs(txt_file_content)
        print(subclips)
        print(len(subclips))
        assert len(subclips) == len(txt_file_content)

    def test_validate_editor_txt_file_times(self):
        txt_file_content = [
            "7,13:43",
            "13:49,29:33",
            "30:03,46:32",
            "47:26,1:02:10",
            "1:02:43,1:20:13"
        ]
        subclips = mp4_splitter.get_subclips_as_objs(txt_file_content)
        print(len(subclips))
        assert len(subclips) == len(txt_file_content)

    def test_validate_editor_txt_file_invalid(self):
        txt_file_content = [
            "7,13:43",
            "1,13:49,29:33",
            "2,1,30:03,46:32",
            "episode 1,2,1,47:26,1:02:10",
            "Hilda,episode 1,hello,1,1:02:43,1:20:13"
        ]
        with self.assertRaises(ValueError) as context:
            mp4_splitter.get_subclips_as_objs(txt_file_content)
        assert type(context.exception.args[0]) is dict
        assert context.exception.args[0].get("message") == "Missing content"
        assert context.exception.args[0].get("string") == "1,13:49,29:33"
        assert context.exception.args[0].get("line_index") == 1

    def test_validate_editor_cmd_list(self):
        txt_file_name = "2024-01-31_16-32-36"
        txt_process_file = f"{EDITOR_RAW_FOLDER}{txt_file_name}.txt"
        text_path = pathlib.Path(txt_process_file).resolve()
        mp4_process_file = txt_process_file.replace('.txt', '.mp4')
        video_path = pathlib.Path(mp4_process_file).resolve()
        assert text_path
        assert video_path

        time_lines = mp4_splitter.get_txt_file_content(text_path)
        assert time_lines
        sub_clips = mp4_splitter.get_subclips_as_objs(time_lines)
        # cmd_list = mp4_splitter.get_cmd_list(sub_clips, mp4_process_file, pathlib.Path(OUTPUT_PATH).resolve())
        mp4_splitter.get_cmd_list(sub_clips, mp4_process_file, pathlib.Path(OUTPUT_PATH).resolve())
        # assert cmd_list
        assert 5 == len(sub_clips)

        current_index = mp4_splitter.ALPHANUMERIC_INDEX_A
        for sub_clip in sub_clips:
            cmd = sub_clip.get_cmd()
            print(cmd)
            assert 6 == len(cmd)
            assert cmd[0] == mp4_splitter.SPLITTER_BASH_CMD
            assert cmd[
                       1] == 'C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4'

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
        assert subclip_metadata.start_time == str(7)
        assert subclip_metadata.end_time == str(823)

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


class TestGetCMDList(TestCase):

    def test_get_cmd_list(self):
        txt_file_name = "2024-01-31_16-32-36"
        subclip_file = f"{EDITOR_RAW_FOLDER}{txt_file_name}.txt"
        sub_clips = mp4_splitter.get_sub_clips_from_txt_file(subclip_file)
        destination_dir = pathlib.Path(DESTINATION_DIR).resolve()
        # cmd_list = mp4_splitter.get_cmd_list(sub_clips, subclip_file, destination_dir)
        mp4_splitter.get_cmd_list(sub_clips, subclip_file, destination_dir)
        for sub_clip in sub_clips:
            cmd = sub_clip.get_cmd()
            assert type(cmd) is list
            assert len(cmd) == 6
            print(cmd)
            for argument in cmd:
                assert type(argument) is str
            assert cmd[0] == mp4_splitter.SPLITTER_BASH_CMD
            assert txt_file_name in cmd[1]
            assert EDITOR_RAW_FOLDER in cmd[1]
            assert type(int(cmd[3])) is int
            assert type(int(cmd[4])) is int
            assert int(cmd[3]) >= 0
            assert int(cmd[4]) >= 0
        cmd = sub_clips[0].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[3] == "7"
        assert cmd[4] == "823"
        assert cmd[5] == "episode name"
        cmd = sub_clips[1].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[3] == "829"
        assert cmd[4] == "1773"
        assert cmd[5] == "episode another name"
        cmd = sub_clips[2].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[3] == "1803"
        assert cmd[4] == "2792"
        assert cmd[5] == "episode name"
        cmd = sub_clips[3].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[3] == "2846"
        assert cmd[4] == "3730"
        assert cmd[5] == "episode 2"
        cmd = sub_clips[4].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[3] == "3763"
        assert cmd[4] == "4813"
        assert cmd[5] == "episode 1"


class TestProcessSubclipFile(TestCase):

    def test_valid_full_content_txt_file(self):
        txt_file_name = "2024-01-31_16-32-36"
        txt_file_str_path = f"{EDITOR_RAW_FOLDER}{txt_file_name}.txt"
        sub_clips = mp4_splitter.get_sub_clips_from_txt_file(txt_file_str_path)
        mp4_splitter.get_cmd_list(sub_clips, txt_file_str_path)
        # assert type(cmd_list) is list
        # assert len(cmd_list) == 5
        for sub_clip in sub_clips:
            cmd = sub_clip.get_cmd()
            assert type(cmd) is list
            assert len(cmd) == 6
            print(cmd)
            for argument in cmd:
                assert type(argument) is str
            assert cmd[0] == mp4_splitter.SPLITTER_BASH_CMD
            assert txt_file_name in cmd[1]
            assert EDITOR_RAW_FOLDER in cmd[1]
            assert type(int(cmd[3])) is int
            assert type(int(cmd[4])) is int
            assert int(cmd[3]) >= 0
            assert int(cmd[4]) >= 0

        cmd = sub_clips[0].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/Hilda/2/E1.mp4"
        assert cmd[3] == "7"
        assert cmd[4] == "823"
        assert cmd[5] == "episode name"
        cmd = sub_clips[1].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/Hilda/1/E1.mp4"
        assert cmd[3] == "829"
        assert cmd[4] == "1773"
        assert cmd[5] == "episode another name"
        cmd = sub_clips[2].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/Hilda/2/E1.mp4"
        assert cmd[3] == "1803"
        assert cmd[4] == "2792"
        assert cmd[5] == "episode name"
        cmd = sub_clips[3].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/Hilda/4/E8.mp4"
        assert cmd[3] == "2846"
        assert cmd[4] == "3730"
        assert cmd[5] == "episode 2"
        cmd = sub_clips[4].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4"
        assert cmd[2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/Hilda/2/E1.mp4"
        assert cmd[3] == "3763"
        assert cmd[4] == "4813"
        assert cmd[5] == "episode 1"

    def test_valid_timing_txt_file(self):
        txt_file_name = "2024-01-31_16-32-37"
        txt_file_str_path = f"{EDITOR_RAW_FOLDER}{txt_file_name}.txt"
        sub_clips = mp4_splitter.get_sub_clips_from_txt_file(txt_file_str_path)
        mp4_splitter.get_cmd_list(sub_clips, txt_file_str_path)
        for index, sub_clip in enumerate(sub_clips):
            cmd = sub_clip.get_cmd()
            assert type(cmd) is list
            assert len(cmd) == 6
            for argument in cmd:
                assert type(argument) is str
            assert cmd[0] == mp4_splitter.SPLITTER_BASH_CMD
            assert f"{cmd[5]}_{txt_file_name}" in cmd[2]
            assert txt_file_name in cmd[1]
            assert EDITOR_RAW_FOLDER in cmd[1]
            assert cmd[5] == chr(mp4_splitter.ALPHANUMERIC_INDEX_A + index)
            assert type(int(cmd[3])) is int
            assert type(int(cmd[4])) is int
            assert int(cmd[3]) >= 0
            assert int(cmd[4]) >= 0
        cmd = sub_clips[0].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert cmd[
                   2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/a_2024-01-31_16-32-37.mp4"
        assert cmd[3] == "7"
        assert cmd[4] == "823"
        assert cmd[5] == "a"
        cmd = sub_clips[1].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert cmd[
                   2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/b_2024-01-31_16-32-37.mp4"
        assert cmd[3] == "829"
        assert cmd[4] == "1773"
        assert cmd[5] == "b"
        cmd = sub_clips[2].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert cmd[
                   2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/c_2024-01-31_16-32-37.mp4"
        assert cmd[3] == "1803"
        assert cmd[4] == "2792"
        assert cmd[5] == "c"
        cmd = sub_clips[3].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert cmd[
                   2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/d_2024-01-31_16-32-37.mp4"
        assert cmd[3] == "2846"
        assert cmd[4] == "3730"
        assert cmd[5] == "d"
        cmd = sub_clips[4].get_cmd()
        assert cmd[
                   1] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-37.mp4"
        assert cmd[
                   2] == "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/e_2024-01-31_16-32-37.mp4"
        assert cmd[3] == "3763"
        assert cmd[4] == "4813"
        assert cmd[5] == "e"

# "C:\Users\lawrencew\PycharmProjects\mp4_splitter\raw_file\2022-06-12_06-22-06.mp4"
# "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2022-06-12_06-22-06.mp4"
