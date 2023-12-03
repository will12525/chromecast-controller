from enum import Enum, auto

from flask import Flask, request, render_template_string, redirect, url_for

# jsonify, redirect, current_app, render_template
from backend_handler import BackEndHandler
from chromecast_handler import CommandList
from database_handler.database_handler import DatabaseHandler
from database_handler.create_database import DBCreator


# TODO: Add to DB: Add media title from ffmpeg extraction
# TODO: Add to DB: Track if media was previously watched
# TODO: Update DB: Remove media that no longer exists
# TODO: Update media grid to dynamically update rather than page reload
# TODO: Extract default values to json config file
# TODO: Update chromecast menu auto populate to remove missing chromecasts
# TODO: Extract HTML building functions and REST endpoints
# TODO: Update all js function references to eventlisteneres on js side
# TODO: Add notification when media scan completes
# TODO: Convert chromecast name strings to id values and use ID values to refer to chromecasts

class APIEndpoints(Enum):
    MAIN = "/"
    GET_CHROMECAST_CONTROLS = "/get_chromecast_controls"
    GET_MEDIA_CONTENT_TYPES = "/get_media_content_types"
    SET_CURRENT_MEDIA_RUNTIME = "/set_current_media_runtime"
    GET_CURRENT_MEDIA_RUNTIME = "/get_current_media_runtime"
    CONNECT_CHROMECAST = "/connect_chromecast"
    GET_CHROMECAST_LIST = "/get_chromecast_list"
    DISCONNECT_CHROMECAST = "/disconnect_chromecast"
    CHROMECAST_COMMAND = "/chromecast_command"
    PLAY_MEDIA = "/play_media"
    SCAN_MEDIA_DIRECTORIES = "/scan_media_directories"
    GET_MEDIA_MENU_DATA = "/get_media_menu_data"


class ContentType(Enum):
    MEDIA = auto()
    TV_SHOW = auto()
    SEASON = auto()
    MOVIE = auto()
    PLAYLIST = auto()


app = Flask(__name__)

webpage_title = "Media Stream"

html_style = '<link rel="stylesheet" href="{{ url_for(\'static\',filename=\'style.css\') | safe }}"> '
html_style += '<script src="https://kit.fontawesome.com/fc24dd5615.js" crossorigin="anonymous"></script>'
html_style += '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">'

bootstrap_js = '<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>'
bootstrap_js += '<script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js" integrity="sha384-I7E8VVD/ismYTF4hNIPjVp/Zjvgyol6VFvRkX/vR+Vc4jQkC+hVqc2pM8ODewa9r" crossorigin="anonymous"></script>'
bootstrap_js += '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.min.js" integrity="sha384-BBtl+eGJRgqQAUMxJ7pMwbEyER4l1g+O15P+16Ep7Q9Q+zqX6gSbd85u4mG4QzX+" crossorigin="anonymous"></script>'

html_scripts = '<script type="text/javascript" language="javascript" src="{{ url_for(\'static\', filename=\'app.js\') }}"></script>'
html_scripts += bootstrap_js

html_head = f'<head><title>{webpage_title}</title><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">{html_style}{html_scripts}</head>'

media_controller_button_dict = {
    "rewind": {"icon": "fa-backward", "id": f"{CommandList.CMD_REWIND.name}_media_button"},
    "rewind_15": {"icon": "fa-rotate-left", "id": f"{CommandList.CMD_REWIND_15.name}_media_button"},
    "play": {"icon": "fa-play", "id": f"{CommandList.CMD_PLAY.name}_media_button"},
    "pause": {"icon": "fa-pause", "id": f"{CommandList.CMD_PAUSE.name}_media_button"},
    "skip_15": {"icon": "fa-rotate-right", "id": f"{CommandList.CMD_SKIP_15.name}_media_button"},
    "skip": {"icon": "fa-forward", "id": f"{CommandList.CMD_SKIP.name}_media_button"},
    "stop": {"icon": "fa-stop", "id": f"{CommandList.CMD_STOP.name}_media_button"}
}

backend_handler = BackEndHandler()
backend_handler.start()


def build_media_menu_header(media_metadata):
    tv_show_grid = ""

    if media_metadata:
        # Build info card for tv show info block
        tv_show_grid += '<div class="container">'
        tv_show_grid += '<div class="row row-cols-auto">'
        tv_show_grid += '<div class="card mb-3" style="width: 18rem; height: 10rem;">'
        tv_show_grid += '<div class="row g-0">'
        tv_show_grid += '<div class="col-md-4">'
        tv_show_grid += '<!--img src="{{ url_for(\'static\', filename=\'default.jpg\') }}" class="img-fluid rounded-start" alt="..."-->'
        tv_show_grid += '</div>'
        tv_show_grid += '<div class="col-md-8">'
        tv_show_grid += '<div class="card-body">'

        if title := media_metadata.get("title"):
            tv_show_grid += f'<h5 class="card-title">{title}</h5>'
        if sub_title := media_metadata.get("sub_title"):
            tv_show_grid += f'<p class="card-text">{sub_title}</p>'
        if season_count := media_metadata.get("season_count"):
            tv_show_grid += f'<p class="card-text">Seasons: {season_count}</p>'
        if episode_count := media_metadata.get("episode_count"):
            tv_show_grid += f'<p class="card-text">Episodes: {episode_count}</p>'
        if tv_show_id := media_metadata.get("tv_show_id"):
            tv_show_grid += f'<a href="?content_type={ContentType.SEASON.value}&media_id={tv_show_id}" class="stretched-link"></a>'
        tv_show_grid += '</div></div></div></div></div></div>'
    return tv_show_grid


