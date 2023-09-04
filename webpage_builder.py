# import json
from enum import Enum

from flask import Flask, request, url_for

# jsonify, redirect, current_app, render_template
from backend_handler import BackEndHandler
from chromecast_handler import CommandList
from media_folder_metadata_handler import MediaID

app = Flask(__name__)

device_button_list = [
    {"name": "connect", "value": "Connect"},
    {"name": "disconnect", "value": "Disconnect"}
]
media_controller_button_list = [
    {"name": "start", "value": "Start"},
    {"name": "pause", "value": "Pause"},
    {"name": "stop", "value": "Stop"},
    {"name": "play", "value": "Play"},
    {"name": "skip", "value": "Skip"}
]

backend_handler = BackEndHandler()
backend_handler.start()

previous_selected_tv_show = None
previous_selected_tv_show_season = None
previous_selected_tv_show_season_episode = None

path_type_strings = ["tv_show", "tv_show_season", "tv_show_season_episode"]


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
    scanned_chromecasts = '<div style="float:left; margin:10px">'
    scanned_chromecasts += f'<select name="select_scan_chromecast" id="select_scan_chromecast_id" size=4>'
    scanned_devices = backend_handler.get_chromecast_scan_list()
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
    connected_devices_str = backend_handler.get_chromecast_connected_device_list()
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


def build_tv_show_name_list(set_selected, media_id):
    if tv_show_dir_list := backend_handler.get_tv_show_name_list():
        return build_select_list(set_selected, PathType.TV_SHOW, tv_show_dir_list, media_id.tv_show_id)
    return ""


def build_tv_show_season_name_list(set_selected, media_id):
    if tv_show_season_dir_list := backend_handler.get_tv_show_season_name_list():
        return build_select_list(set_selected, PathType.TV_SHOW_SEASON, tv_show_season_dir_list,
                                 media_id.tv_show_season_id)
    return ""


def build_tv_show_season_episode_name_list(set_selected, media_id):
    if tv_show_season_episode_dir_list := backend_handler.get_tv_show_season_episode_name_list():
        return build_select_list(set_selected, PathType.TV_SHOW_SEASON_EPISODE, tv_show_season_episode_dir_list,
                                 media_id.tv_show_season_episode_id)
    return ""


def build_visual_selector(changed_type):
    media_id = backend_handler.get_media_id()
    episode_select = f'<div style="float:left; margin:10px"><form action="{url_for("main_index")}" method="post">'
    episode_select += str(build_tv_show_name_list(PathType.TV_SHOW == changed_type, media_id))
    episode_select += str(build_tv_show_season_name_list(PathType.TV_SHOW_SEASON == changed_type, media_id))
    episode_select += str(build_tv_show_season_episode_name_list(PathType.TV_SHOW_SEASON_EPISODE == changed_type,
                                                                 media_id))

    episode_select += build_html_button_list(media_controller_button_list)

    episode_select += build_chromecast_menu()
    episode_select += '</form></div>'

    return episode_select


def update_tv_show(post_id, media_id):
    if post_id and media_id.tv_show_id != (new_tv_show_id := int(post_id)):
        if backend_handler.set_media_id(MediaID(new_tv_show_id, 0, 0)):
            return PathType.TV_SHOW
    return None


def update_tv_show_season(post_id, media_id):
    if post_id and media_id.tv_show_season_id != (new_tv_show_season_id := int(post_id)):
        if backend_handler.set_media_id(MediaID(media_id.tv_show_id, new_tv_show_season_id, 0)):
            return PathType.TV_SHOW_SEASON
    return None


def update_tv_show_season_episode(post_id, media_id):
    if post_id and media_id.tv_show_season_episode_id != (new_tv_show_season_episode_id := int(post_id)):
        new_media_id = media_id
        new_media_id.tv_show_season_episode_id = new_tv_show_season_episode_id
        if backend_handler.set_media_id(new_media_id):
            return PathType.TV_SHOW_SEASON_EPISODE
    return None


def hello_world():
    print("Hello world!")


@app.route('/pause_cast', methods=['GET', 'POST'])
def pause_cast():
    print("PAUSING")
    return main_index()


@app.route('/', methods=['GET', 'POST'])
def main_index():
    changed_type = None

    if request.method == 'POST':
        POST_tv_show_id = request.form.get(f'select_{PathType.TV_SHOW.get_str()}')
        POST_tv_show_season_id = request.form.get('select_tv_show_season')
        POST_tv_show_season_episode_id = request.form.get('select_tv_show_season_episode')

        media_id = backend_handler.get_media_id()
        changed_type = update_tv_show(POST_tv_show_id, media_id)
        if not changed_type:
            changed_type = update_tv_show_season(POST_tv_show_season_id, media_id)
        if not changed_type:
            changed_type = update_tv_show_season_episode(POST_tv_show_season_episode_id, media_id)

        if request.form.get('start'):
            print("START PRESSED")
            backend_handler.play_episode()

        elif request.form.get('play'):
            print("PLAY PRESSED")
            backend_handler.send_chromecast_cmd(CommandList.CMD_PLAY)
        elif request.form.get('pause'):
            print("PAUSE PRESSED")
            backend_handler.send_chromecast_cmd(CommandList.CMD_PAUSE)
        elif request.form.get('stop'):
            backend_handler.send_chromecast_cmd(CommandList.CMD_STOP)
            print("STOP PRESSED")
        elif request.form.get('skip'):
            print("SKIP PRESSED")
            backend_handler.send_chromecast_cmd(CommandList.CMD_SKIP)
        elif request.form.get('connect'):
            print("CONNECT PRESSED")
            # print(request.form.get('select_scan_chromecast'))
            if device_id_str := request.form.get('select_scan_chromecast'):
                backend_handler.connect_chromecast(device_id_str)
        elif request.form.get('disconnect'):
            print("DISCONNECT PRESSED")
            if device_id_str := request.form.get('select_connected_to_chromecast'):
                backend_handler.disconnect_chromecast(device_id_str)

    html_form = backend_handler.get_startup_sha()
    html_form += build_visual_selector(changed_type)
    html_form += backend_handler.get_episode_url()

    return html_form


if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    app.run(debug=True)
    # port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=6000)

    # server = Process(target=app.run)
