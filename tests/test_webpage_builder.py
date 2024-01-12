import inspect
from unittest import TestCase

from werkzeug.datastructures.structures import ImmutableMultiDict

import flask_endpoints
from flask import Flask

from database_handler import common_objects
import __init__

SAVE_FILES = False


def load_file():
    with open(f'templates/{inspect.stack()[1].function}.html', 'r') as file:  # r to open file in READ mode
        return file.read()


def save_to_file(output):
    file_name = f"templates/{inspect.stack()[1].function}.html"
    if SAVE_FILES:
        f"templates/{inspect.stack()[1].function}_gen.html"
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


class TestWebpageBuilder(TestCase):
    DB_PATH = "media_metadata.db"
    template = "index.html"
    app = None

    def setUp(self) -> None:
        # if os.path.exists(self.DB_PATH):
        #     os.remove(self.DB_PATH)
        __init__.patch_get_file_hash(self)
        __init__.patch_get_ffmpeg_metadata(self)
        __init__.patch_move_media_file(self)
        __init__.patch_collect_tv_shows(self)
        __init__.patch_collect_new_tv_shows(self)
        __init__.patch_collect_movies(self)

        self.app = Flask(__name__)
        # Wait for the setup_thread to finish so the database is fully populated for testing
        flask_endpoints.setup_thread.join()


class Test(TestWebpageBuilder):

    def test_build_media_menu_content(self):
        data = ImmutableMultiDict(
            [('content_type', common_objects.ContentType.TV_SHOW.value), (common_objects.ID_COLUMN, 1)])
        data2 = ImmutableMultiDict([('content_type', common_objects.ContentType.MOVIE.value)])
        data3 = ImmutableMultiDict([('content_type', common_objects.ContentType.TV.value)])
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            assert flask_endpoints.build_main_content(data)
            assert flask_endpoints.build_main_content(data2)
            assert flask_endpoints.build_main_content(data3)

    def test_build_movie_menu_content(self):
        request_args = ImmutableMultiDict([('content_type', common_objects.ContentType.MOVIE.value)])
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            assert isinstance(flask_endpoints.build_main_content(request_args), str)

    def test_build_MOVIE_content(self):
        request_args = ImmutableMultiDict([('content_type', common_objects.ContentType.MOVIE.value)])
        html_as_string = load_file()
        assert html_as_string
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            main_content = flask_endpoints.build_main_content(request_args)
            assert main_content
            print_differences(main_content, html_as_string)
            if SAVE_FILES:
                save_to_file(main_content)
            assert main_content == html_as_string

    def test_build_TV_SHOW_content(self):
        request_args = ImmutableMultiDict([('content_type', common_objects.ContentType.TV.value)])
        html_as_string = load_file()
        assert html_as_string
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            main_content = flask_endpoints.build_main_content(request_args)

            assert main_content
            print_differences(main_content, html_as_string)
            if SAVE_FILES:
                save_to_file(main_content)
            assert main_content == html_as_string

    def test_build_SEASON_content(self):
        request_args = ImmutableMultiDict(
            [('content_type', common_objects.ContentType.TV_SHOW.value), (common_objects.MEDIA_ID_COLUMN, 1)])
        html_as_string = load_file()
        assert html_as_string
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True

            main_content = flask_endpoints.build_main_content(request_args)
            assert main_content
            print_differences(main_content, html_as_string)
            if SAVE_FILES:
                save_to_file(main_content)
            assert main_content == html_as_string

    def test_build_MEDIA_content(self):
        request_args = ImmutableMultiDict(
            [('content_type', common_objects.ContentType.SEASON.value), (common_objects.MEDIA_ID_COLUMN, 1)])
        html_as_string = load_file()
        assert html_as_string
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            main_content = flask_endpoints.build_main_content(request_args)
            assert main_content
            print_differences(main_content, html_as_string)
            if SAVE_FILES:
                save_to_file(main_content)
            assert main_content == html_as_string
