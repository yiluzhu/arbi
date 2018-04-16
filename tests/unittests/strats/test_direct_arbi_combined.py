import mock
from unittest2 import TestCase

from arbi.strats.direct_arbi_combined import DirectArbiCombinedStrategy

profit_threshold = 0.008
mock_bookie_id_map = {'b1': 'b1', 'b2': 'b2', 'b3': 'b3'}


@mock.patch('arbi.constants.BOOKIE_ID_MAP', return_value=mock_bookie_id_map)
class DirectArbiCombinedStrategyTest(TestCase):
    def setUp(self):
        self.match = mock.MagicMock()
        self.match.is_in_running = False
        self.bookie_availability_dict = {bookie: {flag: True for flag in ['dead ball', 'running ball']}
                                         for bookie in ['b1', 'b2', 'b3', 'b3 lay']}
        self.match.odds.odds_dict = {
            ('FT', 'AH'): {
                -1: {'b1': ([1.65, 2.45], 'b1!Aa1', 123.45),
                     'b2': ([1.66, 2.35], 'b2!Aa1', 456.78),
                     'b3': ([1.67, 2.3], 'b3!Aa1', 789.65),
                     },
                -0.75: {'b1': ([1.35, 2.70], 'b1!Aa2', 123.45),
                        'b2': ([1.50, 2.65], 'b2!Aa2', 456.78),
                        'b3': ([1.45, 2.50], 'b3!Aa2', 789.65),
                        },
                -1.25: {'b1': ([1.95, 2.03], 'b1!Aa3', 123.45),
                        'b2': ([1.99, 1.92], 'b2!Aa3', 456.78),
                        'b3': ([2.00, 1.97], 'b3!Aa3', 789.65),
                        },
            },
            ('FT', 'OU'): {
                2: {'b1': ([1.65, 2.45], 'b1!Ao1', 123.45),
                    'b2': ([1.66, 2.35], 'b2!Ao1', 456.78),
                    'b3': ([1.67, 2.3], 'b3!Ao1', 789.65),
                    },
                1.75: {'b1': ([1.35, 2.70], 'b1!Ao2', 123.45),
                       'b2': ([1.50, 2.65], 'b2!Ao2', 456.78),
                       'b3': ([1.45, 2.50], 'b3!Ao2', 789.65),
                       },
                2.25: {'b1': ([1.95, 2.03], 'b1!Ao3', 123.45),
                       'b2': ([1.99, 1.92], 'b2!Ao3', 456.78),
                       'b3': ([2.00, 1.97], 'b3!Ao3', 789.65),
                       },
            },
        }

    def test_normal(self, _):
        strat = DirectArbiCombinedStrategy(profit_threshold)
        arbi_opps = strat.spot_arbi(self.match, self.bookie_availability_dict)
        expected_arbi_opps = [(0.00858, (('AH Home', -0.75, 'FT', 'b2', 33.6, 1.5, 'b2!Aa2', False),
                                         ('AH Home', -1.25, 'FT', 'b3', 25.2, 2.0, 'b3!Aa3', False),
                                         ('AH Away', 1, 'FT', 'b1', 41.2, 2.45, 'b1!Aa1', False))),
                              (0.00858, (('OU Over', 2.25, 'FT', 'b3', 25.2, 2.0, 'b3!Ao3', False),
                                         ('OU Over', 1.75, 'FT', 'b2', 33.6, 1.5, 'b2!Ao2', False),
                                         ('OU Under', 2, 'FT', 'b1', 41.2, 2.45, 'b1!Ao1', False)))
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_ignore_lay_prices(self, _):
        self.match.odds.odds_dict[('FT', 'AH')][-1]['b3 lay'] = ([1.68, 2.31], 'b3!Aa1', 789.65)
        self.match.odds.odds_dict[('FT', 'AH')][-0.75]['b3 lay'] = ([1.46, 2.51], 'b3lay!Aa2', 789.65)
        self.match.odds.odds_dict[('FT', 'AH')][-1.25]['b3 lay'] = ([2.01, 1.98], 'b3lay!Aa3', 789.65)
        for x in [-1, -0.75, -1.25]:
            self.match.odds.odds_dict[('FT', 'AH')][x].pop('b3')

        strat = DirectArbiCombinedStrategy(profit_threshold)
        arbi_opps = strat.spot_arbi(self.match, self.bookie_availability_dict)
        expected_arbi_opps = [
                              (0.00858, (('OU Over', 2.25, 'FT', 'b3', 25.2, 2.0, 'b3!Ao3', False),
                                         ('OU Over', 1.75, 'FT', 'b2', 33.6, 1.5, 'b2!Ao2', False),
                                         ('OU Under', 2, 'FT', 'b1', 41.2, 2.45, 'b1!Ao1', False)))
                              ]

        self.assertEqual(arbi_opps, expected_arbi_opps)

    def test_unavailable_bookies(self, _):
        strat = DirectArbiCombinedStrategy(profit_threshold)
        self.bookie_availability_dict['b3']['dead ball'] = False
        arbi_opps = strat.spot_arbi(self.match, self.bookie_availability_dict)

        self.assertEqual(arbi_opps, [])

    # def test_4selections(self, _):
    #     self.match.odds.odds_dict = {
    #         ('FT', 'AH'): {
    #             -1: {'b1': ([1.65, 2.29], 'b1!Aa1', 123.45),
    #                  'b2': ([1.67, 2.27], 'b2!Aa1', 456.78),
    #                  'b3': ([1.69, 2.25], 'b3!Aa1', 789.65),
    #                  },
    #             -0.75: {'b1': ([1.40, 2.54], 'b1!Aa2', 123.45),
    #                     'b2': ([1.42, 2.52], 'b2!Aa2', 456.78),
    #                     'b3': ([1.44, 2.50], 'b3!Aa2', 789.65),
    #                     },
    #             -1.25: {'b1': ([1.95, 1.99], 'b1!Aa3', 123.45),
    #                     'b2': ([1.99, 1.95], 'b2!Aa3', 456.78),
    #                     'b3': ([2.00, 1.94], 'b3!Aa3', 789.65),
    #                     },
    #         },
    #     }
    #     strat = DirectArbiCombinedStrategy(profit_threshold)
    #     arbi_opps = strat.spot_arbi(self.match, self.bookie_availability_dict)
    #     expected_arbi_opps = [(0.00858, (('AH Home', -0.75, 'FT', 'b2', 33.599999999999994, 1.5, 'b!A2', False),
    #                                      ('AH Home', -1.25, 'FT', 'b3', 25.199999999999996, 2.0, 'c!A3', False),
    #                                      ('AH Away', -1.25, 'FT', 'b1', 41.2, 2.45, 'a!A1', False),
    #                                      ('AH Away', -1.25, 'FT', 'b1', 41.2, 2.45, 'a!A1', False))
    #                            )]
    #
    #     self.assertEqual(arbi_opps, expected_arbi_opps)


class DirectArbiCombinedStrategyMethodTest(TestCase):
    def setUp(self):
        self.strat = DirectArbiCombinedStrategy()
        self.match = mock.MagicMock()
        self.match.is_in_running = False
        self.match.odds.odds_dict = {
            ('FT', 'AH'): {
                -1: {'b1': ([1.65, 2.42], 'a!A1', 123.45),
                     'b2': ([1.66, 2.35], 'b!A2', 456.78),
                     'b3': ([1.67, 2.3], 'c!A3', 789.65),
                     },
                -0.75: {'b1': ([1.35, 2.70], 'a!A1', 123.45),
                        'b2': ([1.50, 2.65], 'b!A2', 456.78),
                        'b3': ([1.45, 2.50], 'c!A3', 789.65),
                        },
                -1.25: {'b1': ([1.95, 2.03], 'a!A1', 123.45),
                        'b2': ([1.99, 1.92], 'b!A2', 456.78),
                        'b3': ([2.00, 1.97], 'c!A3', 789.65),
                        },
            },
        }

        self.bookie_availability_dict = {bookie: {flag: True for flag in ['dead ball', 'running ball']}
                                         for bookie in ['b1', 'b2', 'b3', 'b3 lay']}

    def test_get_top_price(self):
        price_dict = self.match.odds.odds_dict[('FT', 'AH')]
        result = self.strat.get_top_price(price_dict[-1.25], self.bookie_availability_dict, 'running ball')
        expected = ('b3', 2.00, 'c!A3', 'b1', 2.03, 'a!A1')
        self.assertEqual(result, expected)

    def test_hcp_checker(self):
        price_dict = self.match.odds.odds_dict[('FT', 'AH')]
        result = self.strat.hcp_checker(-1, price_dict, self.bookie_availability_dict, 'running ball')
        expected = (-1,
                    ['b2', 0.5714285714285714, 'b!A2', 'b3', 0.42857142857142855, 'c!A3'],
                    [1.7142857142857142, 1.5, 2.0],
                    ['b1', 0.4291754756871035, 'a!A1', 'b1', 0.5708245243128964, 'a!A1'],
                    [2.317547568710359, 2.7, 2.03])
        self.assertEqual(result, expected)

    def test_hcp_filter(self):
        price_dict = self.match.odds.odds_dict
        result = self.strat.hcp_filter('FT', 'AH', price_dict, self.bookie_availability_dict, 'running ball')
        expected = [(-1,
                     ['b2', 0.5714285714285714, 'b!A2', 'b3', 0.42857142857142855, 'c!A3'],
                     [1.7142857142857142, 1.5, 2.0],
                     ['b1', 0.4291754756871035, 'a!A1', 'b1', 0.5708245243128964, 'a!A1'],
                     [2.317547568710359, 2.7, 2.03])]
        self.assertEqual(result, expected)

    def test_split_stakes(self):
        price_dict = self.match.odds.odds_dict
        p_arb = self.strat.hcp_filter('FT', 'AH', price_dict, self.bookie_availability_dict, 'running ball')
        result = self.strat.split_stakes('FT', 'AH', p_arb[0], 'H', [58.2, 41.2])
        expected = (('AH Home', -0.75, 'FT', 'b2', 33.26, 1.5, 'b!A2', False),
                    ('AH Home', -1.25, 'FT', 'b3', 24.94, 2.0, 'c!A3', False))
        self.assertEqual(result, expected)

    def test_split_stakes_4selections(self):
        price_dict = self.match.odds.odds_dict
        p_arb = self.strat.hcp_filter('FT', 'AH', price_dict, self.bookie_availability_dict, 'running ball')
        result = self.strat.split_stakes('FT', 'OU', p_arb[0], 'B', [58.2, 41.2])
        expected = (('OU Over', -0.75, 'FT', 'b2', 33.26, 1.5, 'b!A2', False),
                    ('OU Over', -1.25, 'FT', 'b3', 24.94, 2.0, 'c!A3', False),
                    ('OU Under', -0.75, 'FT', 'b1', 17.68, 2.7, 'a!A1', False),
                    ('OU Under', -1.25, 'FT', 'b1', 23.52, 2.03, 'a!A1', False))
        self.assertEqual(result, expected)
