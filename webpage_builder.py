import json
from flask import Flask, request, url_for, render_template_string

# jsonify, redirect, current_app, render_template
from backend_handler import BackEndHandler
from chromecast_handler import CommandList
from media_folder_metadata_handler import MediaID, PathType

app = Flask(__name__)

webpage_title = "Media Stream"

html_style = '<link rel="stylesheet" href="{{ url_for(\'static\',filename=\'style.css\') | safe }}"> ' \
             '<script src="https://kit.fontawesome.com/fc24dd5615.js" crossorigin="anonymous"></script>' \
             '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">'

bootstrap_js = '<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>' \
               '<script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js" integrity="sha384-I7E8VVD/ismYTF4hNIPjVp/Zjvgyol6VFvRkX/vR+Vc4jQkC+hVqc2pM8ODewa9r" crossorigin="anonymous"></script>' \
               '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.min.js" integrity="sha384-BBtl+eGJRgqQAUMxJ7pMwbEyER4l1g+O15P+16Ep7Q9Q+zqX6gSbd85u4mG4QzX+" crossorigin="anonymous"></script>'

html_scripts = '<script  type="text/javascript" language="javascript" src="{{ url_for(\'static\', filename=\'app.js\') }}"></script>'
html_scripts += bootstrap_js

html_head = f'<head><title>{webpage_title}</title><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">{html_style}{html_scripts}</head>'

media_controller_button_dict = {
    "rewind": {"name": "rewind", "value": "&#x23EE;", "icon": "fa-backward",
               "onclick": f"chromecast_command({CommandList.CMD_REWIND.value});"},
    "rewind_15": {"name": "rewind_15", "value": "&#x21BA;", "icon": "fa-rotate-left",
                  "onclick": f"chromecast_command({CommandList.CMD_REWIND_15.value});"},
    "play": {"name": "play", "value": "&#x23F5;", "icon": "fa-play",
             "onclick": f"chromecast_command({CommandList.CMD_PLAY.value});"},
    "pause": {"name": "pause", "value": "&#x23F8;", "icon": "fa-pause",
              "onclick": f"chromecast_command({CommandList.CMD_PAUSE.value});"},
    "skip_15": {"name": "skip_15", "value": "&#x21BB;", "icon": "fa-rotate-right",
                "onclick": f"chromecast_command({CommandList.CMD_SKIP_15.value});"},
    "skip": {"name": "skip", "value": "&#x23ED;", "icon": "fa-forward",
             "onclick": f"chromecast_command({CommandList.CMD_SKIP.value});"},
    "stop": {"name": "stop", "value": "&#x23F9;", "icon": "fa-stop",
             "onclick": f"chromecast_command({CommandList.CMD_STOP.value});"}
}

path_type_strings = ["tv_show", "tv_show_season", "tv_show_season_episode"]

backend_handler = BackEndHandler()
backend_handler.start()


def build_html_button(button_dict):
    name = button_dict.get("name", "Error")
    value = button_dict.get("value", "Error")
    onclick = button_dict.get("onclick", "")
    if button_icon := button_dict.get("icon"):
        return f'<button name="{name}" class="media_control_buttons" onclick="{onclick}"><i class="fa {button_icon}" aria-hidden="true"></i></button>'
    return f'<button name="{name}" class="media_control_buttons" onclick="{onclick}">{value}</button>'


def build_html_button_list(button_list):
    return ' '.join([build_html_button(button_info) for button_info in button_list])


def build_chromecast_menu():
    chromecast_holder = '<ul class="navbar-nav ms-auto mb-2 mb-lg-0">'
    # Create text block to display connected chromecast
    connected_device_id = backend_handler.get_chromecast_device_id()
    if not connected_device_id:
        connected_device_id = ""
    # Create dropdown menu button
    chromecast_holder += f'<li class="nav-item">'
    chromecast_holder += f'<a id=connected_chromecast_id class="nav-link" aria-disabled="true">{connected_device_id}</a></li>'
    chromecast_holder += '<li class="nav-item dropstart">'
    chromecast_holder += '<a class="nav-link" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">'
    chromecast_holder += '<span class="fa-brands fa-chromecast"></span></a>'
    chromecast_holder += '<ul id="dropdown_scanned_chromecasts" class="dropdown-menu">'
    # Create dropdown list of scanned chromecasts
    scanned_devices = backend_handler.get_chromecast_scan_list()
    if scanned_devices:
        for index, item_str in enumerate(scanned_devices):
            chromecast_holder += f'<li><a class="dropdown-item" href="javascript:connectChromecast(\'{item_str}\')" value="{item_str}">{item_str}</a></li>'
    # Add the disconnect button to the dropdown list
    chromecast_holder += f'<li><hr class="dropdown-divider"></li><li><a class="dropdown-item" href="javascript:disconnectChromecast()">Disconnect</a></li>'
    chromecast_holder += '</ul></li></ul>'

    return chromecast_holder


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
    media_controls = '<div class="footer">'
    media_controls += '<div align="center">'
    media_controls += '<input type="range" id="mediaTimeInputId" onMouseUp="setMediaRuntime(this);" min=0 value=0 class="slider">'
    media_controls += '<output id="mediaTimeOutputId"></output>'
    media_controls += '</div>'
    media_controls += '<div align="center">'
    media_controls += build_html_button_list(media_controller_button_dict.values())
    media_controls += '</div>'
    media_controls += '</div>'
    return media_controls


# Build the bootstrap navbar
def build_navbar():
    navbar = '<nav class="navbar fixed-top navbar-expand-lg bg-dark" data-bs-theme="dark"> '
    navbar += '<div class="container-fluid"><a class="navbar-brand" href="#">&#x1F422;&#x1F995;</a>'
    navbar += '<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">'
    navbar += '<span class="navbar-toggler-icon"></span></button>'
    navbar += '<div class="collapse navbar-collapse" id="navbarSupportedContent">'
    navbar += f"{build_chromecast_menu()}"
    navbar += '</div></div></nav>'
    return navbar


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
    if media_metadata := backend_handler.get_media_controller_metadata():
        data = media_metadata
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

    html_form = f'<!DOCTYPE html><html lang="en">{html_head}<body>{build_navbar()}'
    html_form += '<div>'
    html_form += f'<p>{backend_handler.get_startup_sha()}</p>'

    html_form += '<div id="mediaContentSelectDiv">'
    html_form += build_episode_selector(changed_type, backend_handler.get_media_id())

    html_form += '</div></div>'
    html_form += build_media_controls()
    html_form += f'</body></html>'

    return render_template_string(html_form)


if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5002)
