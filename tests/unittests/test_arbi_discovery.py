import mock
import datetime
from unittest2 import TestCase

from arbi.models.arbi_spotter import ArbiSpotter
from arbi.models.opportunity import ArbiOpportunity
from arbi.arbi_discovery import ArbiDiscoveryThread
from arbi.constants import BOOKIE_ID_MAP


class ArbiDiscoveryTest(TestCase):
    def setUp(self):
        mock_account_model = mock.Mock()
        mock_account_model.use_vip_mock_data = True
        mock_account_model.send_orders = False
        mock_account_model.exec_system_on_localhost = False
        mock_account_model.wait_for_vip_host_info = False
        mock_account_model.save_vip_history_flag = False
        mock_account_model.vip_mock_data_pkg_num = '_test1'
        mock_account_model.vip_account_index = ('', '')
        mock_account_model.profit_threshold = 0.01
        self.menu_bar_model = mock.Mock()
        self.menu_bar_model.account_model = mock_account_model

        self.occur_at_utc = datetime.datetime(2015, 4, 15, 20, 35, 22, 1000)

    def test_check_threads_alive(self):
        arbi_discovery = ArbiDiscoveryThread(mock.Mock(), None, None)
        arbi_discovery.check_vip_thread_flag = True
        arbi_discovery.check_betfair_thread_flag = True
        arbi_discovery.check_exec_msger_thread_flag = True
        arbi_discovery.threads_alive_last_checked = 100

        arbi_discovery.vip_feed_thread = mock.Mock()
        arbi_discovery.betfair_feed_thread = mock.Mock()
        arbi_discovery.exec_msger_thread = mock.Mock()
        arbi_discovery.run_exec_msger_thread = mock.Mock()

        arbi_discovery.vip_feed_thread.thread.is_alive.return_value = False
        arbi_discovery.betfair_feed_thread.thread.is_alive.return_value = False
        arbi_discovery.exec_msger_thread.thread.is_alive.return_value = False
        arbi_discovery.source_queue = mock.MagicMock()

        with mock.patch('time.time', return_value=120):
            arbi_discovery.check_threads_alive()

        self.assertEqual(arbi_discovery.threads_alive_last_checked, 120)
        arbi_discovery.vip_feed_thread.start.assert_called_once_with(delay=mock.ANY)
        arbi_discovery.betfair_feed_thread.start.assert_called_once_with(delay=mock.ANY)
        arbi_discovery.run_exec_msger_thread.assert_called_once_with(restart=True)

    def test_process_exec_msger_queue(self):
        arbi_discovery = ArbiDiscoveryThread(None, None, None)
        arbi_discovery.exec_msger_queue = mock.Mock()
        arbi_discovery.exec_msger_queue.empty.side_effect = [False, False, False, True]

        arbi_discovery.update_arbi_spotter_unavailable_bookie_ids = mock.Mock()
        arbi_discovery.switch_vip_feed = mock.Mock()
        arbi_discovery.exec_msger_queue.get.side_effect = [{'bookie id and status': {'bookie1': True}},
                                                           {'bookie id and status': {'bookie2': True}},
                                                           {'bookie id and status': {'bookie1': False}}]
        arbi_discovery.process_exec_msger_queue()
        arbi_discovery.update_arbi_spotter_unavailable_bookie_ids.assert_called_once_with(
            {'bookie1': False, 'bookie2': True})
        self.assertEqual(arbi_discovery.switch_vip_feed.called, 0)

    def test_process_exec_msger_queue_switch_vip_feed(self):
        arbi_discovery = ArbiDiscoveryThread(None, None, None)
        arbi_discovery.exec_msger_queue = mock.Mock()
        arbi_discovery.exec_msger_queue.empty.side_effect = [False, True]

        arbi_discovery.update_arbi_spotter_unavailable_bookie_ids = mock.Mock()
        arbi_discovery.switch_vip_feed = mock.Mock()
        arbi_discovery.exec_msger_queue.get.return_value = {'switch vip server': ('10.11.12.13', 4567)}
        arbi_discovery.process_exec_msger_queue()
        self.assertEqual(arbi_discovery.update_arbi_spotter_unavailable_bookie_ids.called, 0)
        arbi_discovery.switch_vip_feed.assert_called_once_with('10.11.12.13', 4567)

    def test_update_arbi_spotter_unavailable_bookie_ids(self):
        arbi_spotter = ArbiSpotter({})
        arbi_spotter.bookie_availability_dict = {
            'b1': {'dead ball': True, 'running ball': False},
            'b2': {'dead ball': True, 'running ball': False},
            'b3': {'dead ball': True, 'running ball': True},
        }

        arbi_discovery = ArbiDiscoveryThread(None, arbi_spotter, self.menu_bar_model)
        bookie_id_and_status = {
            'b1': {'running ball': True},
            'b2': {'dead ball': False},
            'b3': {'dead ball': True},
        }
        arbi_discovery.update_arbi_spotter_unavailable_bookie_ids(bookie_id_and_status)

        expected = {
            'b1': {'dead ball': True, 'running ball': True},
            'b2': {'dead ball': False, 'running ball': False},
            'b3': {'dead ball': True, 'running ball': True},
        }
        self.assertEqual(arbi_spotter.bookie_availability_dict, expected)

    def test_filter_bookies_leagues_and_teams(self):
        self.menu_bar_model.filter_panel_model.filtered_bookies = ['sbobet', 'ibcbet']
        self.menu_bar_model.filter_panel_model.filtered_leagues = ['ABC League']
        self.menu_bar_model.filter_panel_model.filtered_teams = ['Team X']

        arbi_discovery = ArbiDiscoveryThread(None, None, self.menu_bar_model)

        # 2: sbobet, 5: ibcbet, 69: pinnacle
        opp1 = ArbiOpportunity({'league_name': 'ABC League', 'home_team_name': 'Team X', 'away_team_name': 'a'},
                               self.occur_at_utc, '1', (0.02, ((0, 0, 0, '2', 0, 0, 0, False), (0, 0, 0, '5', 0, 0, 0, False))))
        opp2 = ArbiOpportunity({'league_name': 'foo League', 'home_team_name': 'Team X', 'away_team_name': 'a'},
                               self.occur_at_utc, '2', (0.02, ((0, 0, 0, '2', 0, 0, 0, False), (0, 0, 0, '5', 0, 0, 0, False))))
        opp3 = ArbiOpportunity({'league_name': 'ABC League', 'home_team_name': 'Team X', 'away_team_name': 'a'},
                               self.occur_at_utc, '3', (0.02, ((0, 0, 0, '2', 0, 0, 0, False), (0, 0, 0, '69', 0, 0, 0, False))))
        opp4 = ArbiOpportunity({'league_name': 'ABC League', 'home_team_name': 'Team X', 'away_team_name': 'a'},
                               self.occur_at_utc, '1', (0.02, ((0, 0, 0, '69', 0, 0, 0, False), (0, 0, 0, '5', 0, 0, 0, False))))
        opp5 = ArbiOpportunity({'league_name': 'ABC League', 'home_team_name': 'x', 'away_team_name': 'a'},
                               self.occur_at_utc, '2', (0.02, ((0, 0, 0, '2', 0, 0, 0, False), (0, 0, 0, '5', 0, 0, 0, False))))
        opp6 = ArbiOpportunity({'league_name': 'ABC League', 'home_team_name': 'Team X', 'away_team_name': 'a'},
                               self.occur_at_utc, '3', (0.02, ((0, 0, 0, '5', 0, 0, 0, False), (0, 0, 0, '2', 0, 0, 0, False))))

        arbi_opps = [opp1, opp2, opp3, opp4, opp5, opp6]
        results = arbi_discovery.filter_bookies_leagues_and_teams(arbi_opps)

        expected = [opp1, opp6]
        self.assertEqual(results, expected)

    def test_switch_vip_feed(self):
        arbi_discovery = ArbiDiscoveryThread(None, None, mock.Mock())
        arbi_discovery.signal = mock.Mock()
        arbi_discovery.run_vip_feed_thread = mock.Mock()
        arbi_discovery.vip_feed_thread = mock.Mock()
        new_ip = '12.34.56.78'
        new_port = 1234

        with mock.patch('time.sleep') as mock_sleep:
            arbi_discovery.switch_vip_feed(new_ip, new_port)

        self.assertEqual(arbi_discovery.menu_bar_model.account_model.vip_ip, new_ip)
        self.assertEqual(arbi_discovery.menu_bar_model.account_model.vip_port, new_port)
        arbi_discovery.vip_feed_thread.stop_event.set.assert_called_once_with()
        arbi_discovery.signal.switch_vip_server.emit.assert_called_once('{}:{}'.format(new_port, new_ip))
        arbi_discovery.run_vip_feed_thread.assert_called_once_with()
        mock_sleep.assert_called_once_with(5)

    def test_switch_yy_feed(self):
        arbi_discovery = ArbiDiscoveryThread(None, None, mock.Mock())
        arbi_discovery.signal = mock.Mock()
        arbi_discovery.run_betfair_feed_thread = mock.Mock()
        arbi_discovery.betfair_feed_thread = mock.Mock()
        new_ip = '12.34.56.78'
        new_port = 1234

        with mock.patch('time.sleep') as mock_sleep:
            arbi_discovery.switch_yy_feed(new_ip, new_port)

        self.assertEqual(arbi_discovery.menu_bar_model.account_model.yy_ip, new_ip)
        self.assertEqual(arbi_discovery.menu_bar_model.account_model.yy_port, new_port)
        arbi_discovery.betfair_feed_thread.stop_event.set.assert_called_once_with()
        arbi_discovery.signal.switch_yy_server.emit.assert_called_once('{}:{}'.format(new_port, new_ip))
        arbi_discovery.run_betfair_feed_thread.assert_called_once_with()
        mock_sleep.assert_called_once_with(5)

    def test_stop(self):
        arbi_discovery = ArbiDiscoveryThread(None, None, None)
        arbi_discovery.is_running = True
        arbi_discovery.vip_feed_thread = mock.Mock()
        arbi_discovery.betfair_feed_thread = mock.Mock()
        arbi_discovery.exec_msger_thread = mock.Mock()
        arbi_discovery.arbi_spotter = mock.Mock()

        arbi_discovery.stop()

        self.assertEqual(arbi_discovery.is_running, False)
        arbi_discovery.vip_feed_thread.stop_event.set.assert_called_once_with()
        arbi_discovery.betfair_feed_thread.stop_event.set.assert_called_once_with()
        arbi_discovery.exec_msger_thread.stop_event.set.assert_called_once_with()
        arbi_discovery.arbi_spotter.terminate_all_pools.assert_called_once_with()

    def test_init_arbi_spotter_unavailable_bookie_ids(self):
        spotter = ArbiSpotter({})
        arbi_discovery = ArbiDiscoveryThread(None, spotter, None)

        expected = {bookie_id: {'dead ball': False, 'running ball': False} for bookie_id in BOOKIE_ID_MAP.keys()}
        arbi_discovery.init_arbi_spotter_unavailable_bookie_ids()
        self.assertEqual(spotter.bookie_availability_dict, expected)

    def test_signal_table_view_update(self):
        self.menu_bar_model.account_model.table_view_update = True
        arbi_discovery = ArbiDiscoveryThread(None, None, self.menu_bar_model)
        arbi_discovery.signal.found = mock.Mock()

        dummy_summary = ['some dummy summary']
        opp1 = mock.Mock()
        opp1.get_summary.return_value = dummy_summary
        opp2 = mock.Mock()
        opp2.get_summary.return_value = dummy_summary
        arbi_opps = [opp1, opp2]

        arbi_discovery.signal_table_view_update(arbi_opps)
        arbi_discovery.signal.found.emit.assert_called_once_with([dummy_summary] * 2)
