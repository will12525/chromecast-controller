import pathlib
from unittest import TestCase
import mp4_splitter

EDITOR_RAW_FOLDER = "C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/"
OUTPUT_PATH = "../media_folder_modify/output"


class Test(TestCase):
    def test_splitter_split_txt_file_content(self):
        # subclip_metadata_str = "1:20:47,1:40:43"
        # subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        # # print(subclip_metadata)
        # assert subclip_metadata.start_time == 4847
        # assert subclip_metadata.end_time == 6043
        #
        # subclip_metadata_str = "1,1:20:47,1:40:43"
        # subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        # assert subclip_metadata.start_time == 4847
        # assert subclip_metadata.end_time == 6043
        # assert subclip_metadata.episode_index == 1
        #
        # subclip_metadata_str = "2,1,1:20:47,1:40:43"
        # subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        # assert subclip_metadata.start_time == 4847
        # assert subclip_metadata.end_time == 6043
        # assert subclip_metadata.episode_index == 1
        # assert subclip_metadata.season_index == 2
        #
        # subclip_metadata_str = "episode 1,2,1,1:20:47,1:40:43"
        # subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        # assert subclip_metadata.start_time == 4847
        # assert subclip_metadata.end_time == 6043
        # assert subclip_metadata.episode_index == 1
        # assert subclip_metadata.season_index == 2
        # assert subclip_metadata.media_title == "episode 1"

        subclip_metadata_str = "Hilda,episode 1,2,1,1:20:47,1:40:43"
        subclip_metadata = mp4_splitter.SubclipMetadata(subclip_metadata_str)
        assert subclip_metadata.start_time == 4847
        assert subclip_metadata.end_time == 6043
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
        subclips = mp4_splitter.convert_txt_file_content(txt_file_content)
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
        subclips = mp4_splitter.convert_txt_file_content(txt_file_content)
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
        subclips = mp4_splitter.convert_txt_file_content(txt_file_content)
        assert len(subclips) == 0

    def test_validate_editor_cmd_list(self):
        txt_file_name = "2024-01-31_16-32-36"
        txt_process_file = f"{EDITOR_RAW_FOLDER}{txt_file_name}.txt"
        text_path = pathlib.Path(txt_process_file).resolve()
        mp4_process_file = txt_process_file.replace('.txt', '.mp4')
        video_path = pathlib.Path(mp4_process_file).resolve()
        assert text_path
        assert video_path

        time_lines = mp4_splitter.load_txt_file(text_path)
        assert time_lines
        sub_clips = mp4_splitter.convert_txt_file_content(time_lines)
        cmd_list = mp4_splitter.get_cmd_list(pathlib.Path(OUTPUT_PATH).resolve(), sub_clips,
                                             mp4_process_file, video_path)
        assert cmd_list
        assert 5 == len(cmd_list)

        current_index = mp4_splitter.ALPHANUMERIC_INDEX_A
        for cmd in cmd_list:
            # print(cmd)
            assert 6 == len(cmd)
            assert cmd[0] == mp4_splitter.SPLITTER_BASH_CMD
            assert cmd[
                       1] == 'C:/Users/lawrencew/PycharmProjects/chromecast-controller/editor_raw_files/2024-01-31_16-32-36.mp4'

            current_index += 1
        # print(cmd_list)