def build_media_menu_grid(media_list, media_metadata_href_content_type=None):
    tv_show_grid = ""
    # Create the grid
    tv_show_grid += '<div class="container"><div class="row row-cols-auto">'
    # Add a card element to the grid for each tv show
    for media_item in media_list:
        tv_show_grid += '<div class="col"><div class="card" style="width: 18rem; height: 6rem;">'
        tv_show_grid += '<!--img src="{{ url_for(\'static\', filename=\'default.jpg\') }}" class="card-img" alt="..."-->'
        tv_show_grid += f'<div class="card-body" >'
        tv_show_grid += f'<h5 class="card-title" style="color: black;">{media_item.get("title")}</h5>'
        if media_metadata_href_content_type:
            tv_show_grid += f'<a href="?content_type={media_metadata_href_content_type}&media_id={media_item.get("id")}" class="stretched-link"></a>'
        else:
            tv_show_grid += f'<a class="stretched-link" href="javascript:play_media(\'{media_item.get("id")}\')"></a>'
        tv_show_grid += '</div></div></div>'
    tv_show_grid += '</div></div>'
    return tv_show_grid


def build_top_navbar():
    navbar = '<nav class="navbar fixed-top navbar-expand-lg bg-dark" data-bs-theme="dark">'
    navbar += '<div class="container-fluid"><a class="navbar-brand" href="/">&#x1F422;&#x1F995;</a>'
    navbar += '<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">'
    navbar += '<span class="navbar-toggler-icon"></span></button>'
    navbar += '<div class="collapse navbar-collapse" id="navbarSupportedContent">'
    navbar += '<ul class="navbar-nav me-auto mb-2 mb-lg-0">'
    navbar += '<li class="nav-item"><a id=tv_show_select_button class="nav-link" aria-current="page">TV Shows</a></li>'
    navbar += '<li class="nav-item"><a id=movie_select_button class="nav-link" aria-current="page">Movies</a></li>'
    navbar += '<li class="nav-item"><a id=scan_media_button class="nav-link" aria-current="page">Scan Media</a></li>'
    navbar += '</ul>'
    navbar += '<ul class="navbar-nav ml-auto mb-2 mb-lg-0">'
    navbar += '<li class="nav-item">'
    navbar += '<a id=connected_chromecast_id class="nav-link" aria-disabled="true"></a></li>'
    navbar += '<li class="nav-item dropstart">'
    navbar += '<a id="chromecast_menu" class="nav-link" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">'
    navbar += '<span class="fa-brands fa-chromecast"></span></a>'
    navbar += '<ul id="dropdown_scanned_chromecasts" class="dropdown-menu">'
    navbar += '<li><hr class="dropdown-divider"></li><li><a id="chromecast_disconnect_button" class="dropdown-item">Disconnect</a></li>'
    navbar += '</ul></li></ul>'
    navbar += '</div></div></nav>'
    return navbar


def build_bottom_navbar():
    media_controls = '<nav class="navbar fixed-bottom navbar-expand-xl bg-dark bg-body-tertiary" data-bs-theme="light" style="height: 10%">'
    media_controls += '<div class="container-fluid" align="center">'
    media_controls += '<input type="range" id="mediaTimeInputId" onMouseUp="setMediaRuntime(this);" min=0 value=0 class="slider">'
    media_controls += '<output id="mediaTimeOutputId" align="center"></output>'
    media_controls += '</div>'
    media_controls += '<div class="container" align="center">'
    for button_info in media_controller_button_dict.values():
        media_controls += f'<button id="{button_info.get("id")}" class="btn"><i class="fa-solid {button_info.get("icon")} fa-2xl"></i></button>'
    media_controls += '</div></nav>'
    return media_controls


