import mock
from unittest2 import TestCase

from arbi.strats.correlated_arbi import AHvsXvs2Strategy, AHvs2Strategy

profit_threshold = 0.01
mock_bookie_id_map = {'b1': 'b1', 'b2': 'b2', 'b3': 'b3', 'b4': 'b4', 'b5': 'b5'}


@mock.patch('arbi.constants.BOOKIE_ID_MAP', return_value=mock_bookie_id_map)
class AHvsXvs2StrategyOppsTest(TestCase):

    def setUp(self):
        self.match1 = mock.MagicMock()
        self.match1.info = {'home_team_score': 0, 'away_team_score': 0}
        self.match1.odds.odds_dict = {
                                        ('FT', 'AH'): {
                                                            -0.5: {'b1': ([2.35, 1.60], 'a!A1', 123.45),
                                                                   'b2': ([2.35, 1.60], 'b!A2', 456.78),
                                                                   'b3': ([2.25, 1.70], 'c!A3', 789.65),
                                                                  },
                                                       },
                                        ('FT', '1x2'): {
                                                            None: {'b4': ([2.00, 3.50, 3.50], 'd!A4', 741.23),
                                                                   'b5': ([2.00, 3.40, 3.60], 'e!A5', 963.25),
                                                                   'b4 lay': ([2.10, 3.60, 3.60], 'f!A6', 741.23),
                                                                   },
                                                        },
                                    }

        self.match2 = mock.MagicMock()
        self.match2.info = {'home_team_score': 0, 'away_team_score': 0}
        self.match2.odds.odds_dict = {
                                        ('FT', 'AH'): {
                                                            0.5: {'b1': ([1.60, 2.35], 'a!A1', 123.45),
                                                                  'b2': ([1.60, 2.35], 'b!A2', 456.78),
                                                                  'b3': ([1.70, 2.25], 'c!A3', 789.65),
                                                                 },
                                                       },
                                        ('FT', '1x2'): {
                                                            None: {'b4': ([3.50, 3.50, 2.00], 'd!A4', 741.23),
                                                                   'b5': ([3.60, 3.40, 2.00], 'e!A5', 963.26),
                                                                   'b4 lay': ([3.60, 3.60, 2.10], 'f!A6', 741.23),
                                                                  },
                                                        },
                                     }
        self.reset_bookie_availability_dict()

    def reset_bookie_availability_dict(self):
        self.bookie_availability_dict = {bookie: {flag: True for flag in ['dead ball', 'running ball']}
                                         for bookie in ['b1', 'b2', 'b3', 'b4', 'b5', 'b4 lay']}

    def make_bookie_unavailable(self, bookie_id):
        self.bookie_availability_dict[bookie_id] = {flag: False for flag in ['dead ball', 'running ball']}

    def test_home_winning(self, _):
        # AH calculates from current scores, not 0:0
        # e.g. if the current scores are 0:0, betting on AH Home + 0.5 will win if final results are 0:0 or 1:0
        # but if the current scores are 1:0, betting on AH Home + 0.5 will lose if final results are 1:1
        # because from 1:0 away team scores.
        # So when scores are not even, we need to adjust AH handicap or we could lose for all selections in an arb.
        self.match2.info['home_team_score'] = 1
        self.match2.odds.odds_dict[('FT', 'AH')][1.5] = self.match2.odds.odds_dict[('FT', 'AH')][0.5]

        arb = AHvsXvs2Strategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)

        expected_arbi_opps = [(0.0111, (('AH Away', -1.5, 'FT', 'b1', 43.0, 2.35, 'a!A1', False),
                                         ('1x2', 'Draw', 'FT', 'b4', 28.9, 3.5, 'd!A4', False),
                                         ('1x2', 'Home', 'FT', 'b5', 28.1, 3.6, 'e!A5', False)))]
        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_away_winning(self, _):
        self.match1.info['away_team_score'] = 1
        self.match1.odds.odds_dict[('FT', 'AH')][-1.5] = self.match1.odds.odds_dict[('FT', 'AH')][-0.5]

        arb = AHvsXvs2Strategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)

        expected_arbi_opps = [(0.0111, (('AH Home', -1.5, 'FT', 'b1', 43.0, 2.35, 'a!A1', False),
                                         ('1x2', 'Draw', 'FT', 'b4', 28.9, 3.5, 'd!A4', False),
                                         ('1x2', 'Away', 'FT', 'b5', 28.1, 3.6, 'e!A5', False)))]
        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_lay_price_bug_no_opp(self, _):
        match = mock.MagicMock()
        match.info = {'home_team_score': 0, 'away_team_score': 0}
        match.odds.odds_dict = {
            ('FT', 'AH'): {-0.5: {'b1': ([2.23, 1.70], 'a!', 1.2)}},
            ('FT', '1x2'): {None: {'b4 lay': ([2.24, 3.40, 3.40], 'f!', 3.4)}},
        }
        arb = AHvsXvs2Strategy(profit_threshold)
        arbi_opps = arb.spot_arbi(match, self.bookie_availability_dict)
        self.assertEqual(arbi_opps, [])

    def test_lay_price_bug(self, _):
        match = mock.MagicMock()
        match.info = {'home_team_score': 0, 'away_team_score': 0}
        match.odds.odds_dict = {
            ('FT', 'AH'): {-0.5: {'b1': ([2.24, 1.70], 'a!', 1.2)}},
            ('FT', '1x2'): {None: {'b4 lay': ([2.23, 3.40, 3.40], 'f!', 3.4)}},
        }
        arb = AHvsXvs2Strategy(profit_threshold=0)
        arbi_opps = arb.spot_arbi(match, self.bookie_availability_dict)
        expected_arbi_opps = [(0.00201, (('AH Home', -0.5, 'FT', 'b1', 44.7, 2.24, 'a!', False),
                                         ('1x2', 'Home', 'FT', 'b4', 55.3, 2.23, 'f!', True)))]
        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_lay_only_opp(self, _):
        self.match1.odds.odds_dict[('FT', '1x2')][None]['b5'] = ([2.00, 3.45, 3.55], 'e!A5', 12.3)
        self.match2.odds.odds_dict[('FT', '1x2')][None]['b5'] = ([3.55, 3.45, 2.00], 'e!A5', 56.3)

        for score in [0, -1]:
            self.match1.info['home_team_score'] = self.match1.info['away_team_score'] = score
            arb = AHvsXvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            expected_arbi_opps = [(0.05336, (('AH Home', -0.5, 'FT', 'b1', 44.8, 2.35, 'a!A1', False),
                                             ('1x2', 'Home', 'FT', 'b4', 55.2, 2.1, 'f!A6', True)))
                                  ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.match2.info['home_team_score'] = self.match2.info['away_team_score'] = score
            arb = AHvsXvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            expected_arbi_opps = [(0.05336, (('AH Away', -0.5, 'FT', 'b1', 44.8, 2.35, 'a!A1', False),
                                            ('1x2', 'Away', 'FT', 'b4', 55.2, 2.1, 'f!A6', True)))
                                  ]

            self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_1opp(self, _):
        for score in [0, -1]:
            # match1
            self.reset_bookie_availability_dict()
            self.match1.info['home_team_score'] = self.match1.info['away_team_score'] = score
            arb = AHvsXvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            expected_arbi_opps = [(0.05336, (('AH Home', -0.5, 'FT', 'b1', 44.8, 2.35, 'a!A1', False),
                                             ('1x2', 'Home', 'FT', 'b4', 55.2, 2.1, 'f!A6', True))),
                                  ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b4 lay')
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            expected_arbi_opps = [(0.0111, (('AH Home', -0.5, 'FT', 'b1', 43.0, 2.35, 'a!A1', False),
                                             ('1x2', 'Draw', 'FT', 'b4', 28.9, 3.5, 'd!A4', False),
                                             ('1x2', 'Away', 'FT', 'b5', 28.1, 3.6, 'e!A5', False)))]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            # match2
            self.reset_bookie_availability_dict()
            self.match2.info['home_team_score'] = self.match2.info['away_team_score'] = score
            arb = AHvsXvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            expected_arbi_opps = [(0.05336, (('AH Away', -0.5, 'FT', 'b1', 44.8, 2.35, 'a!A1', False),
                                            ('1x2', 'Away', 'FT', 'b4', 55.2, 2.1, 'f!A6', True))),
                                  # (0.0111, (('AH Away', -0.5, 'FT', 'b2', 43.0, 2.35, 'b!A2', False),
                                  #            ('1x2', 'Draw', 'FT', 'b4', 28.9, 3.5, 'd!A4', False),
                                  #            ('1x2', 'Home', 'FT', 'b5', 28.1, 3.6, 'e!A5', False)))
                                  ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b4 lay')
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            expected_arbi_opps = [(0.0111, (('AH Away', -0.5, 'FT', 'b1', 43.0, 2.35, 'a!A1', False),
                                            ('1x2', 'Draw', 'FT', 'b4', 28.9, 3.5, 'd!A4', False),
                                            ('1x2', 'Home', 'FT', 'b5', 28.1, 3.6, 'e!A5', False)))]
            self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_2opps(self, _):
        self.match1.odds.odds_dict[('FT', '1x2')][None]['b5'] = ([2.00, 3.20, 3.80], 'e!A5', 12.3)
        self.match2.odds.odds_dict[('FT', '1x2')][None]['b5'] = ([3.80, 3.20, 2.00], 'e!A5', 45.6)

        for score in [0, -1]:
            # match1
            self.reset_bookie_availability_dict()
            self.match1.info['home_team_score'] = self.match1.info['away_team_score'] = score
            arb = AHvsXvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            expected_arbi_opps = [(0.05336, (('AH Home', -0.5, 'FT', 'b1', 44.8, 2.35, 'a!A1', False),
                                             ('1x2', 'Home', 'FT', 'b4', 55.2, 2.1, 'f!A6', True))),
                                 ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b4 lay')
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            expected_arbi_opps = [(0.02627, (('AH Home', -0.5, 'FT', 'b1', 43.7, 2.35, 'a!A1', False),
                                             ('1x2', 'Draw', 'FT', 'b4', 29.3, 3.5, 'd!A4', False),
                                             ('1x2', 'Away', 'FT', 'b5', 27.0, 3.8, 'e!A5', False)))
                                 ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b4')
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            self.assertEqual(arbi_opps, [])

            # match2
            self.reset_bookie_availability_dict()
            self.match2.info['home_team_score'] = self.match2.info['away_team_score'] = score
            arb = AHvsXvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            expected_arbi_opps = [(0.05336, (('AH Away', -0.5, 'FT', 'b1', 44.8, 2.35, 'a!A1', False),
                                            ('1x2', 'Away', 'FT', 'b4', 55.2, 2.1, 'f!A6', True))),
                                 ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b4 lay')
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            expected_arbi_opps = [(0.02627, (('AH Away', -0.5, 'FT', 'b1', 43.7, 2.35, 'a!A1', False),
                                             ('1x2', 'Draw', 'FT', 'b4', 29.3, 3.5, 'd!A4', False),
                                             ('1x2', 'Home', 'FT', 'b5', 27.0, 3.8, 'e!A5', False)))
                                 ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b4')
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            self.assertEqual(arbi_opps, [])


@mock.patch('arbi.constants.NON_TRADITIONAL_AH_BOOKIE_IDS', ['b3'])
@mock.patch('arbi.constants.BOOKIE_ID_MAP', return_value=mock_bookie_id_map)
class AHvsXvs2StrategyMethodTest(TestCase):

    def setUp(self):
        self.match = mock.MagicMock()
        self.match.info = {'home_team_score': 0, 'away_team_score': 0}
        self.match.odds.odds_dict = {
                                        ('FT', 'AH'): {
                                                            -0.5: {'b1': ([2.15, 1.80], 'a!A1', 123.45),
                                                                   'b2': ([2.20, 1.75], 'b!A2', 456.78),
                                                                   'b3': ([2.25, 1.70], 'c!A3', 789.65),
                                                                   'b3 lay': ([2.28, 1.73], 'c!A4', 789.65),
                                                                  },
                                                       },
                                        ('FT', '1x2'): {
                                                            None: {'b1': ([2.10, 3.40, 3.53], 'd!A4', 741.23),
                                                                   'b2': ([2.05, 3.45, 3.55], 'e!A5', 963.25),
                                                                   'b3': ([2.00, 3.50, 3.54], 'f!A6', 741.23),
                                                                   'b3 lay': ([2.03, 3.53, 3.57], 'f!A7', 741.23),
                                                                   },
                                                        },
                                }
        self.arbi_args = AHvsXvs2Strategy.arbi_args_for_both_map[False]
        self.bookie_availability_dict = {bookie: {flag: True for flag in ['dead ball', 'running ball']}
                                         for bookie in ['b1', 'b2', 'b3', 'b4', 'b5', 'b3 lay', 'b4 lay']}

    def test_get_prices_by_position(self, *_):
        strat = AHvsXvs2Strategy(profit_threshold)
        ah_prices, draw_prices, x_prices, x_lay_prices = strat.get_prices_by_position(self.match.odds.odds_dict,
                                        self.bookie_availability_dict, 'running ball', self.arbi_args, 'FT', -0.5)
        expected_ah_prices = [('b2', 2.20, 'b!A2'), ('b1', 2.15, 'a!A1')]
        expected_draw_prices = [('b3', 3.5, 'f!A6'), ('b2', 3.45, 'e!A5'), ('b1', 3.4, 'd!A4')]
        expected_x_prices = [('b2', 3.55, 'e!A5'), ('b3', 3.54, 'f!A6'), ('b1', 3.53, 'd!A4')]
        expected_x_lay_prices = [('b3 lay', 1.9708737864077672, 'f!A7')]
        self.assertEqual(ah_prices, expected_ah_prices)
        self.assertEqual(draw_prices, expected_draw_prices)
        self.assertEqual(x_prices, expected_x_prices)
        self.assertEqual(x_lay_prices, expected_x_lay_prices)

    def test_find_opps_for_ah_and_x_lay_prices(self, *_):
        strat = AHvsXvs2Strategy(profit_threshold)
        ah_prices, draw_prices, x_prices, x_lay_prices = strat.get_prices_by_position(self.match.odds.odds_dict,
                                        self.bookie_availability_dict, 'running ball', self.arbi_args, 'FT', -0.5)

        ah_new_prices, opps = strat.find_opps_for_ah_and_x_lay_prices(ah_prices, x_lay_prices,
                                                                      self.arbi_args, 'FT', -0.5)
        self.assertNotEqual(ah_prices, ah_new_prices)

        expected_ah_new_prices = [('b1', 2.15, 'a!A1')]
        self.assertEqual(ah_new_prices, expected_ah_new_prices)

        expected_opps = [
            (0.03957, (('AH Home', -0.5, 'FT', 'b2', 47.3, 2.2, 'b!A2', False),
                       ('1x2', 'Home', 'FT', 'b3', 52.7, 2.03, 'f!A7', True)))
        ]
        self.assertEqual(opps, expected_opps)


@mock.patch('arbi.constants.BOOKIE_ID_MAP', return_value=mock_bookie_id_map)
class AHvs2StrategyTest(TestCase):
    def setUp(self):
        self.match1 = mock.MagicMock()
        self.match1.info = {'home_team_score': 0, 'away_team_score': 0}
        self.match1.odds.odds_dict = {
                                        ('FT', 'AH'): {
                                                            0.5: {'b1': ([2.02, 1.93], 'a!A1', 123.45),
                                                                  'b2': ([2.00, 1.95], 'b!A2', 456.78),
                                                                  'b3': ([1.98, 1.97], 'c!A3', 789.65),
                                                                 },
                                                       },
                                        ('FT', '1x2'): {
                                                            None: {'b4': ([3.50, 3.50, 2.00], 'd!A4', 741.23),
                                                                   'b5': ([3.50, 3.48, 2.02], 'e!A5', 963.26),
                                                                   'b4 lay': ([3.55, 3.55, 2.05], 'f!A6', 741.23),
                                                                   },
                                                        },
                                     }

        self.match2 = mock.MagicMock()
        self.match2.info = {'home_team_score': 0, 'away_team_score': 0}
        self.match2.odds.odds_dict = {
                                        ('FT', 'AH'): {
                                                            -0.5: {'b1': ([1.93, 2.02], 'a!A1', 123.45),
                                                                   'b2': ([1.95, 2.00], 'b!A2', 456.78),
                                                                   'b3': ([1.97, 1.98], 'c!A3', 789.56),
                                                                  },
                                                       },
                                        ('FT', '1x2'): {
                                                            None: {'b4': ([2.00, 3.50, 3.50], 'd!A4', 741.25),
                                                                   'b5': ([2.02, 3.48, 3.50], 'e!A5', 963.25),
                                                                   'b4 lay': ([2.05, 3.55, 3.55], 'f!A6', 963.25),
                                                                   },
                                                        },
                                     }
        self.reset_bookie_availability_dict()

    def reset_bookie_availability_dict(self):
        self.bookie_availability_dict = {bookie: {flag: True for flag in ['dead ball', 'running ball']}
                                         for bookie in ['b1', 'b2', 'b3', 'b4', 'b5', 'b4 lay']}

    def make_bookie_unavailable(self, bookie_id):
        self.bookie_availability_dict[bookie_id] = {flag: False for flag in ['dead ball', 'running ball']}

    def test_home_winning(self, _):
        self.match1.info['home_team_score'] = 1
        self.match1.odds.odds_dict[('FT', 'AH')][1.5] = self.match1.odds.odds_dict[('FT', 'AH')][0.5]

        arb = AHvs2Strategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)

        expected_arbi_opps = [(0.01, (('AH Home', 1.5, 'FT', 'b1', 50.0, 2.02, 'a!A1', False),
                                      ('1x2', 'Away', 'FT', 'b5', 50.0, 2.02, 'e!A5', False)))]
        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_away_winning(self, _):
        self.match2.info['away_team_score'] = 1
        self.match2.odds.odds_dict[('FT', 'AH')][-1.5] = self.match2.odds.odds_dict[('FT', 'AH')][-0.5]

        arb = AHvs2Strategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)

        expected_arbi_opps = [(0.01, (('AH Away', 1.5, 'FT', 'b1', 50.0, 2.02, 'a!A1', False),
                                      ('1x2', 'Home', 'FT', 'b5', 50.0, 2.02, 'e!A5', False)))]
        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_0opp(self, _):
        self.match1.odds.odds_dict[('FT', '1x2')][None]['b5'] = ([3.50, 3.52, 1.98], 'e!A5', 12.3)
        self.match2.odds.odds_dict[('FT', '1x2')][None]['b5'] = ([1.98, 3.52, 3.50], 'e!A5', 45.6)

        for score in [0, -1]:
            for match in [self.match1, self.match2]:
                match.info['home_team_score'] = match.info['away_team_score'] = score
                arb = AHvs2Strategy(profit_threshold)
                arbi_opps = arb.spot_arbi(match, self.bookie_availability_dict)
                self.assertEqual(arbi_opps, [])

    def test_1opp(self, _):
        for score in [0, -1]:
            # match1
            self.reset_bookie_availability_dict()
            self.match1.info['home_team_score'] = self.match1.info['away_team_score'] = score
            arb = AHvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            expected_arbi_opps = [(0.01, (('AH Home', 0.5, 'FT', 'b1', 50.0, 2.02, 'a!A1', False),
                                          ('1x2', 'Away', 'FT', 'b5', 50.0, 2.02, 'e!A5', False)))]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b1')
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            self.assertEqual(arbi_opps, [])

            # match2
            self.reset_bookie_availability_dict()
            self.match2.info['home_team_score'] = self.match2.info['away_team_score'] = score
            arb = AHvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            expected_arbi_opps = [(0.01, (('AH Away', 0.5, 'FT', 'b1', 50.0, 2.02, 'a!A1', False),
                                          ('1x2', 'Home', 'FT', 'b5', 50.0, 2.02, 'e!A5', False)))]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b1')
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            self.assertEqual(arbi_opps, [])

    def test_2opps(self, _):
        self.match1.odds.odds_dict[('FT', '1x2')][None]['b5'] = ([3.50, 3.45, 2.05], 'e!A5', 32.6)
        self.match2.odds.odds_dict[('FT', '1x2')][None]['b5'] = ([2.05, 3.45, 3.50], 'e!A5', 98.4)

        for score in [0, -1]:
            # match1
            self.reset_bookie_availability_dict()
            self.match1.info['home_team_score'] = self.match1.info['away_team_score'] = score
            arb = AHvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            expected_arbi_opps = [(0.01744, (('AH Home', 0.5, 'FT', 'b1', 50.4, 2.02, 'a!A1', False),
                                             ('1x2', 'Away', 'FT', 'b5', 49.6, 2.05, 'e!A5', False))),
                                 ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b1')
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            expected_arbi_opps = [(0.01235,  (('AH Home', 0.5, 'FT', 'b2', 50.6, 2.00, 'b!A2', False),
                                              ('1x2', 'Away', 'FT', 'b5', 49.4, 2.05, 'e!A5', False))),
                                 ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.reset_bookie_availability_dict()
            self.make_bookie_unavailable('b5')
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            self.assertEqual(arbi_opps, [])

            # match2
            self.reset_bookie_availability_dict()
            self.match2.info['home_team_score'] = self.match2.info['away_team_score'] = score
            arb = AHvs2Strategy(profit_threshold)
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            expected_arbi_opps = [(0.01744, (('AH Away', 0.5, 'FT', 'b1', 50.4, 2.02, 'a!A1', False),
                                             ('1x2', 'Home', 'FT', 'b5', 49.6, 2.05, 'e!A5', False))),
                                 ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.make_bookie_unavailable('b1')
            arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
            expected_arbi_opps = [(0.01235,  (('AH Away', 0.5, 'FT', 'b2', 50.6, 2.00, 'b!A2', False),
                                              ('1x2', 'Home', 'FT', 'b5', 49.4, 2.05, 'e!A5', False))),
                                 ]
            self.assertEqual(arbi_opps, expected_arbi_opps)

            self.reset_bookie_availability_dict()
            self.make_bookie_unavailable('b5')
            arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
            expected_arbi_opps = []
            self.assertEqual(arbi_opps, expected_arbi_opps)
