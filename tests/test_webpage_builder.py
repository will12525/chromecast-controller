import inspect
import pathlib
import time
from unittest import TestCase

from flask import Flask
from flask_minify import minify
from app.routes import main_routes, register_blueprints

from app.utils import backend_handler
from app.utils.common import get_file_hash

from . import pytest_mocks

SAVE_FILES = False


def load_file():
    with open(f'tests/templates/{inspect.stack()[1].function}.html', 'r') as file:  # r to open file in READ mode
        return file.read()


def save_to_file(output):
    file_name = f"tests/templates/{inspect.stack()[1].function}.html"
    with open(file_name, 'w') as file:
        file.write(output)


def print_differences(str_1, str_2):
    str_set_1 = set(str_1.split())
    str_set_2 = set(str_2.split())

    str_diff = str_set_1.symmetric_difference(str_set_2)
    isEmpty = (len(str_diff) == 0)

    if not isEmpty:
        print("ERROR: DIFFERENCES FOUND: ")
        print(str_diff)
        assert False


class TestWebpageBuilder(TestCase):
    DB_PATH = pathlib.Path("media_metadata.db")
    app = None

    def setUp(self) -> None:
        if self.DB_PATH.exists():
            self.DB_PATH.unlink()
        pytest_mocks.patch_get_file_hash(self)
        pytest_mocks.patch_get_ffmpeg_metadata(self)
        pytest_mocks.patch_extract_subclip(self)
        pytest_mocks.patch_update_processed_file(self)
        pytest_mocks.patch_get_free_disk_space(self)
        pytest_mocks.patch_get_free_disk_space_percent(self)
        pytest_mocks.patch_load_json_file_content(self)

        self.app = Flask(__name__, template_folder="../app/templates")
        self.app.testing = True
        minify(app=self.app, html=True, js=True, cssless=True)
        self.app.jinja_env.lstrip_blocks = True
        self.app.jinja_env.trim_blocks = True
        register_blueprints(self.app)
        bh = backend_handler.BackEndHandler()
        setup_thread = bh.start()
        # Wait for the setup_thread to finish so the database is fully populated for testing
        setup_thread.join()
        assert self.DB_PATH.exists()


class TestWebpageTemplates(TestWebpageBuilder):

    def test_build_main_content(self):
        client = self.app.test_client()
        response = client.get(main_routes.APIEndpoints.MAIN.value)

        assert response.status_code == 200
        main_content = response.data.decode('utf-8')

        assert main_content
        if SAVE_FILES:
            save_to_file(main_content)
        html_as_string = load_file()
        print_differences(main_content, html_as_string)

    def test_build_editor_content(self):
        client = self.app.test_client()
        response = client.get(main_routes.APIEndpoints.EDITOR.value)

        assert response.status_code == 200
        main_content = response.data.decode('utf-8')

        assert main_content
        if SAVE_FILES:
            save_to_file(main_content)
        html_as_string = load_file()
        print_differences(main_content, html_as_string)


class TestChromecastCommunication(TestWebpageBuilder):

    def test_get_chromecast_list(self):
        client = self.app.test_client()
        time.sleep(10)
        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.GET_CHROMECAST_LIST.value
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'scanned_devices' in data
        assert 'connected_device' in data
        assert len(data['scanned_devices']) > 0
        print(data)


