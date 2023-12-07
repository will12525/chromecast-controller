from unittest import TestCase
import webpage_builder


class Test(TestCase):

    def test_build_media_menu_content(self):
        print(webpage_builder.build_media_menu_content({"content_type": webpage_builder.ContentType.SEASON,
                                                        "media_id": 1}))
        print(webpage_builder.build_media_menu_content({"content_type": webpage_builder.ContentType.MOVIE}))
        print(webpage_builder.build_media_menu_content({"content_type": webpage_builder.ContentType.TV_SHOW}))

    def test_build_movie_menu_content(self):
        print(webpage_builder.build_media_menu_content({"content_type": webpage_builder.ContentType.MOVIE}))

    def test_load_content_type(self):
        print(webpage_builder.ContentType(1))

    def test_build_MOVIE_content(self):
        request_args = {'content_type': webpage_builder.ContentType.MOVIE}
        main_content = webpage_builder.build_main_content(request_args)
        print(main_content)
        assert main_content

    def test_build_TV_SHOW_content(self):
        request_args = {'content_type': webpage_builder.ContentType.TV_SHOW}
        main_content = webpage_builder.build_main_content(request_args)
        print(main_content)
        assert main_content

    def test_build_SEASON_content(self):
        request_args = {'media_id': 1, 'content_type': webpage_builder.ContentType.SEASON}
        main_content = webpage_builder.build_main_content(request_args)
        print(main_content)
        assert main_content

    def test_build_MEDIA_content(self):
        request_args = {'media_id': 1, 'content_type': webpage_builder.ContentType.MEDIA}
        main_content = webpage_builder.build_main_content(request_args)
        print(main_content)
        assert main_content
