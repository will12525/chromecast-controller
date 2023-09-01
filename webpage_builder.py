import json
from enum import Enum
from flask import Flask, request, jsonify, redirect, url_for, current_app, render_template
from chromecast_handler import MediaURLBuilder, MyMediaDevice, ChromecastHandler, CommandList

import media_folder_metadata_handler

app = Flask(__name__)

SERVER_URL = "http://192.168.1.200:8000/"
SERVER_URL_TV_SHOWS = SERVER_URL + "tv_shows/"

device_button_list = [
    {"name": "connect", "value": "Connect",},
    {"name": "disconnect", "value": "Disconnect"}
]
media_controller_button_list = [
    {"name": "start", "value": "Start"},
    {"name": "pause", "value": "Pause"},
    {"name": "stop", "value": "Stop"},
    {"name": "play", "value": "Play"},
    {"name": "skip", "value": "Skip"}
]


url_builder = MediaURLBuilder()
chromecast_handler = ChromecastHandler()
chromecast_handler.start()
# chromecast_handler.connect_to_chromecast("Family Room TV")


previous_selected_tv_show = None
previous_selected_tv_show_season = None
previous_selected_tv_show_season_episode = None

tv_show_name_list = None

current_episode = ""

print("HELLO WORLD!")

path_type_strings = ["tv_show", "tv_show_season", "tv_show_season_episode"]
media_folder_path = "/media/hdd1/plex_media/tv_shows/"
media_folder_metadata = media_folder_metadata_handler.media_metadata_init(media_folder_path)

media_folder_metadata_handler.update(media_folder_metadata)

# print(media_folder_metadata)
# print(json.dumps(media_folder_metadata_handler.get_tv_show_season_episode_metadata(media_folder_metadata, 0, 0, 0), indent=4))


class PathType(Enum):
    TV_SHOW = 0
    TV_SHOW_SEASON = 1
    TV_SHOW_SEASON_EPISODE = 2

    def get_str(self):
        return path_type_strings[self.value]


def build_html_button(button_dict):
    return f'<input type="submit" name="{button_dict.get("name")}" value="{button_dict.get("value")}" style="width: 100px; height: 50px;">'


def build_html_button_list(button_list):
    return ' '.join([build_html_button(button_info) for button_info in button_list])


def build_chromecast_menu():
    global chromecast_handler
    scanned_chromecasts = '<div style="float:left; margin:10px">'
    scanned_chromecasts += f'<select name="select_scan_chromecast" id="select_scan_chromecast_id" size=4>'
    scanned_devices = chromecast_handler.get_scan_list()
    if scanned_devices:
        for index, item_str in enumerate(scanned_devices):
            scanned_chromecasts += f'<option value="{item_str}">{item_str}</option>'
    scanned_chromecasts += '</select></div>'

    chromecast_buttons = '<div style="float:left; margin:10px">'
    chromecast_buttons += build_html_button_list(device_button_list)
    chromecast_buttons += '</div>'

    connected_chromecasts = '<div style="float:left; margin:10px">'
    connected_chromecasts += f'<select name="select_connected_to_chromecast" ' \
                             f'id="select_connected_to_chromecast_id" size=4>'
    connected_devices_str = chromecast_handler.get_connected_devices_list_str()
    if connected_devices_str:
        for index, item_str in enumerate(connected_devices_str):
            connected_chromecasts += f'<option value="{item_str}">{item_str}</option>'
    connected_chromecasts += '</select></div>'

    return scanned_chromecasts + chromecast_buttons + connected_chromecasts


def build_select_list(set_selected, name: PathType, list_to_convert, selected_index=-1):
    add_autofocus = ""
    if set_selected:
        add_autofocus = "autofocus"

    ret_select_html = '<div style="float:left; margin:10px">'
    ret_select_html += f'<select {add_autofocus} name="select_{name.get_str()}" onchange="this.form.submit()" ' \
                       f'id="select_{name.get_str()}_id" size=30>'

    for index, item_str in enumerate(list_to_convert):
        if selected_index == index:
            ret_select_html += f'<option selected value="{index}">{item_str}</option>'
        else:
            ret_select_html += f'<option value="{index}">{item_str}</option>'

    ret_select_html += '</select></div>'
    return ret_select_html


def build_tv_show_name_list(set_selected, selected_tv_show_id=-1):
    if tv_show_dir_list := url_builder.get_tv_show_dir_list():
        return build_select_list(set_selected, PathType.TV_SHOW, tv_show_dir_list, selected_tv_show_id)
    return ""


def build_tv_show_season_name_list(set_selected, tv_show_id, selected_tv_show_season_id=-1):
    if tv_show_season_dir_list := url_builder.get_tv_show_season_dir_list(tv_show_id):
        return build_select_list(set_selected, PathType.TV_SHOW_SEASON, tv_show_season_dir_list,
                                 selected_tv_show_season_id)


def build_tv_show_season_episode_name_list(set_selected, tv_show_id, tv_show_season_id,
                                           selected_tv_show_season_episode_id=-1):
    if tv_show_season_episode_dir_list := url_builder.get_tv_show_season_show_dir_list(tv_show_id, tv_show_season_id):
        return build_select_list(set_selected, PathType.TV_SHOW_SEASON_EPISODE, tv_show_season_episode_dir_list,
                                 selected_tv_show_season_episode_id)


