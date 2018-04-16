import time
import datetime
from multiprocessing.pool import AsyncResult

import mock
from unittest2 import TestCase

from arbi.models.arbi_spotter import ArbiSpotter
from arbi.strats.direct_arbi import DirectArbiStrategy
from arbi.strats.correlated_arbi import AHvsXvs2Strategy
from arbi.strats.correlated_arbi_eh import EHvsEHXvsAHStrategy
from arbi.strats.cross_handicap_arbi import CrossHandicapArbiStrategy
from arbi.ui_models.menu_bar_model import StratsPanelModel

profit_threshold = 0.01


class ArbiSpotterTest(TestCase):
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

    def test_spot_arbi_betfair_AH(self):
        match = mock.MagicMock(id='001')
        match.info = self.match_info
        match.odds.odds_dict = {
            # be aware that bookie_id 1, 2, 5 all have commissions
            ('FT', 'AH'):
                {0.5: {'7 lay': ([2.00, 2.08], '7457059973!A247', time.time()),
                       '2': ([2.06, 1.86], '7457059973!A247', time.time()),
                       '5': ([2.02, 1.90], '146ba9!B4231374', time.time()),
                       '7': ([1.92, 2.02], '146ba9!B4231374', time.time())}}
        }
        match_dict = {
            '001': match
        }

        spotter = ArbiSpotter(match_dict, profit_threshold=profit_threshold)
        spotter.initialize_strats()
        arbi_opps = spotter.spot_arbi()

        selection1 = arbi_opps[0].selections[0]
        self.assertEqual(selection1.odds_type, 'AH Home')
        self.assertEqual(selection1.bookie_id, '2')
        self.assertEqual(selection1.lay_flag, False)
        selection2 = arbi_opps[0].selections[1]
        self.assertEqual(selection2.odds_type, 'AH Away')
        self.assertEqual(selection2.bookie_id, '7')
        self.assertEqual(selection2.lay_flag, False)

    def test_arbi_summary(self):
        match = mock.MagicMock(id='001')
        match.info = self.match_info
        match.odds.odds_dict = {
            # be aware that bookie_id 1, 2, 5 all have commissions
            ('FT', 'AH'): {0.5: {'1': ([2.05, 1.90], 'a!A1', time.time()),
                                  '2': ([2.00, 1.95], 'b!A2', time.time()),
                                  '5': ([1.95, 2.00], 'c!A3', time.time()),
                                 }
                           }
        }
        match_dict = {
            '001': match
        }

        spotter = ArbiSpotter(match_dict, profit_threshold=profit_threshold)
        spotter.initialize_strats()

        mock_datetime = mock.Mock()
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2011, 1, 1, 2, 3, 4, 5000)
        mock_datetime.timedelta.return_value = datetime.timedelta(hours=8)
        patch1 = mock.patch('arbi.models.arbi_spotter.datetime', mock_datetime)
        patch2 = mock.patch('arbi.models.opportunity.datetime', mock_datetime)
        with patch1, patch2:
            arbi_opps = spotter.spot_arbi()
            arbi_summary = [opp.get_summary() for opp in arbi_opps]

        expected = [[False, '1', '1.731 %', '2011-01-01 10:03:04.005', 'A Cup', 'A Cup', 'A', 'A', 0, 0, 'B', 'B',
                     'AH Home', 0.5, 'FT', 'crown_c', u'\u7687\u51a0_C', 49.4, 2.05, 2.065, '0.75 %', False,
                     'AH Away', -0.5, 'FT', 'ibcbet', u'\u6c99\u5df4', 50.6, 2.0, 2.005, '0.25 %', False]]
        self.assertEqual(arbi_summary, expected)


class ArbiSpotterMiscTest(TestCase):
    def test_selected_strats(self):
        menu_bar_model = mock.Mock()
        menu_bar_model.strats_panel_model.get_enabled_strats.return_value = [DirectArbiStrategy, CrossHandicapArbiStrategy]
        spotter = ArbiSpotter({}, menu_bar_model=menu_bar_model)
        spotter.initialize_strats()

        self.assertEqual(spotter.selected_strats_str, {'DirectArbiStrategy', 'CrossHandicapArbiStrategy'})

    def test_default_strats(self):
        defaults = {'DirectArbiStrategy', 'AHvsXvs2Strategy', 'AHvs2Strategy'}
        spotter = ArbiSpotter({})
        spotter.initialize_strats()

        self.assertEqual(spotter.selected_strats_str, defaults)

        # Select strats before run time
        spotter.menu_bar_model = mock.Mock()
        spotter.menu_bar_model.strats_panel_model.get_enabled_strats.return_value = [AHvsXvs2Strategy, EHvsEHXvsAHStrategy]

        # Run
        spotter.initialize_strats()
        self.assertEqual(spotter.selected_strats_str, {'AHvsXvs2Strategy', 'EHvsEHXvsAHStrategy'})


