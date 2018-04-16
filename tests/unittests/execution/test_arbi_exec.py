import socket
import time
import datetime
import inspect
from mock import patch, Mock
from unittest2 import TestCase

from arbi.utils import gzip_string
from arbi.execution.arbi_exec import ArbiExecMessenger, MockMessenger, ArbiExecMsgerThreadObj, ExecMsgerConnectionError
from arbi.models.opportunity import ArbiOpportunity


class ArbiExecTest(TestCase):
    def test_login(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        messenger.create_packet = lambda x: x
        messenger.wfile = mock_wfile = Mock()

        with patch('arbi.execution.arbi_exec.gzip_string', lambda x: x):
            for return_message, expected_result in [('true', True), ('false', False)]:
                messenger.read_exec_msg = lambda is_blocked_read=True: [return_message]
                result = messenger.login('username', 'password', '1.2.3')

                expected_msg = 'NL^1.0^username^password^1.2.3'
                mock_wfile.write.assert_called_with(expected_msg)
                self.assertEqual(result, expected_result)

    def test_send(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        messenger.wfile = mock_wfile = Mock()
        messenger.filter_by_bet_frequency_restriction = lambda x: x

        # bookie id: 1: crown_d, 24: pinnacle
        selection1 = ('AH Home', -0.5, 'FT', 1, 49.3, 2.08, 'a!A1', False)
        selection2 = ('AH Away', 0.5, 'FT', 24, 50.7, 2.02, 'b!B2', False)
        match_info = {'match_id': '123', 'league_name': 'foo', 'match_hk_time': '2015-04-16 06:45:00', 'is_in_running': True,
                      'home_team_name': 'bar', 'away_team_name': 'baz', 'home_team_score': 0, 'away_team_score': 0}
        strat_id = '3'
        arbi_opps = [ArbiOpportunity(match_info, datetime.datetime(2015, 4, 15, 22, 55, 0, 1000), strat_id, (0.02544, (selection1, selection2)))]

        hk_time = (2015, 4, 16, 06, 55)
        messenger.get_hk_now = lambda: datetime.datetime(*hk_time)
        with patch('arbi.execution.arbi_exec.gzip_string', lambda x: x):
            messenger.send(arbi_opps)

        # Be careful that the handicap for away team is the same as that of home team.
        expected_msg_body = 'NB^3^1^123^0^0^2.544^2015-04-16 06:55:00.001^O1|a!1|4|-2|2.08|49.3|0^O24|b!2|5|2|2.02|50.7|0'
        expected_msg_head = chr(len(expected_msg_body)) + '\x00\x00\x00'
        mock_wfile.write.assert_called_with(expected_msg_head + expected_msg_body + '[END]')

    def test_send_lay(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        messenger.wfile = mock_wfile = Mock()
        messenger.filter_by_bet_frequency_restriction = lambda x: x

        opp = (0.03066, (('OU Over', 0.5, 'FT', '15', 89.8, 1.15, 'a!A1', False),
                         ('OU Over', 0.5, 'FT', '7', 10.2, 1.11, 'b!B2', True)))
        match_info = {'match_id': '123', 'league_name': 'foo', 'match_hk_time': '2015-04-16 06:45:00', 'is_in_running': True,
                      'home_team_name': 'bar', 'away_team_name': 'baz', 'home_team_score': 0, 'away_team_score': 0}
        strat_id = '4'
        arbi_opps = [ArbiOpportunity(match_info, datetime.datetime(2015, 4, 15, 22, 55, 0, 1000), strat_id, opp)]

        hk_time = (2015, 4, 16, 06, 55)
        messenger.get_hk_now = lambda: datetime.datetime(*hk_time)
        with patch('arbi.execution.arbi_exec.gzip_string', lambda x: x):
            messenger.send(arbi_opps)

        # Be careful that the handicap for away team is the same as that of home team.
        expected_msg_body = 'NB^4^1^123^0^0^3.066^2015-04-16 06:55:00.001^O15|a!1|0|2|1.15|89.8|0^O7|b!2|0|2|1.11|10.2|1'
        expected_msg_head = chr(len(expected_msg_body)) + '\x00\x00\x00'
        mock_wfile.write.assert_called_with(expected_msg_head + expected_msg_body + '[END]')

    def test_send_3selections(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        messenger.wfile = mock_wfile = Mock()
        messenger.filter_by_bet_frequency_restriction = lambda x: x

        # bookie id: 1: crown_d, 24: pinnacle
        selection1 = ('AH Home', -0.5, 'FT', 1, 45.2, 1.66, 'a!A1', False)
        selection2 = ('1x2', 'Draw', 'FT', 24, 33.7, 2.88, 'b!B2', False)
        selection3 = ('1x2', 'Away', 'FT', 5, 21.1, 3.52, 'c!B3', False)
        match_info = {'match_id': '123', 'league_name': 'foo', 'match_hk_time': '2015-04-16 06:45:00', 'is_in_running': False,
                      'home_team_name': 'bar', 'away_team_name': 'baz', 'home_team_score': -1, 'away_team_score': -1}
        strat_id = '5'
        arbi_opps = [ArbiOpportunity(match_info, datetime.datetime(2015, 4, 15, 22, 55, 0, 1000), strat_id, (0.08438, (selection1, selection2, selection3)))]

        for hk_time, time_type in [((2015, 4, 15, 15, 20), 0), ((2015, 4, 15, 11, 5), 2), ((2015, 4, 14), 2)]:
            with patch('arbi.execution.arbi_exec.gzip_string', lambda x: x), patch('arbi.execution.arbi_exec.get_hk_time_now', return_value = datetime.datetime(*hk_time)):
                messenger.send(arbi_opps)
            expected_msg_body = 'NB^5^{0}^123^-1^-1^8.438^2015-04-16 06:55:00.001^O1|a!1|4|-2|1.66|45.2|0^O24|b!2|10||2.88|33.7|0^O5|c!3|9||3.52|21.1|0'.format(time_type)
            expected_msg_head = chr(len(expected_msg_body)) + '\x00\x00\x00'
            mock_wfile.write.assert_called_with(expected_msg_head + expected_msg_body + '[END]')

    def test_send_heartbeat(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        messenger.wfile = mock_wfile = Mock()

        messenger.send_heartbeat()
        mock_wfile.write.assert_called_with(messenger.heartbeat_pkt)

    def test_filter_by_bookie_cooldown(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')

        messenger.cooldown_opps = {(1, '001', 0, 0): {'B2|5|2': 2.01, 'B5|7|8': 1.99}}
        messenger._get_time_type = lambda x: 1
        now = datetime.datetime.utcnow()
        opp1 = ArbiOpportunity({'match_id': '001', 'home_team_score': 0, 'away_team_score': 0}, now, '1',
                               (0, (('AH Home', -0.5, 'FT', '1', 0, 2.02, '', False),
                                    ('AH Away', 0.5, 'FT', '2', 0, 2.01, '', False))))
        opp2 = ArbiOpportunity({'match_id': '001', 'home_team_score': 0, 'away_team_score': 0}, now, '2',
                               (0, (('AH Home', -0.5, 'FT', '3', 0, 2.01, '', False),
                                    ('AH Away', 0.5, 'FT', '4', 0, 2.01, '', False))))
        opp3 = ArbiOpportunity({'match_id': '001', 'home_team_score': 0, 'away_team_score': 0}, now, '3',
                               (0, (('AH Home', -0.75, 'FT', '1', 0, 2.01, '', False),
                                    ('AH Away', 0.75, 'FT', '2', 0, 2.01, '', False))))
        opp4 = ArbiOpportunity({'match_id': '001', 'home_team_score': 0, 'away_team_score': 0}, now, '1',
                               (0, (('1x2', 'Home', 'FT', '1', 0, 2.02, '', False),
                                    ('AH Away', 0.5, 'FT', '2', 0, 2.01, '', False))))
        opp5 = ArbiOpportunity({'match_id': '002', 'home_team_score': 0, 'away_team_score': 0}, now, '2',
                               (0, (('AH Home', -0.5, 'FT', '1', 0, 2.02, '', False),
                                    ('AH Away', 0.5, 'FT', '2', 0, 2.01, '', False))))
        opp6 = ArbiOpportunity({'match_id': '001', 'home_team_score': 0, 'away_team_score': 0}, now, '3',
                               (0, (('AH Home', -0.5, 'FT', '1', 0, 2.02, '', False),
                                    ('AH Away', 0.5, 'FT', '2', 0, 2.02, '', False))))

        self.assertEqual(messenger.any_bookie_in_cooldown(opp1), True)
        self.assertEqual(messenger.cooldown_opps, {(1, '001', 0, 0): {'B2|5|2': 2.01, 'B5|7|8': 1.99}})

        self.assertEqual(messenger.any_bookie_in_cooldown(opp2), False)
        self.assertEqual(messenger.cooldown_opps, {(1, '001', 0, 0): {'B2|5|2': 2.01, 'B5|7|8': 1.99,
                                                                       'B3|4|-2': 2.01, 'B4|5|2': 2.01}})

        self.assertEqual(messenger.any_bookie_in_cooldown(opp3), False)
        self.assertEqual(messenger.cooldown_opps, {(1, '001', 0, 0): {'B2|5|2': 2.01, 'B5|7|8': 1.99,
                                                                       'B3|4|-2': 2.01, 'B4|5|2': 2.01,
                                                                       'B2|5|3': 2.01, 'B1|4|-3': 2.01}})

        self.assertEqual(messenger.any_bookie_in_cooldown(opp4), True)
        self.assertEqual(messenger.cooldown_opps, {(1, '001', 0, 0): {'B2|5|2': 2.01, 'B5|7|8': 1.99,
                                                                       'B3|4|-2': 2.01, 'B4|5|2': 2.01,
                                                                       'B2|5|3': 2.01, 'B1|4|-3': 2.01}})

        self.assertEqual(messenger.any_bookie_in_cooldown(opp5), False)
        self.assertEqual(messenger.cooldown_opps, {(1, '002', 0, 0): {'B2|5|2': 2.01, 'B1|4|-2': 2.02},
                                                   (1, '001', 0, 0): {'B3|4|-2': 2.01, 'B5|7|8': 1.99, 'B4|5|2': 2.01,
                                                                       'B2|5|3': 2.01, 'B2|5|2': 2.01, 'B1|4|-3': 2.01}})

        self.assertEqual(messenger.any_bookie_in_cooldown(opp6), False)
        self.assertEqual(messenger.cooldown_opps, {(1, '002', 0, 0): {'B2|5|2': 2.01, 'B1|4|-2': 2.02},
                                                   (1, '001', 0, 0): {'B3|4|-2': 2.01, 'B5|7|8': 1.99, 'B4|5|2': 2.01,
                                                                       'B2|5|3': 2.01, 'B2|5|2': 2.02, 'B1|4|-3': 2.01,
                                                                       'B1|4|-2': 2.02}})

    def test_process_exec_msg(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        messenger.check_cooldown_opps_timestamp = lambda : None
        self.assertEqual(messenger.cooldown_opps, {})

        messenger.cooldown_opps = {('2', '1014182', '-1', '-1'): {'B2|4|-5': 100, 'B52|5|5': 200}}
        messenger.read_exec_msg = lambda: ['NS^1^0^2', 'NS^3^9^1', 'NS^a^b^c^d', 'XX^2^1',
                                            'NR^2^1014182^-1^-1^B2|4|-5^B3|5|5', 'NR^2^1014183^1^0^B2|4|-5']
        bookie_id_and_status = messenger.process_exec_msg()
        self.assertEqual(bookie_id_and_status, {'bookie id and status': {'1': {'running ball': False}}})
        self.assertEqual(messenger.cooldown_opps, {('2', '1014182', '-1', '-1'): {'B52|5|5': 200}})

        messenger.read_exec_msg = lambda: ['NS^2^0^1', 'NS^1^1^2']
        bookie_id_and_status = messenger.process_exec_msg()
        expected = {'bookie id and status': {'1': {'running ball': True},
                                                '2': {'dead ball': False}}}
        self.assertEqual(bookie_id_and_status, expected)

    def test_process_exec_ns_msg_add_to_empty(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        msg = 'NS^2^0^0'
        bookie_id_and_status = {}
        messenger.process_exec_ns_msg(bookie_id_and_status, msg)
        expected = {'2': {'dead ball': False, 'running ball': False}}
        self.assertEqual(bookie_id_and_status, expected)

    def test_process_exec_ns_msg_add_to_empty_with_lay_bookie(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        msg = 'NS^7^1^0'
        bookie_id_and_status = {}
        messenger.process_exec_ns_msg(bookie_id_and_status, msg)
        expected = {'7': {'dead ball': True, 'running ball': True},
                    '7 lay': {'dead ball': True, 'running ball': True}}
        self.assertEqual(bookie_id_and_status, expected)

    def test_process_exec_ns_msg_add_one_bet_period(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        msg = 'NS^1^1^1'
        bookie_id_and_status = {'1': {'running ball': True}}
        messenger.process_exec_ns_msg(bookie_id_and_status, msg)
        expected = {'1': {'dead ball': True, 'running ball': True}}
        self.assertEqual(bookie_id_and_status, expected)

    def test_process_exec_ns_msg_add_one_bet_period_with_lay_bookie(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        msg = 'NS^7^1^1'
        bookie_id_and_status = {'7': {'running ball': True},
                                '7 lay': {'running ball': True}}
        messenger.process_exec_ns_msg(bookie_id_and_status, msg)
        expected = {'7': {'dead ball': True, 'running ball': True},
                    '7 lay': {'dead ball': True, 'running ball': True}}
        self.assertEqual(bookie_id_and_status, expected)

    def test_process_exec_ns_msg_replace_one_bet_period(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        msg = 'NS^1^1^2'
        bookie_id_and_status = {'1': {'running ball': False, 'dead ball': True}}
        messenger.process_exec_ns_msg(bookie_id_and_status, msg)
        expected = {'1': {'dead ball': True, 'running ball': True}}
        self.assertEqual(bookie_id_and_status, expected)

    def test_process_exec_ns_msg_replace_one_bet_period_with_lay_bookie(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        msg = 'NS^7^1^2'
        bookie_id_and_status = {'7': {'running ball': False, 'dead ball': True},
                                '7 lay': {'running ball': False, 'dead ball': True}}
        messenger.process_exec_ns_msg(bookie_id_and_status, msg)
        expected = {'7': {'dead ball': True, 'running ball': True},
                    '7 lay': {'dead ball': True, 'running ball': True}}
        self.assertEqual(bookie_id_and_status, expected)

    def test_process_exec_ns_msg_with_lay_bookies(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')
        msg = 'NS^7^0^0'
        bookie_id_and_status = {}
        messenger.process_exec_ns_msg(bookie_id_and_status, msg)
        expected = {
            '7': {'dead ball': False, 'running ball': False},
            '7 lay': {'dead ball': False, 'running ball': False},
        }
        self.assertEqual(bookie_id_and_status, expected)

    def test_read_exec_msg_no_message(self):
        def mock_read(n):
            raise socket.error

        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')

        messenger.rfile.read = mock_read
        with self.assertRaises(ExecMsgerConnectionError):
            messenger.read_exec_msg()

    def test_read_exec_msg_unzip_error(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')

        original_message = 'hello world !'
        packet = messenger.create_packet(original_message)

        messenger.rfile.read.side_effect = [packet[:4], packet[4:-5]]
        result = messenger.read_exec_msg()

        self.assertEqual(result, [])

    def test_read_exec_msg_get_body_size_error(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')

        messenger.rfile.read.return_value = '' * 4
        result = messenger.read_exec_msg()

        self.assertEqual(result, [])

    def test_read_exec_msg(self):
        with patch('arbi.execution.arbi_exec.socket'):
            messenger = ArbiExecMessenger('', '')

        original_message = 'hello world !' * 1000
        packet = messenger.create_packet(gzip_string(original_message))

        messenger.rfile.read.side_effect = [packet[:4], packet[4: -5]]  # remove [END] from the end whose length is 5
        result = messenger.read_exec_msg()

        self.assertEqual(result, [original_message])

    def test_MockMessenger(self):
        msger = MockMessenger(None, None)
        for name in ['write', 'reconnect', 'send_heartbeat', 'process_exec_msg']:
            method = getattr(msger, name)
            if callable(method):
                args = inspect.getargspec(method).args
                method(*args[1:])


class ArbiExecMsgerThreadObjTest(TestCase):
    def test_create_exec_messenger(self):
        thread_obj = ArbiExecMsgerThreadObj(None, True, True)
        messenger = thread_obj.create_exec_messenger(True, True)
        self.assertIsNone(messenger)

    def test(self):
        thread_obj = ArbiExecMsgerThreadObj(None, True, True)
        thread_obj.start()
