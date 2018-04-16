# -*- coding: utf-8 -*-

from mock import patch, ANY, Mock
from unittest2 import TestCase
from arbi.tools.tc.web.scraper import SportteryScraper


class MockRow(object):
    def __init__(self, lst):
        self.lst = lst

    def findAll(self, text):
        return self.lst

mock_datetime = Mock()
mock_datetime.now.return_value = Mock(year=2016)


class SportteryScraperTest(TestCase):

    def setUp(self):
        SportteryScraper.get_driver = lambda *args: Mock()

    def test_get_match_data(self):
        rows = [
            MockRow([u'周六 2016-11-26 [共', u'35', u'场比赛] ', u'隐藏']),
            MockRow([u'周六', u'039', u'英甲', u'11-26', u'23:00', u'\xa0-1\xb0', u'奥德汉姆', u' VS ', u'彼得堡联',
                     u'0', u'+1', u'2.54', u'3.05', u'2.45', u'1.43', u'4.10', u'5.40', u'\u6b27', u' ', u'\u4e9a', u'\u8baf', u' ', u'\u540c',
                     u'15%', u'29%', u'56%', u'25%', u'25%', u'49%', u'\xa0']),
            MockRow([u'周六', u'067', u'比甲', u'11-27', u'03:00', u'未知', u'\xa05\xb0', u'洛克伦', u' VS ', u'圣图尔登',
                     u'0', u'-1', u'1.90', u'3.25', u'3.40', u'3.80', u'3.55', u'1.71', u'\u6b27', u' ', u'\u4e9a', u'\u8baf', u' ', u'\u540c',
                     u'55%', u'38%', u'7%', u'24%', u'57%', u'19%', u'\xa0']),
        ]

        scraper = SportteryScraper()
        SportteryScraper.get_effective_price = lambda self, price: float(price)

        with patch('datetime.datetime', mock_datetime):
            result = scraper.get_match_data(rows)

        expected = [
            ('2016-11-26 23:00', u'英甲', u'奥德汉姆', u'彼得堡联',
             {('FT', 'EH'): {1.0: {'99': ([1.43, 4.1, 5.4], 'sporttery', ANY)}},
              ('FT', '1x2'): {None: {'99': ([2.54, 3.05, 2.45], 'sporttery', ANY)}}}),
            ('2016-11-27 03:00', u'比甲', u'洛克伦', u'圣图尔登',
             {('FT', 'EH'): {-1.0: {'99': ([3.8, 3.55, 1.71], 'sporttery', ANY)}},
              ('FT', '1x2'): {None: {'99': ([1.9, 3.25, 3.4], 'sporttery', ANY)}}}),
        ]
        self.assertEqual(expected, result)

    def test_get_match_data_with_unopened_1x2(self):
        rows = [
            MockRow([u'周六', u'039', u'英甲', u'11-26', u'23:00', u'\xa0-1\xb0', u'奥德汉姆', u' VS ', u'彼得堡联',
                     u'未开赛', u'+1', u'--', u'--', u'--', u'1.43', u'4.10', u'5.40', u'\u6b27', u' ', u'\u4e9a', u'\u8baf', u' ', u'\u540c',
                     u'15%', u'29%', u'56%', u'25%', u'25%', u'49%', u'\xa0']),
        ]

        scraper = SportteryScraper()
        SportteryScraper.get_effective_price = lambda self, price: float(price)

        with patch('datetime.datetime', mock_datetime):
            result = scraper.get_match_data(rows)

        expected = [
            ('2016-11-26 23:00', u'英甲', u'奥德汉姆', u'彼得堡联',
             {('FT', 'EH'): {1.0: {'99': ([1.43, 4.1, 5.4], 'sporttery', ANY)}}}),
        ]
        self.assertEqual(expected, result)

    def test_get_match_data_with_unopened_EH(self):
        rows = [
            MockRow([u'周六 2016-11-26 [共', u'35', u'场比赛] ', u'隐藏']),
            MockRow([u'周六', u'067', u'比甲', u'11-27', u'03:00', u'未知', u'\xa05\xb0', u'洛克伦', u' VS ', u'圣图尔登',
                     u'0', u'未开赛', u'1.90', u'3.25', u'3.40', u'--', u'--', u'--', u'\u6b27', u' ', u'\u4e9a', u'\u8baf', u' ', u'\u540c',
                     u'55%', u'38%', u'7%', u'24%', u'57%', u'19%', u'\xa0']),
        ]

        scraper = SportteryScraper()
        SportteryScraper.get_effective_price = lambda self, price: float(price)

        with patch('datetime.datetime', mock_datetime):
            result = scraper.get_match_data(rows)

        expected = [
            ('2016-11-27 03:00', u'比甲', u'洛克伦', u'圣图尔登',
             {('FT', '1x2'): {None: {'99': ([1.9, 3.25, 3.4], 'sporttery', ANY)}}}),
        ]
        self.assertEqual(expected, result)

    def test_get_match_data_with_rank(self):
        rows = [
            MockRow([u'周六 2016-11-26 [共', u'35', u'场比赛] ', u'隐藏']),
            MockRow([u'周六', u'039', u'英甲', u'11-26', u'23:00', u'\xa0-1\xb0', u'奥德汉姆', u' VS ', u'彼得堡联',
                     u'0', u'+1', u'2.54', u'3.05', u'2.45', u'1.43', u'4.10', u'5.40', u'\u6b27', u' ', u'\u4e9a', u'\u8baf', u' ', u'\u540c',
                     u'15%', u'29%', u'56%', u'25%', u'25%', u'49%', u'\xa0']),
            MockRow([u'周日', u'025', u'意甲', u'02-26', u'22:00', u'\xa012\xb0', u'[意甲11]', u'切沃', u' VS ', u'佩斯卡拉', u'[意甲20]',
                     u'0', u'-1', u'1.65', u'3.65', u'4.02', u'3.05', u'3.58', u'1.92', u'\u6b27', u' ', u'\u4e9a', u'\u8baf', u' ', u'\u540c',
                     u'69%', u'15%', u'16%', u'49%', u'29%', u'23%', u'\xa0']),
        ]

        scraper = SportteryScraper()
        SportteryScraper.get_effective_price = lambda self, price: float(price)

        with patch('datetime.datetime', mock_datetime):
            result = scraper.get_match_data(rows)

        expected = [
            ('2016-11-26 23:00', u'英甲', u'奥德汉姆', u'彼得堡联',
             {('FT', 'EH'): {1.0: {'99': ([1.43, 4.1, 5.4], 'sporttery', ANY)}},
              ('FT', '1x2'): {None: {'99': ([2.54, 3.05, 2.45], 'sporttery', ANY)}}}),
            ('2016-02-26 22:00', u'意甲', u'切沃', u'佩斯卡拉',
             {('FT', 'EH'): {-1.0: {'99': ([3.05, 3.58, 1.92], 'sporttery', ANY)}},
              ('FT', '1x2'): {None: {'99': ([1.65, 3.65, 4.02], 'sporttery', ANY)}}}),
        ]
        self.assertEqual(expected, result)

    def test_get_match_data_with_notice(self):
        rows = [
            MockRow([u'周日', u'025', u'意甲', u'02-26', u'22:00', u'\xa012\xb0', u'[意甲11]', u'切沃', u' VS ', u'佩斯卡拉', u'[意甲20]',
                     u'0', u'-1', u'1.65', u'3.65', u'4.02', u'3.05', u'3.58', u'1.92', u'\u6b27', u' ', u'\u4e9a', u'\u8baf', u' ', u'\u540c',
                     u'69%', u'15%', u'16%', u'49%', u'29%', u'23%', u'\xa0', u'\u4e2d\u7acb']),
        ]

        scraper = SportteryScraper()
        SportteryScraper.get_effective_price = lambda self, price: float(price)

        with patch('datetime.datetime', mock_datetime):
            result = scraper.get_match_data(rows)

        expected = [
            ('2016-02-26 22:00', u'意甲', u'切沃', u'佩斯卡拉',
             {('FT', 'EH'): {-1.0: {'99': ([3.05, 3.58, 1.92], 'sporttery', ANY)}},
              ('FT', '1x2'): {None: {'99': ([1.65, 3.65, 4.02], 'sporttery', ANY)}}}),
        ]
        self.assertEqual(expected, result)