class ArbiSpotterMethodsTest(TestCase):
    def setUp(self):
        self.bookie_availability_dict = {bookie: {flag: True for flag in ['dead ball', 'running ball']}
                                         for bookie in ['b1', 'b2', 'b3', 'b7', 'b7 lay']}

    def test_check_running_ball_prices_expiry(self):
        t = time.time()
        match = mock.Mock()
        match.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'b1': ([2.05, 1.90], 'a!A1', t),
                                  'b2': ([2.00, 1.95], 'b!A2', 678.90),
                                  'b3': ([1.95, 2.00], 'c!A3', 246.84),
                                 }
                           }
        }

        spotter = ArbiSpotter({'101': match})

        spotter.check_running_ball_prices_expiry(match.odds.odds_dict)
        expected_odds_dict = {('FT', 'AH'): {0.5: {'b1': ([2.05, 1.90], 'a!A1', t)}}}
        self.assertEqual(match.odds.odds_dict, expected_odds_dict)

    def test_check_rb_prices_expiry(self):
        t = time.time()
        b1_odds_info = ([2.05, 1.90], 'a!A1', t)
        b2_odds_info = ([2.00, 1.95], 'b!A2', 67.9)
        b3_odds_info = ([2.05, 1.90], 'a!A1', t)
        b4_odds_info = ([2.00, 1.95], 'b!A2', 67.9)
        match1 = mock.Mock(is_in_running=True, id='101')
        match1.info = mock.MagicMock()
        match1.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'b1': b1_odds_info,
                                  'b2': b2_odds_info,
                                 }
                           }
        }

        match2 = mock.Mock(is_in_running=False, id='102')
        match2.info = mock.MagicMock()
        match2.odds.odds_dict = {
            ('FT', 'AH'): {0.5: {'b1': b3_odds_info,
                                  'b2': b4_odds_info,
                                 }
                           }
        }

        spotter = ArbiSpotter({'101': match1, '102': match2})
        spotter.last_rb_prices_expiry_checked -= 10
        # spotter.apply_strats = mock.Mock(return_value=[])
        spotter.apply_strats_in_parallel = mock.Mock(return_value={})
        old_last_rb_prices_expiry_checked = spotter.last_rb_prices_expiry_checked

        spotter.spot_arbi()

        expected_odds_dict1 = {('FT', 'AH'): {0.5: {'b1': b1_odds_info}}}
        expected_odds_dict2 = {('FT', 'AH'): {0.5: {'b1': b3_odds_info,
                                                     'b2': b4_odds_info}}}
        self.assertEqual(match1.odds.odds_dict, expected_odds_dict1)
        self.assertEqual(match2.odds.odds_dict, expected_odds_dict2)
        self.assertTrue(spotter.last_rb_prices_expiry_checked > old_last_rb_prices_expiry_checked)

    def test_update_raw_opps_dict(self):
        raw_opps_dict = {
            '001': {'1': ['a', 'b'], '2': []},
            '002': {'1': ['d'], '2': ['e', 'f']}
        }
        new_opps_dict = {
            '001': {'3': ['h', 'i']},
            '002': {'3': ['k']}
        }
        expected = {
            '001': {'1': ['a', 'b'], '2': [], '3': ['h', 'i']},
            '002': {'1': ['d'], '2': ['e', 'f'], '3': ['k']},
        }
        result = ArbiSpotter.update_raw_opps_dict(raw_opps_dict, new_opps_dict)
        self.assertEqual(result, expected)

    def test_update_raw_opps_dict_empty_raw_opps_dict(self):
        raw_opps_dict = {}
        new_opps_dict = {1: {'1': ['e', 'f'], '2': ['g']}}

        result = ArbiSpotter.update_raw_opps_dict(raw_opps_dict, new_opps_dict)
        self.assertEqual(result, new_opps_dict)

    def test_update_raw_opps_dict_empty_new_opps_dict(self):
        raw_opps_dict = {1: {'1': ['e', 'f'], '2': ['g']}}
        new_opps_dict = {}

        result = ArbiSpotter.update_raw_opps_dict(raw_opps_dict, new_opps_dict)
        self.assertEqual(result, raw_opps_dict)


    # def test_apply_strats_in_parallel(self):
    #     mock_strat_class1 = mock.Mock(__name__='1')
    #     mock_strat_class2 = mock.Mock(__name__='2')
    #     mock_match1 = mock.Mock()
    #     mock_match2 = mock.Mock()
    #     strats_model = mock.Mock()
    #     mock_bookie_av_dict = mock.Mock()
    #     strats_model.get_enabled_strats.return_value = [mock_strat_class1, mock_strat_class2]
    #
    #     spotter = ArbiSpotter({}, strats_model=strats_model)
    #     spotter.bookie_availability_dict = mock_bookie_av_dict
    #
    #     opps = spotter.apply_strats_in_parallel([mock_match1, mock_match2])
    #     spotter.selected_strats[0].spot_arbi.assert_called_once_with(mock_match1, mock_bookie_av_dict)

    def test_run_cross_handicap_arbi_strategy_async_1st_run(self):
        strats_panel_model = StratsPanelModel()
        strats_panel_model.use_cross_handicap_arb = True
        menu_bar_model = mock.Mock(strats_panel_model=strats_panel_model)
        spotter = ArbiSpotter({}, menu_bar_model=menu_bar_model)
        spotter.initialize_strats()

        self.assertEqual(spotter.cross_handicap_strat_result, None)

        raw_opps_dict = {'001': [1, 2, 3]}
        res = spotter.run_cross_handicap_strat([], raw_opps_dict)

        self.assertEqual(res, raw_opps_dict)
        self.assertIsInstance(spotter.cross_handicap_strat_result, AsyncResult)

    def test_run_cross_handicap_arbi_strategy_async_has_result(self):
        strats_panel_model = StratsPanelModel()
        strats_panel_model.use_cross_handicap_arb = True
        menu_bar_model = mock.Mock(strats_panel_model=strats_panel_model)
        spotter = ArbiSpotter({}, menu_bar_model=menu_bar_model)
        spotter.initialize_strats()

        async_result = mock.Mock()
        async_result.get.return_value = {'001': {'6': ['opp1', 'opp2']}, '002': {'6': ['opp3']}}
        spotter.cross_handicap_strat_result = async_result

        res = spotter.run_cross_handicap_strat([], {'001': {'5': ['opp0']}, '002': {'5': []}})
        expected = {
            '001': {'6': ['opp1', 'opp2'], '5': ['opp0']},
            '002': {'6': ['opp3'], '5': []}
        }

        self.assertEqual(res, expected)
