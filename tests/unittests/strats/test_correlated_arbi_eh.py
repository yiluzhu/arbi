import mock
from unittest2 import TestCase

from arbi.strats.correlated_arbi_eh import EHvsEHXvsAHStrategy

profit_threshold = 0.01
mock_bookie_id_map = {'b1': 'b1', 'b2': 'b2', 'b3': 'b3', 'b4': 'b4', 'b5': 'b5'}


@mock.patch('arbi.constants.BOOKIE_ID_MAP', return_value=mock_bookie_id_map)
class AHvsXvs2StrategyTest(TestCase):
    def setUp(self):
        self.match1 = mock.MagicMock()
        self.match1.info = {'home_team_score': 0, 'away_team_score': 0}
        self.match1.odds.odds_dict = {
                                        ('FT', 'AH'): {
                                                            -0.5: {'b1': ([1.65, 2.30], 'a!A1', 123.45),
                                                                   'b2': ([1.70, 2.25], 'b!A2', 456.78),
                                                                   'b3': ([1.75, 2.20], 'c!A3', 789.65),
                                                                   },
                                                       },
                                        ('FT', 'EH'): {
                                                            -1: {'b4': ([4.00, 3.50, 2.00], 'd!A4', 741.23),
                                                                 'b4 lay': ([4.10, 3.60, 2.10], 'e!A5', 741.23),
                                                                 },
                                                       },
                                    }

        self.match2 = mock.MagicMock()
        self.match2.info = {'home_team_score': 0, 'away_team_score': 0}
        self.match2.odds.odds_dict = {
                                        ('FT', 'AH'): {
                                                            0.5: {'b1': ([2.30, 1.65], 'a!A1', 123.45),
                                                                  'b2': ([2.25, 1.70], 'b!A2', 456.78),
                                                                  'b3': ([2.20, 1.75], 'c!A3', 789.65),
                                                                  },
                                                       },
                                        ('FT', 'EH'): {
                                                            1: {'b4': ([2.00, 3.50, 4.00], 'd!A4', 741.23),
                                                                'b4 lay': ([2.10, 3.60, 4.10], 'e!A5', 741.23),
                                                                },
                                                        },
                                     }
        self.reset_bookie_availability_dict()

    def make_bookie_unavailable(self, bookie_id):
        self.bookie_availability_dict[bookie_id] = {flag: False for flag in ['dead ball', 'running ball']}

    def reset_bookie_availability_dict(self):
        self.bookie_availability_dict = {bookie: {flag: True for flag in ['dead ball', 'running ball']}
                                         for bookie in ['b1', 'b2', 'b3', 'b4', 'b5', 'b4 lay']}

    def test_normal_1goal_3_selection_opps(self, _):
        """3 selection opportunities are generated only when corresponding 2 selection opportunities are not generated.
        """
        self.match1.odds.odds_dict[('FT', 'EH')][-1].pop('b4 lay')
        arb = EHvsEHXvsAHStrategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0304, (('EH Home', -1, 'FT', 'b4', 25.8, 4.0, 'd!A4', False),
                                        ('EH Draw', -1, 'FT', 'b4', 29.4, 3.5, 'd!A4', False),
                                        ('AH Away', 0.5, 'FT', 'b1', 44.8, 2.3, 'a!A1', False))),
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_3_selection_opps_due_to_bookie_unavailable(self, _):
        """Corresponding 2 selection opportunities are not generated due to bookie unavailable,
        3 selection opportunities should be generated in this case.
        """
        arb = EHvsEHXvsAHStrategy(profit_threshold)

        self.make_bookie_unavailable('b4 lay')
        arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0304, (('EH Home', -1, 'FT', 'b4', 25.8, 4.0, 'd!A4', False),
                                        ('EH Draw', -1, 'FT', 'b4', 29.4, 3.5, 'd!A4', False),
                                        ('AH Away', 0.5, 'FT', 'b1', 44.8, 2.3, 'a!A1', False))),
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_lay_price_bug_no_opp(self, _):
        match = mock.MagicMock()
        match.info = {'home_team_score': 0, 'away_team_score': 0}
        match.odds.odds_dict = {
            ('FT', 'AH'): {-0.5: {'b1': ([1.70, 2.23], 'a!', 12.4)}},
            ('FT', 'EH'): {-1: {'b4 lay': ([3.50, 3.60, 2.24], 'e!', 14.2)}},
        }

        arb = EHvsEHXvsAHStrategy(profit_threshold)
        arbi_opps = arb.spot_arbi(match, self.bookie_availability_dict)

        self.assertEqual(arbi_opps, [])

    def test_lay_price_bug(self, _):
        match = mock.MagicMock()
        match.info = {'home_team_score': 0, 'away_team_score': 0}
        match.odds.odds_dict = {
            ('FT', 'AH'): {-0.5: {'b1': ([1.70, 2.24], 'a!', 12.4)}},
            ('FT', 'EH'): {-1: {'b4 lay': ([3.40, 3.40, 2.23], 'e!', 14.2)}},
        }

        arb = EHvsEHXvsAHStrategy(profit_threshold=0)
        arbi_opps = arb.spot_arbi(match, self.bookie_availability_dict)
        expected_arbi_opps = [(0.00201, (('EH Away', 1, 'FT', 'b4', 55.3, 2.23, 'e!', True),
                                         ('AH Away', 0.5, 'FT', 'b1', 44.7, 2.24, 'a!', False))),
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_normal_1goal(self, _):
        arb = EHvsEHXvsAHStrategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0432, (('EH Away', 1, 'FT', 'b4', 54.6, 2.1, 'e!A5', True),
                                        ('AH Away', 0.5, 'FT', 'b1', 45.4, 2.3, 'a!A1', False))),
                              # (0.02024, (('EH Home', -1, 'FT', 'b4', 25.5, 4.0, 'd!A4', False),
                              #            ('EH Draw', -1, 'FT', 'b4', 29.1, 3.5, 'd!A4', False),
                              #            ('AH Away', 0.5, 'FT', 'b2', 45.3, 2.25, 'b!A2', False))),
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_normal_2goals(self, _):
        self.match1.odds.odds_dict[('FT', 'AH')][-1.5] = self.match1.odds.odds_dict[('FT', 'AH')].pop(-0.5)
        self.match1.odds.odds_dict[('FT', 'EH')][-2] = self.match1.odds.odds_dict[('FT', 'EH')].pop(-1)

        arb = EHvsEHXvsAHStrategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0432, (('EH Away', 2, 'FT', 'b4', 54.6, 2.1, 'e!A5', True),
                                        ('AH Away', 1.5, 'FT', 'b1', 45.4, 2.3, 'a!A1', False)))
                              # (0.02024, (('EH Home', -2, 'FT', 'b4', 25.5, 4.0, 'd!A4', False),
                              #            ('EH Draw', -2, 'FT', 'b4', 29.1, 3.5, 'd!A4', False),
                              #            ('AH Away', 1.5, 'FT', 'b2', 45.3, 2.25, 'b!A2', False))),
                              ]
        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_normal_3goals(self, _):
        self.match1.odds.odds_dict[('FT', 'AH')][-2.5] = self.match1.odds.odds_dict[('FT', 'AH')].pop(-0.5)
        self.match1.odds.odds_dict[('FT', 'EH')][-3] = self.match1.odds.odds_dict[('FT', 'EH')].pop(-1)

        arb = EHvsEHXvsAHStrategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match1, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0432, (('EH Away', 3, 'FT', 'b4', 54.6, 2.1, 'e!A5', True),
                                        ('AH Away', 2.5, 'FT', 'b1', 45.4, 2.3, 'a!A1', False)))
                              # (0.02024, (('EH Home', -3, 'FT', 'b4', 25.5, 4.0, 'd!A4', False),
                              #            ('EH Draw', -3, 'FT', 'b4', 29.1, 3.5, 'd!A4', False),
                              #            ('AH Away', 2.5, 'FT', 'b2', 45.3, 2.25, 'b!A2', False))),
                              ]
        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_reversed_1goal_3_selection_opps(self, _):
        self.match2.odds.odds_dict[('FT', 'EH')][1].pop('b4 lay')
        arb = EHvsEHXvsAHStrategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0304, (('AH Home', 0.5, 'FT', 'b1', 44.8, 2.3, 'a!A1', False),
                                        ('EH Draw', 1, 'FT', 'b4', 29.4, 3.5, 'd!A4', False),
                                        ('EH Away', -1, 'FT', 'b4', 25.8, 4.0, 'd!A4', False)))
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_reversed_1goal_3_selection_opps_due_to_bookie_unavailable(self, _):
        arb = EHvsEHXvsAHStrategy(profit_threshold)
        self.make_bookie_unavailable('b4 lay')
        arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0304, (('AH Home', 0.5, 'FT', 'b1', 44.8, 2.3, 'a!A1', False),
                                        ('EH Draw', 1, 'FT', 'b4', 29.4, 3.5, 'd!A4', False),
                                        ('EH Away', -1, 'FT', 'b4', 25.8, 4.0, 'd!A4', False)))
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_reversed_1goal(self, _):
        arb = EHvsEHXvsAHStrategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0432, (('AH Home', 0.5, 'FT', 'b1', 45.4, 2.3, 'a!A1', False),
                                        ('EH Home', 1, 'FT', 'b4', 54.6, 2.1, 'e!A5', True)))
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_reversed_2goal(self, _):
        self.match2.odds.odds_dict[('FT', 'AH')][1.5] = self.match2.odds.odds_dict[('FT', 'AH')].pop(0.5)
        self.match2.odds.odds_dict[('FT', 'EH')][2] = self.match2.odds.odds_dict[('FT', 'EH')].pop(1)

        arb = EHvsEHXvsAHStrategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0432, (('AH Home', 1.5, 'FT', 'b1', 45.4, 2.3, 'a!A1', False),
                                        ('EH Home', 2, 'FT', 'b4', 54.6, 2.1, 'e!A5', True)))
                              # (0.02024, (('AH Home', 1.5, 'FT', 'b2', 45.3, 2.25, 'b!A2', False),
                              #            ('EH Draw', 2, 'FT', 'b4', 29.1, 3.5, 'd!A4', False),
                              #            ('EH Away', -2, 'FT', 'b4', 25.5, 4.0, 'd!A4', False))),
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_reversed_3goal(self, _):
        self.match2.odds.odds_dict[('FT', 'AH')][2.5] = self.match2.odds.odds_dict[('FT', 'AH')].pop(0.5)
        self.match2.odds.odds_dict[('FT', 'EH')][3] = self.match2.odds.odds_dict[('FT', 'EH')].pop(1)

        arb = EHvsEHXvsAHStrategy(profit_threshold)
        arbi_opps = arb.spot_arbi(self.match2, self.bookie_availability_dict)
        expected_arbi_opps = [(0.0432, (('AH Home', 2.5, 'FT', 'b1', 45.4, 2.3, 'a!A1', False),
                                        ('EH Home', 3, 'FT', 'b4', 54.6, 2.1, 'e!A5', True)))
                              # (0.02024, (('AH Home', 2.5, 'FT', 'b2', 45.3, 2.25, 'b!A2', False),
                              #            ('EH Draw', 3, 'FT', 'b4', 29.1, 3.5, 'd!A4', False),
                              #            ('EH Away', -3, 'FT', 'b4', 25.5, 4.0, 'd!A4', False))),
                              ]
        self.assertEqual(arbi_opps, expected_arbi_opps)