def build_media_menu_content(content_type, media_id_str=None):
    media_id = None
    tv_show_grid = ""
    media_metadata = None
    media_list = None
    next_content_type = None
    db_handler = DatabaseHandler()

    if db_handler:
        if media_id_str:
            media_id = int(media_id_str)
        if content_type == ContentType.MEDIA:
            media_metadata = db_handler.get_tv_show_season_metadata(media_id)
            media_list = db_handler.get_tv_show_season_episode_title_list(media_id)
        elif content_type == ContentType.SEASON:
            media_metadata = db_handler.get_tv_show_metadata(media_id)
            media_list = db_handler.get_tv_show_season_title_list(media_id)
            next_content_type = ContentType.MEDIA.value

        elif content_type == ContentType.MOVIE:
            media_list = db_handler.get_movie_title_list()
        elif content_type == ContentType.TV_SHOW:
            media_list = db_handler.get_tv_show_title_list()
            next_content_type = ContentType.SEASON.value
        else:
            print(f"Unknown content type provided: {content_type}")

    tv_show_grid += f'<!DOCTYPE html><html lang="en">{html_head}<body>{build_top_navbar()}<div style="margin-bottom: 40%;">'
    tv_show_grid += f'<p>{backend_handler.get_startup_sha()}</p>'
    tv_show_grid += '<div id="mediaContentSelectDiv">'
    try:
        tv_show_grid += build_media_menu_header(media_metadata)
        tv_show_grid += build_media_menu_grid(media_list, next_content_type)
    except ValueError as e:
        print(f"Error building media page content\n{e}")
    tv_show_grid += '</div></div>'
    tv_show_grid += build_bottom_navbar()
    tv_show_grid += '</body></html>'

    return tv_show_grid


def build_main_content(request_args):
    media_id_str = request_args.get('media_id', None)
    content_type_value = request_args.get('content_type', None)
    content_type = ContentType.TV_SHOW
    if content_type_value:
        try:
            content_type = ContentType(int(content_type_value))
        except Exception as e:
            print(e)

    return build_media_menu_content(content_type=content_type, media_id_str=media_id_str)


@app.route(APIEndpoints.MAIN.value)
def main_index():
    return render_template_string(build_main_content(request.args))


@app.route(APIEndpoints.GET_MEDIA_CONTENT_TYPES.value, methods=['GET'])
def get_media_content_types():
    data = {i.name: i.value for i in ContentType}
    return data, 200


@app.route(APIEndpoints.GET_CHROMECAST_CONTROLS.value, methods=['GET'])
def get_chromecast_controls():
    data = {"chromecast_controls": {i.name: i.value for i in CommandList}}
    return data, 200


@app.route(APIEndpoints.SET_CURRENT_MEDIA_RUNTIME.value, methods=['POST'])
def set_current_media_runtime():
    data = {}
    if json_request := request.get_json():
        if new_media_time := json_request.get("new_media_time"):
            backend_handler.seek_media_time(new_media_time)
    return data, 200


@app.route(APIEndpoints.GET_CURRENT_MEDIA_RUNTIME.value, methods=['GET'])
def get_current_media_runtime():
    data = {}
    if media_metadata := backend_handler.get_chromecast_media_controller_metadata():
        data = media_metadata
    return data, 200


@app.route(APIEndpoints.CONNECT_CHROMECAST.value, methods=['POST'])
def connect_chromecast():
    data = {}
    if json_request := request.get_json():
        if chromecast_id := json_request.get("chromecast_id"):
            if backend_handler.connect_chromecast(chromecast_id):
                data = {'chromecast_id': chromecast_id}
    return data, 200


@app.route(APIEndpoints.GET_CHROMECAST_LIST.value, methods=['POST'])
def get_chromecast_list():
    data = {
        "scanned_devices": backend_handler.get_chromecast_scan_list(),
        "connected_device": backend_handler.get_chromecast_device_id()
    }
    return data, 200


@app.route(APIEndpoints.DISCONNECT_CHROMECAST.value, methods=['POST'])
def disconnect_chromecast():
    data = {}
    backend_handler.disconnect_chromecast()
    return data, 200


@app.route(APIEndpoints.CHROMECAST_COMMAND.value, methods=['POST'])
def chromecast_command():
    data = {}
    if json_request := request.get_json():
        if chromecast_cmd_id := json_request.get("chromecast_cmd_id"):
            backend_handler.send_chromecast_cmd(CommandList(chromecast_cmd_id))
    return data, 200


@app.route(APIEndpoints.PLAY_MEDIA.value, methods=['POST'])
def play_media():
    data = {}
    if json_request := request.get_json():
        if media_id := json_request.get("media_id", 0):
            playlist_id = json_request.get("playlist_id", None)
            backend_handler.play_media_on_chromecast(media_id, playlist_id)
    return data, 200


@app.route(APIEndpoints.SCAN_MEDIA_DIRECTORIES.value, methods=['POST'])
def scan_media_directories():
    data = {}
    db_creator = DBCreator()
    if db_creator:
        db_creator.scan_all_media_directories()
    return data, 200


@app.route(APIEndpoints.GET_MEDIA_MENU_DATA.value, methods=['POST'])
def get_media_menu_data():
    data = {}
    db_creator = DBCreator()
    if db_creator:
        pass
    return data, 200


if __name__ == "__main__":
    print("--------------------Running Main--------------------")
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5002)
