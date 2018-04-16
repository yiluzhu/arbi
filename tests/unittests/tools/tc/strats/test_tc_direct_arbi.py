import mock
from unittest2 import TestCase

from arbi.tools.tc.strats.tc_direct_arbi import TCDirectArbiStrategy

profit_threshold = 0.01


class TCDirectArbiStrategyTest(TestCase):
    def setUp(self):
        self.match_info = {
            'match_id': '001',
            'league_id': 'L01',
            'league_name': 'A Cup',
            'league_name_simp': 'A Cup',
            'home_team_id': 'T01',
            'home_team_name': 'A',
            'home_team_name_simp': 'A',
            'away_team_id': 'T02',
            'away_team_name': 'B',
            'away_team_name_simp': 'B',
            'is_in_running': True,
            'home_team_score': 0,
            'away_team_score': 0,
            'match_hk_time': 'bla',
            'running_time': '2h 5',
        }

    def test_spot_direct_arbi_no_sporttery(self):
        strat = TCDirectArbiStrategy(profit_threshold)
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'b1': ([2.05, 1.90], 'a!A1', 123.45),
                                  'b2': ([2.00, 1.95], 'b!A2', 678.90),
                                  'b3': ([1.94, 2.01], 'c!A3', 246.84),
                                 }
                           }
        }

        mock_bookie_id_map = {'b1': 'b1', 'b2': 'b2', 'b3': 'b3'}
        with mock.patch('arbi.constants.BOOKIE_ID_MAP', mock_bookie_id_map):
            opps = strat.spot_arbi(match)

        self.assertEqual(opps, [])

    def test_spot_direct_arbi(self):
        strat = TCDirectArbiStrategy(profit_threshold)
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'b1': ([2.05, 1.90], 'a!A1', 123.45),
                                  'b2': ([2.00, 1.95], 'b!A2', 678.90),
                                  'b3': ([1.94, 2.01], 'c!A3', 246.84),
                                  '99': ([1.95, 2.00], 'c!A3', 246.84),
                                 }
                           }
        }

        mock_bookie_id_map = {'b1': 'b1', 'b2': 'b2', 'b3': 'b3', '99': '99'}
        with mock.patch('arbi.constants.BOOKIE_ID_MAP', mock_bookie_id_map):
            opps = strat.spot_arbi(match)

        expected = [(0.01235, (('AH Home', 0.5, 'FT', 'b1', 49.4, 2.05, '', False),
                              ('AH Away', -0.5, 'FT', '99', 50.6, 2.0, '', False)))]
        self.assertEqual(opps, expected)

    def test_spot_direct_arbi_two_opps(self):
        strat = TCDirectArbiStrategy(profit_threshold)
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', 'OU'): {0.5: {'15': ([1.16, 10.0], 'a!A1', 123.45),
                                  '99': ([1.15, 6.0], 'a!A1', 123.45),
                                  '7': ([1.10, 10.5], 'c!A3', 246.84),
                                  '7 lay': ([1.11, 11.0], 'c!A4', 246.80),
                                 }
                           }
        }

        result = strat.spot_arbi(match)
        expected = [(0.03451, (('OU Over', 0.5, 'FT', '99', 90.1, 1.15, '', False),
                               ('OU Under', 0.5, 'FT', '7', 9.9, 10.5, '', False))),
                    (0.03139, (('OU Over', 0.5, 'FT', '99', 89.7, 1.15, '', False),
                               ('OU Under', 0.5, 'FT', '15', 10.3, 10.0, '', False)))]
        self.assertEqual(result, expected)

    def test_spot_direct_arbi_with_lay(self):
        strat = TCDirectArbiStrategy(profit_threshold)
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'b1': ([2.06, 1.89], 'a!A1', 123.45),
                                  '99': ([2.05, 1.90], 'a!A1', 123.45),
                                  'b2': ([2.00, 1.95], 'b!A2', 678.90),
                                  'b3': ([1.99, 1.96], 'c!A3', 246.84),
                                  'b3 lay': ([2.00, 1.97], 'c!A4', 246.80),
                                 }
                           }
        }

        mock_bookie_id_map = {'b1': 'b1', 'b2': 'b2', 'b3': 'b3', 'b3 lay': 'b3', '99': '99'}
        with mock.patch('arbi.constants.BOOKIE_ID_MAP', mock_bookie_id_map):
            opps = strat.spot_arbi(match)

        expected = [(0.01235, (('AH Home', 0.5, 'FT', '99', 49.4, 2.05, '', False),
                              ('AH Home', 0.5, 'FT', 'b3', 50.6, 2.00, '', True)))]
        self.assertEqual(opps, expected)

    def test_spot_direct_arbi_with_lay_and_betfair_commission(self):
        strat = TCDirectArbiStrategy(profit_threshold)
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', 'OU'): {0.5: {'15': ([1.16, 6.0], 'a!A1', 123.45),
                                  '99': ([1.15, 6.0], 'a!A1', 123.45),
                                  '7': ([1.10, 10.5], 'c!A3', 246.84),
                                  '7 lay': ([1.11, 11.0], 'c!A4', 246.80),
                                 }
                           }
        }

        result = strat.spot_arbi(match)
        expected = [(0.03451, (('OU Over', 0.5, 'FT', '99', 90.1, 1.15, '', False),
                               ('OU Under', 0.5, 'FT', '7', 9.9, 10.5, '', False)))]
        self.assertEqual(result, expected)

        # without 7 back price
        match.odds.odds_dict = {
            ('FT', 'OU'): {0.5: {'15': ([1.16, 6.0], 'a!A1', 123.45),
                                  '99': ([1.15, 6.0], 'a!A1', 123.45),
                                  '7 lay': ([1.11, 11.0], 'c!A4', 246.80),
                                 }
                           }
        }
        result = strat.spot_arbi(match)
        expected = [(0.0303, (('OU Over', 0.5, 'FT', '99', 89.8, 1.15, '', False),
                              ('OU Over', 0.5, 'FT', '7', 10.2, 1.11, '', True)))]
        self.assertEqual(result, expected)

    def test_spot_direct_arbi_with_lay_and_betfair_commission_and_AH(self):
        strat = TCDirectArbiStrategy(profit_threshold)
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'15': ([1.16, 6.0], 'a!A1', 123.45),
                                  '99': ([1.15, 6.0], 'a!A1', 123.45),
                                  '7': ([1.10, 10.5], 'c!A3', 246.84),
                                  '7 lay': ([1.11, 11.0], 'c!A4', 246.80),
                                 }
                           }
        }

        result = strat.spot_arbi(match)
        expected = [(0.03451, (('AH Home', 0.5, 'FT', '99', 90.1, 1.15, '', False),
                               ('AH Away', -0.5, 'FT', '7', 9.9, 10.5, '', False)))]
        self.assertEqual(result, expected)

        # without 7 back price
        match.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'15': ([1.15, 6.0], 'a!A1', 123.45),
                                  '99': ([1.15, 6.0], 'a!A1', 123.45),
                                  '7 lay': ([1.11, 11.0], 'c!A4', 246.80),
                                 }
                           }
        }
        result = strat.spot_arbi(match)
        expected = [(0.0303, (('AH Home', 0.5, 'FT', '99', 89.8, 1.15, '', False),
                              ('AH Home', 0.5, 'FT', '7', 10.2, 1.11, '', True)))]
        self.assertEqual(result, expected)

    def test_spot_direct_arbi_with_lay_regression(self):
        strat = TCDirectArbiStrategy(profit_threshold)
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', 'OU'): {2.5: {'99': ([2.05, 1.9], 'a!A1', 123.45),
                                  '7': ([1.94, 1.82], 'c!A3', 246.84),
                                  '7 lay': ([2.24, 2.08], 'c!A4', 246.80),
                                 }
                           }
        }

        result = strat.spot_arbi(match)
        self.assertEqual(result, [])

    def test_spot_direct_arbi_with_betfair_commission(self):
        strat = TCDirectArbiStrategy(profit_threshold)
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'99': ([2.05, 1.90], 'a!A1', 123.45),
                                  '7' : ([1.91, 2.04], 'c!A3', 246.84),
                                 }
                           }
        }

        opps = strat.spot_arbi(match)

        expected = [(0.01247, (('AH Home', 0.5, 'FT', '99', 49.9, 2.05, '', False),
                               ('AH Away', -0.5, 'FT', '7', 50.1, 2.04, '', False)))
                    ]
        self.assertEqual(opps, expected)

        # Compared with betfair, other bookie could give much higher profit
        match.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'99': ([2.05, 1.90], 'a!A1', 123.45),
                                  '37' : ([1.91, 2.04], 'c!A3', 246.84),
                                 }
                           }
        }

        opps = strat.spot_arbi(match)

        expected = [(0.02249, (('AH Home', 0.5, 'FT', '99', 49.9, 2.05, '', False),
                               ('AH Away', -0.5, 'FT', '37', 50.1, 2.04, '', False)))
                    ]
        self.assertEqual(opps, expected)

    def test_spot_direct_arbi_do_not_use_both_back_and_lay_prices(self):
        strat = TCDirectArbiStrategy(profit_threshold=0)
        match = mock.Mock()
        match.info = {'home_team_score': 0, 'away_team_score': 0}
        match.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'99': ([2.05, 1.90], 'a!A1', 123.45),
                                  'b1': ([2.05, 1.90], 'a!A1', 123.45),
                                  'b2': ([2.04, 1.91], 'b!A2', 678.90),
                                  'b3': ([1.96, 1.99], 'c!A3', 246.84),
                                  'b3 lay': ([2.00, 1.97], 'c!A4', 246.80),
                                 }
                           }
        }

        mock_bookie_id_map = {'b1': 'b1', 'b2': 'b2', 'b3': 'b3', 'b3 lay': 'b3', '99': '99'}
        patch1 = mock.patch('arbi.constants.BOOKIE_IDS_WITH_LAY_PRICES', ['b3'])
        patch2 = mock.patch('arbi.constants.BOOKIE_ID_MAP', mock_bookie_id_map)
        with patch1, patch2:
            opps = strat.spot_arbi(match)

        expected = [(0.01235, (('AH Home', 0.5, 'FT', '99', 49.4, 2.05, '', False),
                               ('AH Home', 0.5, 'FT', 'b3', 50.6, 2.00, '', True))),
                    # TODO update below comments
                    # This one would use b3 back so not allowed, as b3 lay is used already
                    # (0.00734, (('AH Home', 0.5, 'FT', 'b2', 49.4, 2.04, 'b!A2', False),
                    #            ('AH Away', -0.5, 'FT', 'b3', 50.6, 1.99, 'c!A3', False))),
                    ]
        self.assertEqual(opps, expected)

    def test_spot_direct_arbi_for_1x2(self):
        strat = TCDirectArbiStrategy()
        strat.spot_direct_arb_for_AH_and_OU = lambda *args: []
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', '1x2'): {None: {'b1': ([3.15, 3.4, 3.6], 'a!A1', 123.45),
                                    'b2': ([3.25, 3.4, 3.5], 'b!A2', 678.90),
                                    '99': ([3.2, 3.4, 3.55], 'b!A2', 678.90),
                                    'b3': ([3.0, 3.3, 3.3], 'c!A3', 246.84),
                                    'b3 lay': ([3.1, 3.4, 3.4], 'c!A4', 246.80),
                                   }
                            }
        }

        mock_bookie_id_map = {'b1': 'b1', 'b2': 'b2', 'b3': 'b3', 'b3 lay': 'b3', '99': '99'}
        patch1 = mock.patch('arbi.constants.BOOKIE_IDS_WITH_LAY_PRICES', ['b3'])
        patch2 = mock.patch('arbi.constants.BOOKIE_ID_MAP', mock_bookie_id_map)
        with patch1, patch2:
            opps = strat.spot_arbi(match)

        expected = [(0.01018, (('1x2', 'Home', 'FT', '99', 31.6, 3.2, '', False),
                               ('1x2', 'Home', 'FT', 'b3', 68.4, 3.1, '', True))),
                    (0.01258, (('1x2', 'Away', 'FT', '99', 28.5, 3.55, '', False),
                               ('1x2', 'Away', 'FT', 'b3', 71.5, 3.4, '', True)))
                    ]
        self.assertEqual(opps, expected)


