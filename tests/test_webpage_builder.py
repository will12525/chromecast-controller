from unittest import TestCase
import webpage_builder


class Test(TestCase):
    def test_build_tv_show_season_menu(self):
        tv_show_season_card_block = webpage_builder.build_tv_show_season_menu(1)
        print(tv_show_season_card_block)
        self.assertTrue(tv_show_season_card_block)
