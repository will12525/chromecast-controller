import inspect
from unittest import TestCase
import flask_endpoints
from flask import Flask

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
    template = "index.html"
    app = None

    def setUp(self) -> None:
        self.app = Flask(__name__)
        # Wait for the setup_thread to finish so the database is fully populated for testing
        flask_endpoints.setup_thread.join()


class Test(TestWebpageBuilder):

    def test_build_media_menu_content(self):
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            assert flask_endpoints.build_main_content({"content_type": flask_endpoints.ContentType.TV_SHOW.value,
                                                       "media_id": 1})
            assert flask_endpoints.build_main_content({"content_type": flask_endpoints.ContentType.MOVIE.value})
            assert flask_endpoints.build_main_content({"content_type": flask_endpoints.ContentType.TV.value})

    def test_build_movie_menu_content(self):
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            assert isinstance(
                flask_endpoints.build_main_content({"content_type": flask_endpoints.ContentType.MOVIE.value}), str)

    def test_build_MOVIE_content(self):
        html_as_string = load_file()
        assert html_as_string
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            request_args = {"content_type": flask_endpoints.ContentType.MOVIE.value}
            main_content = flask_endpoints.build_main_content(request_args)
            assert main_content
            print_differences(main_content, html_as_string)
            if SAVE_FILES:
                save_to_file(main_content)
            assert main_content == html_as_string

    def test_build_TV_SHOW_content(self):
        html_as_string = load_file()
        assert html_as_string
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            request_args = {"content_type": flask_endpoints.ContentType.TV.value}
            main_content = flask_endpoints.build_main_content(request_args)
            assert main_content
            print_differences(main_content, html_as_string)
            if SAVE_FILES:
                save_to_file(main_content)
            assert main_content == html_as_string

    def test_build_SEASON_content(self):
        html_as_string = load_file()
        assert html_as_string
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            request_args = {'media_id': 1, "content_type": flask_endpoints.ContentType.TV_SHOW.value}
            main_content = flask_endpoints.build_main_content(request_args)
            assert main_content
            print_differences(main_content, html_as_string)
            if SAVE_FILES:
                save_to_file(main_content)
            assert main_content == html_as_string

    def test_build_MEDIA_content(self):
        html_as_string = load_file()
        assert html_as_string
        with self.app.app_context(), self.app.test_request_context():
            self.app.jinja_env.lstrip_blocks = True
            self.app.jinja_env.trim_blocks = True
            request_args = {'media_id': 1, "content_type": flask_endpoints.ContentType.SEASON.value}
            main_content = flask_endpoints.build_main_content(request_args)
            assert main_content
            print_differences(main_content, html_as_string)
            if SAVE_FILES:
                save_to_file(main_content)
            assert main_content == html_as_string