def build_visual_selector(tv_show_id, tv_show_season_id, tv_show_season_episode_id, changed_type):
    print(changed_type.get_str())
    episode_select = f'<div style="float:left; margin:10px"><form action="{url_for("main_index")}" method="post">'
    episode_select += str(build_tv_show_name_list(PathType.TV_SHOW == changed_type, tv_show_id))
    episode_select += str(build_tv_show_season_name_list(PathType.TV_SHOW_SEASON == changed_type, tv_show_id,
                                                         tv_show_season_id))
    episode_select += str(build_tv_show_season_episode_name_list(PathType.TV_SHOW_SEASON_EPISODE == changed_type,
                                                                 tv_show_id, tv_show_season_id,
                                                                 tv_show_season_episode_id))

    episode_select += build_html_button_list(media_controller_button_list)

    episode_select += build_chromecast_menu()
    episode_select += '</form></div>'

    return episode_select


def hello_world():
    print("Hello world!")


@app.route('/pause_cast', methods=['GET', 'POST'])
def pause_cast():
    print("PAUSING")
    return main_index()


@app.route('/', methods=['GET', 'POST'])
def main_index():
    global current_episode, previous_selected_tv_show, previous_selected_tv_show_season, \
        previous_selected_tv_show_season_episode
    print(request.form)

    tv_show_id = 0
    tv_show_season_id = 0
    tv_show_season_episode_id = 0

    if request.method == 'POST':
        POST_tv_show_id = request.form.get(f'select_{PathType.TV_SHOW.get_str()}')
        POST_tv_show_season_id = request.form.get('select_tv_show_season')
        POST_tv_show_season_episode_id = request.form.get('select_tv_show_season_episode')

        if POST_tv_show_id:
            POST_tv_show_id_int = int(POST_tv_show_id)
            tv_show_id = POST_tv_show_id_int if url_builder.valid_tv_show_id(POST_tv_show_id_int) else 0
            print(f"VALID tv_show_id: {tv_show_id}")
        if POST_tv_show_season_id:
            POST_tv_show_id_season_int = int(POST_tv_show_season_id)
            tv_show_season_id = POST_tv_show_id_season_int \
                if url_builder.valid_tv_show_season_id(tv_show_id, POST_tv_show_id_season_int) else 0
            print(f"VALID tv_show_season_id: {tv_show_season_id}")
        if POST_tv_show_season_episode_id:
            POST_tv_show_id_season_episode_int = int(POST_tv_show_season_episode_id)
            tv_show_season_episode_id = POST_tv_show_id_season_episode_int \
                if url_builder.valid_tv_show_season_episode_id(tv_show_id, tv_show_season_id,
                                                               POST_tv_show_id_season_episode_int) else 0
            print(f"VALID tv_show_season_episode_id: {tv_show_season_episode_id}")

        if request.form.get('start'):
            print("START PRESSED")
            # my_media_device.play_url(current_episode)
            # my_media_device.play_media_drive_id(tv_show_id, tv_show_season_id, tv_show_season_episode_id)
            current_episode = chromecast_handler.play_from_media_drive(tv_show_id, tv_show_season_id,
                                                                       tv_show_season_episode_id)
            print(f"Playing episode: {current_episode}")
            # current_episode = my_media_device.get_url()

        elif request.form.get('play'):
            print("PLAY PRESSED")
            chromecast_handler.send_command(CommandList.CMD_PLAY)
        elif request.form.get('pause'):
            print("PAUSE PRESSED")
            chromecast_handler.send_command(CommandList.CMD_PAUSE)
        elif request.form.get('stop'):
            chromecast_handler.send_command(CommandList.CMD_STOP)
            print("STOP PRESSED")
        elif request.form.get('skip'):
            print("SKIP PRESSED")
            chromecast_handler.send_command(CommandList.CMD_SKIP)
        elif request.form.get('connect'):
            print("CONNECT PRESSED")
            # print(request.form.get('select_scan_chromecast'))
            if device_id_str := request.form.get('select_scan_chromecast'):
                chromecast_handler.connect_to_chromecast(device_id_str)
        elif request.form.get('disconnect'):
            print("DISCONNECT PRESSED")
            if device_id_str := request.form.get('select_connected_to_chromecast'):
                chromecast_handler.disconnect_from_chromecast(device_id_str)

    changed_type = PathType.TV_SHOW

    if previous_selected_tv_show != tv_show_id:
        print("SHOW CHANGED")
        previous_selected_tv_show = tv_show_id
    elif previous_selected_tv_show_season != tv_show_season_id:
        print("SEASON CHANGED")
        changed_type = PathType.TV_SHOW_SEASON
        previous_selected_tv_show_season = tv_show_season_id
    # elif previous_selected_tv_show_season_episode != tv_show_season_episode_id:
    #     print("EPISODE CHANGED")
    #     changed_type = PathType.TV_SHOW_SEASON_EPISODE
    #     previous_selected_tv_show_season_episode = tv_show_season_episode_id

    html_form = chromecast_handler.get_startup_sha()
    html_form += build_visual_selector(tv_show_id, tv_show_season_id, tv_show_season_episode_id, changed_type)
    html_form += current_episode

    return html_form


if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    app.run(debug=True)
    # port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=6000)

    # server = Process(target=app.run)