class TestQueryMediaDB(TestWebpageBuilder):

    def query_media_db_example(self):
        client = self.app.test_client()
        payload = {
            "tag_list": ["movie"],
            "content_txt_search": "",
            "container_dict": {}
        }
        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.QUERY_DB.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        print(data)

    def test_update_media_metadata_container(self):
        client = self.app.test_client()
        payload = {
            "container_id": 2,
            "img_src": "",
            "description": "Hello world!"
        }

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.UPDATE_MEDIA_METADATA.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        print(data)

        payload = {
            "tag_list": [],
            "content_txt_search": "",
            "container_dict": {},
            "container_txt_search": "Duck"
        }

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.QUERY_DB.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        assert {'containers': [
            {'container_path': '/tv_shows/Duck Stories', 'container_title': 'Duck Stories',
             'description': 'Hello world!', 'id': 2,
             'img_src': '', 'season_index': 0}]} == data

    def test_scan_media_directories(self):
        initial_file_hash = get_file_hash(self.DB_PATH)
        client = self.app.test_client()

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.SCAN_MEDIA_DIRECTORIES.value,
        )

        assert response.status_code == 200
        data = response.get_json()
        new_file_hash = get_file_hash(self.DB_PATH)
        assert initial_file_hash == new_file_hash

    def test_get_next_media_tv_show(self):
        client = self.app.test_client()
        payload = {
            "content_id": 16,
            "parent_container_id": 1
        }

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.GET_NEXT_MEDIA.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        assert {'content_title': 'Test Tile', 'id': 17,
                'local_play_url': 'http://localhost:8002//tv_shows/Duck Stories/Duck Stories - s02e001.mp4',
                'parent_container_id': 1} == data
        payload["content_id"] = data.get('id')
        payload["parent_container_id"] = data.get('parent_container_id')

        response = client.post(
            main_routes.APIEndpoints.GET_NEXT_MEDIA.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        assert {'content_title': 'Test Tile', 'id': 3,
                'local_play_url': 'http://localhost:8000//tv_shows/Duck Stories/Duck Stories - s02e002.mp4',
                'parent_container_id': 1} == data

        payload["content_id"] = data.get('id')
        payload["parent_container_id"] = data.get('parent_container_id')

        response = client.post(
            main_routes.APIEndpoints.GET_NEXT_MEDIA.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        assert {'content_title': 'Test Tile', 'id': 1,
                'local_play_url': 'http://localhost:8000//tv_shows/Duck Stories/Duck Stories - s01e001.mp4',
                'parent_container_id': 1} == data

    def test_search_specific_movie(self):
        client = self.app.test_client()
        payload = {
            "tag_list": [],
            "content_txt_search": "Leonard",
            "container_dict": {}
        }

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.QUERY_DB.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        print(data)
        assert {'content': [{'container_id': None, 'content_directory_id': 1, 'content_id': 11,
                             'content_src': '/movies/Leonard (2014).mp4', 'content_title': 'Leonard',
                             'content_url': 'http://localhost:8000', 'description': '2014', 'id': 11, 'img_src': '',
                             'img_url': 'http://localhost:8000/', 'play_count': 0, 'tag_title': 'movie',
                             'user_tags': 'movie', 'user_tags_id': 5},
                            {'container_id': None, 'content_directory_id': 1, 'content_id': 12,
                             'content_src': '/movies/Leonard 2 (2016).mp4', 'content_title': 'Leonard 2',
                             'content_url': 'http://localhost:8000', 'description': '2016', 'id': 12,
                             'img_src': '/movies/Leonard 2 (2016).mp4.jpg',
                             'img_url': 'http://localhost:8000//movies/Leonard 2 (2016).mp4.jpg', 'play_count': 0,
                             'tag_title': 'movie', 'user_tags': 'movie', 'user_tags_id': 5}]} == data

    def test_search_specific_tv_show(self):
        client = self.app.test_client()
        payload = {
            "tag_list": [],
            "content_txt_search": "",
            "container_dict": {},
            "container_txt_search": "Duck"
        }

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.QUERY_DB.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        assert {'containers': [
            {'container_path': '/tv_shows/Duck Stories', 'container_title': 'Duck Stories', 'description': '', 'id': 2,
             'img_src': '', 'season_index': 0}]} == data

    def test_build_tv_shows_content(self):
        client = self.app.test_client()
        payload = {
            "tag_list": ["tv show"],
            "content_txt_search": "",
            "container_dict": {}
        }

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.QUERY_DB.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        assert {'containers': [
            {'container_id': 2, 'container_path': '/tv_shows/Duck Stories', 'container_title': 'Duck Stories',
             'content_id': None, 'description': '', 'id': 2, 'img_src': '', 'season_index': 0, 'tag_title': 'tv show',
             'user_tags': 'tv show', 'user_tags_id': 4},
            {'container_id': 5, 'container_path': '/tv_shows/Vampire', 'container_title': 'Vampire', 'content_id': None,
             'description': '', 'id': 5, 'img_src': '', 'season_index': 0, 'tag_title': 'tv show',
             'user_tags': 'tv show', 'user_tags_id': 4}], 'content': []} == data

    def test_build_tv_show_content(self):
        client = self.app.test_client()
        payload = {
            "tag_list": [],
            "content_txt_search": "",
            "container_dict": {"container_id": 2}
        }

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.QUERY_DB.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        assert {'containers': [
            {'container_id': 1, 'container_path': '/tv_shows/Duck Stories', 'container_title': 'Season 1',
             'content_index': 1, 'description': '', 'id': 1, 'img_src': '', 'parent_container_id': 2,
             'season_index': 1},
            {'container_id': 3, 'container_path': '/tv_shows/Duck Stories', 'container_title': 'Season 2',
             'content_index': 2, 'description': '', 'id': 3, 'img_src': '', 'parent_container_id': 2,
             'season_index': 2}], 'content': [], 'parent_containers': [
            {'container_id': None, 'container_path': '/tv_shows/Duck Stories', 'container_title': 'Duck Stories',
             'content_id': None, 'content_index': None, 'description': '', 'id': 2, 'img_src': '',
             'parent_container_id': None, 'tag_title': 'tv', 'user_tags': 'tv,tv show', 'user_tags_id': 3}]} == data

    def test_build_season_content(self):
        client = self.app.test_client()
        payload = {
            "tag_list": [],
            "content_txt_search": "",
            "container_dict": {"container_id": 1}
        }

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.QUERY_DB.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        assert {'containers': [], 'content': [
            {'container_id': None, 'content_directory_id': 1, 'content_id': 1, 'content_index': 1,
             'content_src': '/tv_shows/Duck Stories/Duck Stories - s01e001.mp4', 'content_title': 'Test Tile',
             'content_url': 'http://localhost:8000', 'description': '', 'id': 1, 'img_src': '',
             'img_url': 'http://localhost:8000/', 'parent_container_id': 1, 'play_count': 0, 'tag_title': 'episode',
             'user_tags': 'episode', 'user_tags_id': 1},
            {'container_id': None, 'content_directory_id': 1, 'content_id': 2, 'content_index': 2,
             'content_src': '/tv_shows/Duck Stories/Duck Stories - s01e002.mp4', 'content_title': 'Test Tile',
             'content_url': 'http://localhost:8000', 'description': '', 'id': 2, 'img_src': '',
             'img_url': 'http://localhost:8000/', 'parent_container_id': 1, 'play_count': 0, 'tag_title': 'episode',
             'user_tags': 'episode', 'user_tags_id': 1},
            {'container_id': None, 'content_directory_id': 2, 'content_id': 15, 'content_index': 3,
             'content_src': '/tv_shows/Duck Stories/Duck Stories - s01e003.mp4', 'content_title': 'Test Tile',
             'content_url': 'http://localhost:8002', 'description': '', 'id': 15, 'img_src': '',
             'img_url': 'http://localhost:8002/', 'parent_container_id': 1, 'play_count': 0, 'tag_title': 'episode',
             'user_tags': 'episode', 'user_tags_id': 1},
            {'container_id': None, 'content_directory_id': 2, 'content_id': 16, 'content_index': 4,
             'content_src': '/tv_shows/Duck Stories/Duck Stories - s01e004.mp4', 'content_title': 'Test Tile',
             'content_url': 'http://localhost:8002', 'description': '', 'id': 16, 'img_src': '',
             'img_url': 'http://localhost:8002/', 'parent_container_id': 1, 'play_count': 0, 'tag_title': 'episode',
             'user_tags': 'episode', 'user_tags_id': 1}], 'parent_containers': [
            {'container_id': None, 'container_path': '/tv_shows/Duck Stories', 'container_title': 'Duck Stories',
             'content_id': None, 'content_index': None, 'description': '', 'id': 2, 'img_src': '',
             'parent_container_id': None, 'tag_title': 'tv', 'user_tags': 'tv,tv show', 'user_tags_id': 3},
            {'container_id': 1, 'container_path': '/tv_shows/Duck Stories', 'container_title': 'Season 1',
             'content_id': None, 'content_index': 1, 'description': '', 'id': 1, 'img_src': '',
             'parent_container_id': 2, 'tag_title': 'season', 'user_tags': 'season', 'user_tags_id': 2}]} == data

    def test_build_movie_content(self):
        client = self.app.test_client()
        payload = {
            "tag_list": ["movie"],
            "content_txt_search": "",
            "container_dict": {},
            "container_txt_search": ""
        }

        # The client handles the request context for you
        response = client.post(
            main_routes.APIEndpoints.QUERY_DB.value,
            json=payload
        )

        assert response.status_code == 200
        data = response.get_json()
        assert {'containers': [], 'content': [{'container_id': None, 'content_directory_id': 1, 'content_id': 10,
                                               'content_src': '/movies/Boogers (2012).mp4', 'content_title': 'Boogers',
                                               'content_url': 'http://localhost:8000', 'description': '2012', 'id': 10,
                                               'img_src': '', 'img_url': 'http://localhost:8000/', 'play_count': 0,
                                               'tag_title': 'movie', 'user_tags': 'movie', 'user_tags_id': 5},
                                              {'container_id': None, 'content_directory_id': 1, 'content_id': 11,
                                               'content_src': '/movies/Leonard (2014).mp4', 'content_title': 'Leonard',
                                               'content_url': 'http://localhost:8000', 'description': '2014', 'id': 11,
                                               'img_src': '', 'img_url': 'http://localhost:8000/', 'play_count': 0,
                                               'tag_title': 'movie', 'user_tags': 'movie', 'user_tags_id': 5},
                                              {'container_id': None, 'content_directory_id': 1, 'content_id': 12,
                                               'content_src': '/movies/Leonard 2 (2016).mp4',
                                               'content_title': 'Leonard 2', 'content_url': 'http://localhost:8000',
                                               'description': '2016', 'id': 12,
                                               'img_src': '/movies/Leonard 2 (2016).mp4.jpg',
                                               'img_url': 'http://localhost:8000//movies/Leonard 2 (2016).mp4.jpg',
                                               'play_count': 0, 'tag_title': 'movie', 'user_tags': 'movie',
                                               'user_tags_id': 5}]} == data
