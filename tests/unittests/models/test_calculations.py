from unittest2 import TestCase
from arbi.models.calculations import calculate_stakes, calculate_stakes_new, convert_back_lay_prices, \
    get_better_price_from_back_lay_prices


profit_threshold = 0.01


class StakeCalculationTest(TestCase):
    def test_calculate_stakes_no_arbi(self):
        # by default the minimum profit for arbitrage is 1%
        odds1 = 2.02
        odds2 = 2.01
        expected = None

        result = calculate_stakes(odds1, odds2, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)

    def test_calculate_stakes_no_commission(self):
        # for 1% profit, both sides need 2 points higher than 2.0
        odds1 = 2.02
        odds2 = 2.02
        expected = (50.0, 50.0, 0.01)

        result = calculate_stakes(odds1, odds2, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)

    def test_calculate_stakes_one_commission(self):
        # test the relation between commission, stake distribution and profit
        odds1 = 2.02
        odds2 = 2.01

        # case 1
        # vs previous test, 0.5% commission equals to 1% odds
        commission2 = 0.005
        expected = (49.9, 50.1, 0.01)
        result = calculate_stakes(odds1, odds2, commission2=commission2, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)

        # case 2
        # 1 vs 2: change of commission changes profit, but don't change stake distribution
        commission2 = 0.015
        expected = (49.9, 50.1, 0.01501)
        result = calculate_stakes(odds1, odds2, commission2=commission2, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)

        # case 3
        # 1 vs 3: same commission if applied to different side, could produce different profit
        commission1 = 0.005
        expected = (49.9, 50.1, 0.00999)
        result = calculate_stakes(odds1, odds2, commission1=commission1, profit_threshold=0)
        self.assertEqual(result, expected)

        # case 4
        # 2 vs 4: same commission if applied to different side, don't change stake distribution
        commission1 = 0.015
        expected = (49.9, 50.1, 0.01498)
        result = calculate_stakes(odds1, odds2, commission1=commission1, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)

    def test_calculate_stakes_two_commission(self):
        odds1 = 2.02
        odds2 = 2.01

        # case 1
        commission1 = 0.0075
        commission2 = 0.0075
        expected = (49.9, 50.1, 0.01499)
        result = calculate_stakes(odds1, odds2, commission1=commission1, commission2=commission2, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)

        # case 2
        commission1 = 0.0075
        commission2 = 0.0025
        expected = (49.9, 50.1, 0.01249)
        result = calculate_stakes(odds1, odds2, commission1=commission1, commission2=commission2, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)

        # case 3
        commission1 = 0.0025
        commission2 = 0.0075
        expected = (49.9, 50.1, 0.0125)
        result = calculate_stakes(odds1, odds2, commission1=commission1, commission2=commission2, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)

    def test_calculate_stakes_negative_commission(self):
        # betfair charges for winning, e.g. 2%

        odds1 = 2.06
        odds2 = 2.03

        # case 1
        commission1 = -0.02
        expected = (49.6, 50.4, 0.01252)
        result = calculate_stakes(odds1, odds2, commission1=commission1, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)

        # case 2
        commission2 = -0.02
        expected = (49.6, 50.4, 0.01237)
        result = calculate_stakes(odds1, odds2, commission2=commission2, profit_threshold=profit_threshold)
        self.assertEqual(result, expected)


class NewStakeCalculationTest(TestCase):

    def test_calculate_stakes_new_no_arb(self):
        price1 = price2 = price3 = 3.0

        result = calculate_stakes_new(price1, price2, price3, profit_threshold=0)
        self.assertIsNone(result)

    def test_calculate_stakes_new_arb_no_commission(self):
        price1 = price2 = price3 = 3.1

        result = calculate_stakes_new(price1, price2, price3)
        expected = 33.3, 33.3, 33.3, 0.03333  # round((3.1 - 3) / 3, 5)
        self.assertEqual(result, expected)

    def test_calculate_stakes_new_no_arb_for_high_prifit(self):
        price1 = price2 = price3 = 3.1

        result = calculate_stakes_new(price1, price2, price3, profit_threshold=0.04)
        self.assertIsNone(result)

    def test_calculate_stakes_new_arb_commission(self):
        price1 = price2 = price3 = 3.1
        commission1 = commission2 = commission3 = 0.001

        result = calculate_stakes_new(price1, price2, price3, commission1, commission2, commission3)
        expected = 33.3, 33.3, 33.3, 0.03437  # round((3.1 - 3 + 0.001 * 3) / 3, 5)  this is accurate profit, in the function we use approximate
        self.assertEqual(result, expected)


