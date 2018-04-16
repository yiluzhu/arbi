# -*- coding: utf-8 -*-

from mock import Mock, patch
from unittest2 import TestCase
from arbi.tools.tc.web.web_api import VIPMatchMappingAPI


class VIPMatchMappingAPITest(TestCase):
    def test_map_sporttery_data_all_found(self):
        mock_data = {
            "matchCount": 2,
            "Result": [
                {
                    "itemCount": 1,
                    "matchInfo": [{"VIPmatchID": "972960", "Status": 0, "matchTime": "2016-02-20 03:30"}],
                    "teamInfo": [
                        {"Source": u"奥德汉姆", "vipID": 88, "nameEN": "Oldham", "nameTC": u"奥德汉姆", "nameSC": u"奥德汉姆"},
                        {"Source": u"彼得堡联", "vipID": 2513, "nameEN": "Peterborough", "nameTC": u"彼得堡联", "nameSC": u"彼得堡联"}
                    ]
                },
                {
                    "itemCount": 1,
                    "matchInfo": [{"VIPmatchID": "981300", "Status": 0, "matchTime": "2016-02-20 22:30"}],
                    "teamInfo": [
                        {"Source": u"洛克伦", "vipID": 39057, "nameEN": "Lokeren", "nameTC": u"洛克伦", "nameSC": u"洛克伦"},
                        {"Source": u"圣图尔登", "vipID": 20753, "nameEN": "Sint-Truiden", "nameTC": u"圣图尔登", "nameSC": u"圣图尔登"}
                    ]
                }
            ]
        }

        VIPMatchMappingAPI._request = Mock(return_value=mock_data)
        api = VIPMatchMappingAPI()

        sporttery_data = [
            ('2016-11-26 23:00', u'英甲', u'奥德汉姆', u'彼得堡联',
             {('FT', 'EH'): {1.0: {'99': [1.43, 4.1, 5.4]}}, ('FT', '1x2'): {None: {'99': [2.54, 3.05, 2.45]}}}),
            ('2016-11-27 03:00', u'比甲', u'洛克伦', u'圣图尔登',
             {('FT', 'EH'): {-1.0: {'99': [3.8, 3.55, 1.71]}}, ('FT', '1x2'): {None: {'99': [1.9, 3.25, 3.4]}}}),
        ]

        result = api.map_sporttery_data(sporttery_data)

        expected_url = 'http://14.102.249.58/admin/api/getvipmatchid'
        expected_params = u'奥德汉姆,彼得堡联,2016-11-26 23:00;洛克伦,圣图尔登,2016-11-27 03:00'
        expected_result = [
            ('972960', {('FT', '1x2'): {None: {'99': [2.54, 3.05, 2.45]}}, ('FT', 'EH'): {1.0: {'99': [1.43, 4.1, 5.4]}}}),
            ('981300', {('FT', '1x2'): {None: {'99': [1.9, 3.25, 3.4]}}, ('FT', 'EH'): {-1.0: {'99': [3.8, 3.55, 1.71]}}})
        ]

        VIPMatchMappingAPI._request.assert_called_once_with(expected_url, expected_params)
        self.assertEqual(expected_result, result)

    def test_map_sporttery_data_1_missing(self):
        mock_data = {
            "matchCount": 1,
            "Result": [
                {
                    "itemCount": 1,
                    "matchInfo": [{"VIPmatchID": "1274029", "Status": 0, "matchTime": "2016-12-04 11:30"}],
                    "teamInfo": [
                        {"Source": "金泽塞维", "vipID": 12445, "nameEN": "Zweigen", "nameTC": "金澤", "nameSC": "金泽"},
                        {"Source": "枥木SC", "vipID": 8592, "nameEN": "Tochigi", "nameTC": "櫪木SC", "nameSC": "枥木SC"}
                    ]
                },
                {
                    "itemCount": 0,
                    "matchInfo": []
                }
            ]
        }

        VIPMatchMappingAPI._request = Mock(return_value=mock_data)
        api = VIPMatchMappingAPI()

        sporttery_data = [
            ('2016-12-04 11:30', u'日乙', u'金泽塞维', u'枥木SC',
             {('FT', 'EH'): {1.0: {'99': [1.43, 4.1, 5.4]}}, ('FT', '1x2'): {None: {'99': [2.54, 3.05, 2.45]}}}),
            ('2016-11-27 03:00', u'不存在', u'不存在A', u'不存在B',
             {('FT', 'EH'): {-1.0: {'99': [3.8, 3.55, 1.71]}}, ('FT', '1x2'): {None: {'99': [1.9, 3.25, 3.4]}}}),
        ]

        with patch('arbi.tools.tc.web.web_api.log') as mock_log:
            result = api.map_sporttery_data(sporttery_data)

        expected_url = 'http://14.102.249.58/admin/api/getvipmatchid'
        expected_params = u'金泽塞维,枥木SC,2016-12-04 11:30;不存在A,不存在B,2016-11-27 03:00'
        expected_warning = u'No VIP match ID found for match: 不存在, 2016-11-27 03:00, 不存在A vs 不存在B'
        expected_result = [
            ('1274029', {('FT', '1x2'): {None: {'99': [2.54, 3.05, 2.45]}}, ('FT', 'EH'): {1.0: {'99': [1.43, 4.1, 5.4]}}}),
        ]

        VIPMatchMappingAPI._request.assert_called_once_with(expected_url, expected_params)
        mock_log.warning.assert_called_once_with(expected_warning)
        self.assertEqual(expected_result, result)

    def test_map_sporttery_data_no_found(self):
        mock_data = {
            "matchCount": 0,
            "Result": [
                {"itemCount": 0, "matchInfo": []}
            ]
        }

        VIPMatchMappingAPI._request = Mock(return_value=mock_data)
        api = VIPMatchMappingAPI()

        sporttery_data = [
            ('2016-11-27 03:00', u'不存在', u'不存在A', u'不存在B',
             {('FT', 'EH'): {-1.0: {'99': [3.8, 3.55, 1.71]}}, ('FT', '1x2'): {None: {'99': [1.9, 3.25, 3.4]}}}),
        ]

        with patch('arbi.tools.tc.web.web_api.log') as mock_log:
            result = api.map_sporttery_data(sporttery_data)

        expected_url = 'http://14.102.249.58/admin/api/getvipmatchid'
        expected_params = u'不存在A,不存在B,2016-11-27 03:00'
        expected_warning = 'No info found from VIP match ID API for: 不存在A,不存在B,2016-11-27 03:00'

        VIPMatchMappingAPI._request.assert_called_once_with(expected_url, expected_params)
        mock_log.warning.assert_called_once_with(expected_warning)
        self.assertEqual([], result)

    def test_validate_api_response_data(self):
        data = {"matchCount": 0, "Result": "Error"}

        api = VIPMatchMappingAPI()

        with patch('arbi.tools.tc.web.web_api.log') as mock_log:
            result = api.validate_api_response_data(data, 'dummy;params')

        expected_error = 'Error when matching from VIP match ID API for: dummy;params'

        mock_log.error.assert_called_once_with(expected_error)
        self.assertEqual(False, result)

    def test_validate_api_response_data_None(self):
        data = None
        api = VIPMatchMappingAPI()
        result = api.validate_api_response_data(data, 'dummy;params')

        self.assertEqual(False, result)
