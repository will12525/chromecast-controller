import argparse
import subprocess
import time
import shutil
import os
# import tkinter as tk
# from tkinter import filedialog

import pathlib

# from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

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

DEFAULT_MP4_FILE = "raw_file/2022-06-12_06-22-06.mp4"
DEFAULT_EPISODE_START_INDEX = 0
DEFAULT_SEASON_START_INDEX = None
DEFAULT_TV_SHOW_NAME = "abc"


def quit_program(message):
    print(message)
    input("Press enter to quit...")
    quit()


def convert_timestamp(timestamp_str):
    try:
        colon_count = timestamp_str.count(":")
        h = m = s = 0
        if colon_count == 0:
            (s,) = timestamp_str.split(':')
        elif colon_count == 1:
            m, s = timestamp_str.split(':')
        elif colon_count == 2:
            h, m, s = timestamp_str.split(':')
        else:
            print(f"To many colons found: {colon_count}")
            raise ValueError

        return int(h) * 3600 + int(m) * 60 + int(s)
    except ValueError as e:
        quit_program(f"Error encountered reading timestamp: {timestamp_str}")


def run_image_processor_v2(mp4_process_file, tv_show_name, season_index, episode_start_index):
    txt_process_file = mp4_process_file.replace('.mp4', '.txt')
    time_lines = []
    times = []
    alphanumeric_index_a = 97
    video_path = pathlib.Path(mp4_process_file).resolve()
    text_path = pathlib.Path(txt_process_file).resolve()
    output_path = video_path.parent / tv_show_name
    print(video_path, output_path)
    # quit()
    if season_index:
        output_path = output_path / f'S{season_index}'

    if not text_path.is_file():
        quit_program(f"Missing times txt file: {txt_process_file}")
    else:
        with open(text_path) as f:
            time_lines = f.readlines()

    if len(time_lines) < 1:
        quit_program(f"Only 1 time split found in: {text_path}")
    else:
        print(f"Processing time txt file: {text_path}")
        times = []
        for index, time_str in enumerate(time_lines):
            time_data_list = time_str.split('-')
            if len(time_data_list) != 2:
                quit_program(f"Malformed time data: line {index}, {time_str}, Path: {text_path}: ")
            times.append((convert_timestamp(time_data_list[0]), convert_timestamp(time_data_list[1])))

    if video_path.is_file():
        for time_data in times:
            file_index = f'E{episode_start_index}'
            if not season_index:
                file_index = chr(alphanumeric_index_a + episode_start_index)
            episode_path = output_path / f'{file_index}_{video_path.stem}.mp4'

            # if episode_path.exists():
            #     usr_input = ""
            #     if ASK_QUESTION:
            #         usr_input = input(f'File exists: {episode_path}.\nReplace? (Y/N) N: ')
            #     if usr_input in ['n', 'N', 'No']:
            #         continue
            #     elif usr_input == 'q':
            #         quit_program(f'User provided: {usr_input}')
            #     else:
            #         pass

            print(f"Splitting: {time_data[0]}:{time_data[1]}, {mp4_process_file} -> {episode_path}")
            print(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            # print(type(episode_path))
            command_list = ["./splitter.sh", str(mp4_process_file), str(episode_path), str(time_data[0]),
                            str(time_data[1]), str(file_index)]
            print(command_list)
            subprocess.run(command_list, check=True, text=True)
            # ffmpeg_extract_subclip(mp4_process_file, time_data[0], time_data[1], targetname=episode_path)

            episode_start_index += 1


# def main():
#     episode_start_index = DEFAULT_EPISODE_START_INDEX
#     season_start_index = DEFAULT_SEASON_START_INDEX
#     mp4_file = DEFAULT_MP4_FILE
#     tv_show_name = DEFAULT_TV_SHOW_NAME
#
#     if ASK_QUESTION:
#         user_episode_start_index = input(
#             f'Episode start index: e.g. E1.mp4, E2.mp4, ... default < {episode_start_index} >: ')
#         if user_episode_start_index:
#             try:
#                 episode_start_index = int(user_episode_start_index)
#             except ValueError as e:
#                 quit_program("Input provided not int. 1, 2, 3, etc...")
#
#         user_season_start_index = input(f'Season start index: e.g. S1.mp4, S2, ... default < {season_start_index} >: ')
#         if user_season_start_index:
#             try:
#                 season_start_index = int(user_season_start_index)
#             except ValueError as e:
#                 quit_program("Input provided not int. 1, 2, 3, etc...")
#
#         user_tv_show_name = input(f'Tv show name: e.g. Hilda, House, ... default < {tv_show_name} >: ')
#         if user_tv_show_name and len(user_tv_show_name) > 1:
#             tv_show_name = user_tv_show_name
#
#         root = tk.Tk()
#         root.withdraw()
#         mp4_file = filedialog.askopenfilename(title="Select an video file", filetypes=[("MP4", "*.mp4")])
#
#     run_image_processor_v2(mp4_file, tv_show_name, season_start_index, episode_start_index)


if __name__ == "__main__":
    dirpath = "abc"
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)
    # Old way
    # main()

    # CLI Way
    parser = argparse.ArgumentParser(description='Splits mp4 files given a mp4 file with timestamp file')
    # parser.add_argument('-f', '--file', help='File to be split', required=True, dest='input_file', type=str)
    parser.add_argument('-f', help='File to be split', default=DEFAULT_MP4_FILE, dest='input_file', type=str)
    args = parser.parse_args()
    if args.input_file:
        # print(args.input_file)
        run_image_processor_v2(args.input_file, DEFAULT_TV_SHOW_NAME, None, 0)