class FunctionsTest(TestCase):
    def test_convert_back_lay_prices(self):
        lay_price = 2.30
        results = convert_back_lay_prices(lay_price)
        expected = 1.77
        self.assertEqual(results, expected)


class GetBetterPriceFromBackLayPricesTest(TestCase):
    def test_return_both_lay_prices(self):
        back_lay_prices_dict = {
            'b7': {
                'b7': ([1.95, 2.0], 'a!1'),
                'b7 lay': ([1.96, 2.01], 'b!2'),
            }
        }
        result = get_better_price_from_back_lay_prices(back_lay_prices_dict)
        expected = {
            'b7': [('b7 lay', 1.96, 'b!2'), ('b7 lay', 2.01, 'b!2')]
        }
        self.assertEqual(result, expected)

    def test_return_both_back_prices(self):
        back_lay_prices_dict = {
            'b7': {
                'b7': ([1.95, 2.0], 'a!1'),
                'b7 lay': ([1.94, 1.99], 'b!2'),
            }
        }
        result = get_better_price_from_back_lay_prices(back_lay_prices_dict)
        expected = {
            'b7': [('b7', 1.95, 'a!1'), ('b7', 2.0, 'a!1')]
        }
        self.assertEqual(result, expected)

    def test_return_home_back_away_lay_prices(self):
        back_lay_prices_dict = {
            'b7': {
                'b7': ([1.95, 2.0], 'a!1'),
                'b7 lay': ([1.94, 2.01], 'b!2'),
            }
        }
        result = get_better_price_from_back_lay_prices(back_lay_prices_dict)
        expected = {
            'b7': [('b7', 1.95, 'a!1'), ('b7 lay', 2.01, 'b!2')]
        }
        self.assertEqual(result, expected)

    def test_return_home_lay_away_back_prices(self):
        back_lay_prices_dict = {
            'b7': {
                'b7': ([1.95, 2.0], 'a!1'),
                'b7 lay': ([1.96, 1.99], 'b!2'),
            }
        }
        result = get_better_price_from_back_lay_prices(back_lay_prices_dict)
        expected = {
            'b7': [('b7 lay', 1.96, 'b!2'), ('b7', 2.0, 'a!1')]
        }
        self.assertEqual(result, expected)

    def test_there_are_two_lay_bookies(self):
        back_lay_prices_dict = {
            'b7': {
                'b7': ([1.95, 2.0], 'a!1'),
                'b7 lay': ([1.94, 2.01], 'b!2'),
            },
            'b8': {
                'b8': ([1.97, 1.97], 'c!1'),
                'b8 lay': ([1.98, 1.96], 'd!2'),
            }
        }
        result = get_better_price_from_back_lay_prices(back_lay_prices_dict)
        expected = {
            'b7': [('b7', 1.95, 'a!1'), ('b7 lay', 2.01, 'b!2')],
            'b8': [('b8 lay', 1.98, 'd!2'), ('b8', 1.97, 'c!1')],
        }
        self.assertEqual(result, expected)

    def test_only_back_prices_available(self):
        back_lay_prices_dict = {
            'b7': {
                'b7': ([1.95, 2.0], 'a!1'),
            }
        }
        result = get_better_price_from_back_lay_prices(back_lay_prices_dict)
        expected = {
            'b7': [('b7', 1.95, 'a!1'), ('b7', 2.0, 'a!1')]
        }
        self.assertEqual(result, expected)

    def test_only_lay_prices_available(self):
        back_lay_prices_dict = {
            'b7': {
                'b7 lay': ([1.95, 2.0], 'b!2'),
            }
        }
        result = get_better_price_from_back_lay_prices(back_lay_prices_dict)
        expected = {
            'b7': [('b7 lay', 1.95, 'b!2'), ('b7 lay', 2.0, 'b!2')]
        }
        self.assertEqual(result, expected)
