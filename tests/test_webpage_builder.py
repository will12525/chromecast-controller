from unittest import TestCase
import webpage_builder
from flask import Flask


class TestWebpageBuilder(TestCase):
    template = "index.html"
    app = None

    def setUp(self) -> None:
        self.app = Flask(__name__)


class Test(TestWebpageBuilder):

    def test_build_media_menu_content(self):
        with self.app.app_context(), self.app.test_request_context():
            print(webpage_builder.build_main_content({"content_type": webpage_builder.ContentType.TV_SHOW.value,
                                                      "media_id": 1}))
            print(webpage_builder.build_main_content({"content_type": webpage_builder.ContentType.MOVIE.value}))
            print(webpage_builder.build_main_content({"content_type": webpage_builder.ContentType.TV.value}))

    def test_build_movie_menu_content(self):
        with self.app.app_context(), self.app.test_request_context():
            print(type(
                webpage_builder.build_main_content
                ({"content_type": webpage_builder.ContentType.MOVIE.value}, self.template)))

    def test_load_content_type(self):
        print(webpage_builder.ContentType(1))

    def test_build_MOVIE_content(self):
        with self.app.app_context(), self.app.test_request_context():
            request_args = {"content_type": webpage_builder.ContentType.MOVIE.value}
            main_content = webpage_builder.build_main_content(request_args)
            print(main_content)
            assert main_content

    def test_build_TV_SHOW_content(self):
        with self.app.app_context(), self.app.test_request_context():
            request_args = {"content_type": webpage_builder.ContentType.TV.value}
            main_content = webpage_builder.build_main_content(request_args)
            print(main_content)
            assert main_content

    def test_build_SEASON_content(self):
        with self.app.app_context(), self.app.test_request_context():
            request_args = {'media_id': 1, "content_type": webpage_builder.ContentType.TV_SHOW.value}
            main_content = webpage_builder.build_main_content(request_args)
            print(main_content)
            assert main_content

    def test_build_MEDIA_content(self):
        with self.app.app_context(), self.app.test_request_context():
            request_args = {'media_id': 1, "content_type": webpage_builder.ContentType.SEASON.value}
            main_content = webpage_builder.build_main_content(request_args)
            print(main_content)
            assert main_content
