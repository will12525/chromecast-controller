import json
import js2py
from markupsafe import escape
from flask import Flask, request, url_for, render_template, render_template_string, jsonify

# jsonify, redirect, current_app, render_template
from backend_handler import BackEndHandler
from chromecast_handler import CommandList
from media_folder_metadata_handler import MediaID, PathType

app = Flask(__name__)

webpage_title = "Media Stream"

html_style = '<link rel="stylesheet" href="{{ url_for(\'static\',filename=\'style.css\') | safe }}">'
html_scripts = '<script src="{{ url_for(\'static\', filename=\'app.js\') }}"></script>'

html_head = f'<head><title>{webpage_title}</title><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">{html_style}{html_scripts}</head>'

chromecast_button_list = [
    {"name": "connect", "value": "Connect", "onclick": "connect_chromecast()"},
    {"name": "disconnect", "value": "Disconnect", "onclick": "disconnect_chromecast()"}
]

media_controller_button_dict = {
    "rewind": {"name": "rewind", "value": "&#x23EE;", "font_size": "50px",
               "onclick": f"chromecast_command({CommandList.CMD_REWIND.value});"},
    "rewind_15": {"name": "rewind_15", "value": "&#x21BA;", "font_size": "50px",
                  "onclick": f"chromecast_command({CommandList.CMD_REWIND_15.value});"},
    "play": {"name": "play", "value": "&#x23F5;", "font_size": "50px",
             "onclick": f"chromecast_command({CommandList.CMD_PLAY.value});"},
    "pause": {"name": "pause", "value": "&#x23F8;", "font_size": "50px",
              "onclick": f"chromecast_command({CommandList.CMD_PAUSE.value});"},
    "skip_15": {"name": "skip_15", "value": "&#x21BB;", "font_size": "50px",
                "onclick": f"chromecast_command({CommandList.CMD_SKIP_15.value});"},
    "skip": {"name": "skip", "value": "&#x23ED;", "font_size": "50px",
             "onclick": f"chromecast_command({CommandList.CMD_SKIP.value});"},
    "stop": {"name": "stop", "value": "&#x23F9;", "font_size": "50px",
             "onclick": f"chromecast_command({CommandList.CMD_STOP.value});"}
}

seek_button_list = [
    {"name": "seek", "value": "Seek"}
]
path_type_strings = ["tv_show", "tv_show_season", "tv_show_season_episode"]

backend_handler = BackEndHandler()
backend_handler.start()


def build_html_button(button_dict):
    name = button_dict.get("name", "Error")
    value = button_dict.get("value", "Error")
    font_size = button_dict.get("font_size", "10px")
    onclick = button_dict.get("onclick", "")

    return f'<button name="{name}" onclick="{onclick}" style="width: 100px; height: auto; align: center; font-size:{font_size};">{value}</button>'


def build_html_button_list(button_list):
    return ' '.join([build_html_button(button_info) for button_info in button_list])


def build_chromecast_menu():
    scanned_chromecasts = '<div style="float:left; margin:10px">'
    scanned_chromecasts += '<select id="select_scan_chromecast_id" size=4 ' \
                           'onChange="connectChromecast(this);">'
    scanned_chromecasts += '<option selected disabled>Scanned</option>'
    scanned_devices = backend_handler.get_chromecast_scan_list()
    if scanned_devices:
        for index, item_str in enumerate(scanned_devices):
            scanned_chromecasts += f'<option value="{item_str}">{item_str}</option>'
    scanned_chromecasts += '</select></div>'

    connected_chromecasts = '<div style="float:left; margin:10px">'
    connected_chromecasts += f'<select ' \
                             f'id="select_connected_to_chromecast_id" size=4 ' \
                             f'onChange="disconnectChromecast(this);">'
    connected_chromecasts += '<option selected disabled>Connected</option>'
    connected_device_id = backend_handler.get_chromecast_device_id()
    if connected_device_id:
        connected_chromecasts += f'<option value="{connected_device_id}">{connected_device_id}</option>'
    connected_chromecasts += '</select></div>'

    return scanned_chromecasts + connected_chromecasts


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
    print(url_for("main_index"))
    media_controls = '<div class="footer">'
    media_controls += '<input type="range" id="mediaTimeInputId" onMouseUp="setMediaRuntime(this);" min=0 value=0 class="slider">'
    media_controls += '<output id="mediaTimeOutputId"></output>'
    media_controls += build_html_button_list(media_controller_button_dict.values())
    media_controls += '</div>'
    return media_controls


@app.route('/set_current_media_runtime', methods=['POST'])
def set_current_media_runtime():
    data = {}
    if json_request := request.get_json():
        if new_media_time := json_request.get("new_media_time"):
            backend_handler.seek_media_time(new_media_time)
    return data, 200


@app.route('/get_current_media_runtime', methods=['GET'])
def get_current_media_runtime():
    data = {}
    if media_runtime := backend_handler.get_media_current_time():
        data['media_runtime'] = media_runtime
        data['media_duration'] = backend_handler.get_media_current_duration()
    return data, 200


@app.route('/connect_chromecast', methods=['POST'])
def connect_chromecast():
    data = {}
    if json_request := request.get_json():
        if chromecast_id := json_request.get("chromecast_id"):
            if backend_handler.connect_chromecast(chromecast_id):
                data = {'chromecast_id': chromecast_id}
    return data, 200


@app.route('/disconnect_chromecast', methods=['POST'])
def disconnect_chromecast():
    data = {}
    backend_handler.disconnect_chromecast()
    return data, 200


@app.route('/chromecast_command', methods=['POST'])
def chromecast_command():
    data = {}
    if json_request := request.get_json():
        if chromecast_cmd_id := json_request.get("chromecast_cmd_id"):
            backend_handler.send_chromecast_cmd(CommandList(chromecast_cmd_id))
    return data, 200


@app.route('/', methods=['GET', 'POST'])
def main_index():
    print(backend_handler)
    changed_type = None

    if request.method == 'POST':
        print(json.dumps(request.form, indent=4))
        if new_tv_show_id := request.form.get(f"select_{path_type_strings[PathType.TV_SHOW.value]}"):
            new_tv_show_season_id = request.form.get(f"select_{path_type_strings[PathType.TV_SHOW_SEASON.value]}")
            new_tv_show_season_episode_id = request.form.get(
                f"select_{path_type_strings[PathType.TV_SHOW_SEASON_EPISODE.value]}")

            new_media_id = MediaID(new_tv_show_id, new_tv_show_season_id, new_tv_show_season_episode_id)
            changed_type = backend_handler.update_media_id_selection(new_media_id)
            if changed_type == PathType.TV_SHOW_SEASON_EPISODE:
                backend_handler.play_episode()

    html_form = f'<!DOCTYPE html><html lang="en">{html_head}<body>'
    html_form += f'<div class="header"><p>&#x1F422;&#x1F995;</p></div>'
    html_form += '<div>'
    html_form += f'<p>{backend_handler.get_startup_sha()}</p>'
    html_form += build_episode_selector(changed_type, backend_handler.get_media_id())
    html_form += build_chromecast_menu()
    html_form += f'<p>{backend_handler.get_episode_url()}'
    if current_playing_episode_info := backend_handler.get_current_playing_episode_info():
        html_form += f'<p>{current_playing_episode_info.get("name", "")}</p>'

    html_form += build_media_controls()
    html_form += '</div></body></html>'

    return render_template_string(html_form)


if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5002)
