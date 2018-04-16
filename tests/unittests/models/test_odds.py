from mock import patch
from unittest2 import TestCase
from arbi.models.odds import Odds

class OddsTest(TestCase):
    def setUp(self):
        self.init_record_dict = {
            'event_type': 'FT',
            'odds_type': 'AH',
            'bookie_id': '2',
            'bet_data': 'abc!A123',
            'dish': -0.5,
            'o1': 2.000,
            'o2': 1.950,
            'o3': -2.000,
            'lay_flag': False
        }
        self.update_record_dict1 = {
            'event_type': 'HT',
            'odds_type': '1x2',
            'bookie_id': '69',
            'bet_data': 'abd!A124',
            'dish': None,
            'o1': 3.100,
            'o2': 2.500,
            'o3': 2.700,
            'lay_flag': False
        }
        self.update_record_dict2 = {
            'event_type': 'FT',
            'odds_type': 'AH',
            'bookie_id': '2',
            'bet_data': 'abe!A125',
            'dish': -0.75,
            'o1': 2.300,
            'o2': 1.650,
            'o3': -3.000,
            'lay_flag': False
        }
        self.update_record_dict3 = {
            'event_type': 'FT',
            'odds_type': 'AH',
            'bookie_id': '5',
            'bet_data': 'abf!A126',
            'dish': -0.5,
            'o1': 1.950,
            'o2': 2.000,
            'o3': -2.000,
            'lay_flag': False
        }
        self.mock_time = 1234567

    def test_init(self):
        with patch('time.time', return_value=self.mock_time):
            odds = Odds(self.init_record_dict)
        expected_odds_dict = {
            ('FT', 'AH'): {
                -0.5: {'2': ([2.0, 1.95], 'abc!A123', self.mock_time)}
            }
        }
        self.assertEqual(odds.odds_dict, expected_odds_dict)

    def test_update(self):
        with patch('time.time', return_value=self.mock_time):
            odds = Odds(self.init_record_dict)
            odds.update_with_dict(self.update_record_dict1)
            odds.update_with_dict(self.update_record_dict2)
            odds.update_with_dict(self.update_record_dict3)

        expected_odds_dict = {
            ('FT', 'AH'): {
                -0.5: {
                    '2': ([2.0, 1.95], 'abc!A123', self.mock_time),
                    '5': ([1.95, 2.0], 'abf!A126', self.mock_time),
                },
                -0.75: {
                    '2': ([2.3, 1.65], 'abe!A125', self.mock_time),
                }
            },
            ('HT', '1x2'): {
                None: {'69': ([3.1, 2.5, 2.7], 'abd!A124', self.mock_time)}
            },
        }
        self.assertEqual(odds.odds_dict, expected_odds_dict)

    def test_update_betfair_odds(self):
        """betfair AH odds is different from traditional bookies - it doesn't count current scores.
        """
        # no goal difference information
        init_record_dict = {
            'event_type': 'FT', 'odds_type': 'AH', 'bookie_id': '7', 'bet_data': 'abc!A123',
            'dish': -0.5, 'o1': 2.000, 'o2': 1.950, 'o3': -2.0, 'lay_flag': False
        }
        odds = Odds(init_record_dict)
        self.assertEqual(odds.odds_dict, {})

        # 0: 0
        update_record_dict0 = {
            'event_type': 'FT', 'odds_type': 'AH', 'bookie_id': '7', 'bet_data': 'abc!A123',
            'dish': -0.5, 'o1': 2.000, 'o2': 1.950, 'o3': -2.0, 'lay_flag': False
        }
        update_record_dict1 = {
            'event_type': 'FT', 'odds_type': 'AH', 'bookie_id': '7', 'bet_data': 'abd!A124',
            'dish': -0.5, 'o1': 2.100, 'o2': 2.000, 'o3': -2.0, 'lay_flag': True
        }
        with patch('time.time', return_value=self.mock_time):
            odds.update_with_dict(update_record_dict0, 0)
            odds.update_with_dict(update_record_dict1, 0)

        expected_odds_dict = {
            ('FT', 'AH'): {
                -0.5: {
                    '7': ([2.0, 1.95], 'abc!A123', self.mock_time),
                    '7 lay': ([2.1, 2.0], 'abd!A124', self.mock_time),
                },
            },
        }
        self.assertEqual(odds.odds_dict, expected_odds_dict)

        # 1: 0
        update_record_dict0 = {
            'event_type': 'FT', 'odds_type': 'AH', 'bookie_id': '7', 'bet_data': 'abe!A125',
            'dish': -1.5, 'o1': 2.300, 'o2': 1.650, 'o3': -6.000, 'lay_flag': False
        }
        update_record_dict1 = {
            'event_type': 'FT', 'odds_type': 'AH', 'bookie_id': '7', 'bet_data': 'abf!A126',
            'dish': -1.5, 'o1': 2.40, 'o2': 1.70, 'o3': -6.000, 'lay_flag': True
        }
        with patch('time.time', return_value=self.mock_time):
            odds.update_with_dict(update_record_dict0, 1)
            odds.update_with_dict(update_record_dict1, 1)

        expected_odds_dict = {
            ('FT', 'AH'): {
                -0.5: {
                    '7': ([2.3, 1.65], 'abe!A125', self.mock_time),
                    '7 lay': ([2.4, 1.7], 'abf!A126', self.mock_time),
                },
            },
        }
        self.assertEqual(odds.odds_dict, expected_odds_dict)

        # 1: 0
        update_record_dict0 = {
            'event_type': 'FT', 'odds_type': 'AH', 'bookie_id': '7', 'bet_data': 'abe!A127',
            'dish': -0.5, 'o1': 1.300, 'o2': 2.650, 'o3': -2.000, 'lay_flag': False
        }
        update_record_dict1 = {
            'event_type': 'FT', 'odds_type': 'AH', 'bookie_id': '7', 'bet_data': 'abf!A128',
            'dish': -0.5, 'o1': 1.40, 'o2': 2.70, 'o3': -2.000, 'lay_flag': True
        }
        with patch('time.time', return_value=self.mock_time):
            odds.update_with_dict(update_record_dict0, 1)
            odds.update_with_dict(update_record_dict1, 1)

        expected_odds_dict = {
            ('FT', 'AH'): {
                -0.5: {
                    '7': ([2.3, 1.65], 'abe!A125', self.mock_time),
                    '7 lay': ([2.4, 1.7], 'abf!A126', self.mock_time),
                },
                0.5: {
                    '7': ([1.3, 2.65], 'abe!A127', self.mock_time),
                    '7 lay': ([1.4, 2.7], 'abf!A128', self.mock_time),
                },
            },
        }
        self.assertEqual(odds.odds_dict, expected_odds_dict)

    def test_get_odds_details_unknown_bookie_id(self):
        odds = Odds(self.init_record_dict)
        dict_with_unknown_bookie_id = {
            'event_type': 'FT',
            'odds_type': 'AH',
            'bookie_id': '999',
            'bet_data': 'ab!A12',
            'dish': -0.5,
            'o1': 1.950,
            'o2': 2.000,
            'o3': -2.000,
            'lay_flag': False
        }
        odds_details = odds.get_odds_details(dict_with_unknown_bookie_id)
        self.assertIsNone(odds_details)

    # def test_get_odds_details_unknown_odds_type(self):
    #     odds = Odds(self.init_record_dict)
    #     dict_with_unknown_odds_type = {
    #         'event_type': 'FT',
    #         'odds_type': 'BLA',
    #         'bookie_id': '2',
    #         'bet_data': 'ab!A12',
    #         'dish': -0.5,
    #         'o1': 1.950,
    #         'o2': 2.000,
    #         'o3': -2.000,
    #         'lay_flag': False
    #     }
    #     odds_details = odds.get_odds_details(dict_with_unknown_odds_type)
    #     self.assertIsNone(odds_details)
