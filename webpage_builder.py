# import json

from flask import Flask, request, url_for

# jsonify, redirect, current_app, render_template
from backend_handler import BackEndHandler
from chromecast_handler import CommandList
from media_folder_metadata_handler import MediaID, PathType

app = Flask(__name__)

chromecast_button_list = [
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
path_type_strings = ["tv_show", "tv_show_season", "tv_show_season_episode"]

backend_handler = BackEndHandler()
backend_handler.start()


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
    chromecast_buttons += build_html_button_list(chromecast_button_list)
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


def build_select_list(select_name, select_list, select_selected_index, add_autofocus):
    autofocus_txt = ""
    if add_autofocus:
        autofocus_txt = "autofocus"

    ret_select_html = '<div style="float:left; margin:10px">'
    ret_select_html += f'<select {autofocus_txt} name="select_{select_name}" onchange="this.form.submit()" ' \
                       f'id="select_{select_name}_id" size=30>'
    if select_list:
        for index, item_str in enumerate(select_list):
            if select_selected_index == index:
                ret_select_html += f'<option selected value="{index}">{item_str}</option>'
            else:
                ret_select_html += f'<option value="{index}">{item_str}</option>'

    ret_select_html += '</select></div>'
    return ret_select_html


def build_episode_selector(changed_type, media_id):
    episode_select = f'<div style="float:left; margin:10px"><form action="{url_for("main_index")}" method="post">'
    episode_select += build_select_list(path_type_strings[PathType.TV_SHOW.value],
                                        backend_handler.get_tv_show_name_list(),
                                        media_id.tv_show_id,
                                        PathType.TV_SHOW == changed_type)
    episode_select += build_select_list(path_type_strings[PathType.TV_SHOW_SEASON.value],
                                        backend_handler.get_tv_show_season_name_list(),
                                        media_id.tv_show_season_id,
                                        PathType.TV_SHOW_SEASON == changed_type)
    episode_select += build_select_list(path_type_strings[PathType.TV_SHOW_SEASON_EPISODE.value],
                                        backend_handler.get_tv_show_season_episode_name_list(),
                                        media_id.tv_show_season_episode_id,
                                        PathType.TV_SHOW_SEASON_EPISODE == changed_type)
    episode_select += '</form></div>'

    return episode_select


def build_media_controls():
    chromecast_controls = f'<div style="float:left; margin:10px"><form action="{url_for("main_index")}" method="post">'
    chromecast_controls += build_html_button_list(media_controller_button_list)
    chromecast_controls += '</form></div>'
    return chromecast_controls


def build_chromecast_controls():
    chromecast_controls = f'<div style="float:left; margin:10px"><form action="{url_for("main_index")}" method="post">'
    chromecast_controls += build_chromecast_menu()
    chromecast_controls += '</form></div>'
    return chromecast_controls


@app.route('/', methods=['GET', 'POST'])
def main_index():
    changed_type = None

    if request.method == 'POST':
        new_tv_show_id = request.form.get(f"select_{path_type_strings[PathType.TV_SHOW.value]}")
        new_tv_show_season_id = request.form.get(f"select_{path_type_strings[PathType.TV_SHOW_SEASON.value]}")
        new_tv_show_season_episode_id = request.form.get(
            f"select_{path_type_strings[PathType.TV_SHOW_SEASON_EPISODE.value]}")

        new_media_id = MediaID(new_tv_show_id, new_tv_show_season_id, new_tv_show_season_episode_id)
        changed_type = backend_handler.update_media_id_selection(new_media_id)

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
            if device_id_str := request.form.get('select_scan_chromecast'):
                backend_handler.connect_chromecast(device_id_str)
        elif request.form.get('disconnect'):
            print("DISCONNECT PRESSED")
            if device_id_str := request.form.get('select_connected_to_chromecast'):
                backend_handler.disconnect_chromecast(device_id_str)

    html_form = backend_handler.get_startup_sha()
    html_form += build_episode_selector(changed_type, backend_handler.get_media_id())
    html_form += build_chromecast_controls()
    html_form += build_media_controls()
    html_form += backend_handler.get_episode_url()

    return html_form


if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5002)