class TCDirectArbiStrategyMethodsTest(TestCase):

    def test_get_prices_by_position(self):
        bookie_odds_id_and_info = {
            '99': ([2.03, 1.92], 'a!1', 0),
            'b1': ([2.05, 1.90], 'a!1', 0),
            'b2': ([2.00, 1.95], 'b!2', 0),
            'b7': ([1.95, 2.00], 'c!3', 0),
            'b7 lay': ([1.97, 2.02], 'c!4', 0),
        }
        with mock.patch('arbi.constants.BOOKIE_IDS_WITH_LAY_PRICES', ['b7']):
            home_prices, away_prices, home_sporttery_price, away_sporttery_price = TCDirectArbiStrategy.get_prices_by_position(bookie_odds_id_and_info)

        expected_home_prices = [('b1', 2.05, 'a!1'), ('b2', 2.0, 'b!2'), ('b7 lay', 1.9803921568627452, 'c!4')]
        expected_away_prices = [('b7 lay', 2.0309278350515463, 'c!4'), ('b2', 1.95, 'b!2'), ('b1', 1.9, 'a!1')]
        self.assertEqual(home_prices, expected_home_prices)
        self.assertEqual(away_prices, expected_away_prices)
        self.assertEqual(home_sporttery_price, 2.03)
        self.assertEqual(away_sporttery_price, 1.92)

    def test_get_prices_by_position_no_sporttery(self):
        bookie_odds_id_and_info = {
            'b1': ([2.05, 1.90], 'a!1', 0),
            'b2': ([2.00, 1.95], 'b!2', 0),
            'b7': ([1.95, 2.00], 'c!3', 0),
            'b7 lay': ([1.97, 2.02], 'c!4', 0),
        }
        with mock.patch('arbi.constants.BOOKIE_IDS_WITH_LAY_PRICES', ['b7']):
            home_prices, away_prices, home_sporttery_price, away_sporttery_price = TCDirectArbiStrategy.get_prices_by_position(bookie_odds_id_and_info)

        expected_home_prices = [('b1', 2.05, 'a!1'), ('b2', 2.0, 'b!2'), ('b7 lay', 1.9803921568627452, 'c!4')]
        expected_away_prices = [('b7 lay', 2.0309278350515463, 'c!4'), ('b2', 1.95, 'b!2'), ('b1', 1.9, 'a!1')]
        self.assertEqual(home_prices, expected_home_prices)
        self.assertEqual(away_prices, expected_away_prices)
        self.assertEqual(home_sporttery_price, None)
        self.assertEqual(away_sporttery_price, None)
