import datetime
from mock import Mock, patch, call
from unittest2 import TestCase
from arbi.models.data_utils import log_opps_details


class TestFunctions(TestCase):
    def test_log_opps_details(self):
        opp1 = Mock()
        opp1.get_summary.return_value = ['Premier League', u'\u82f1\u8d85', 'Man U', u'\u66fc\u8054',
                                         0, 0, 'Arsenal', u'\u963f\u68ee\u7eb3']
        opp2 = Mock()
        opp2.get_summary.return_value = ['Italian A', u'\u610f\u7532', 'Milan', u'\u7c73\u5170',
                                         -1, -1, 'Inter', u'\u56fd\u9645']
        opps = [opp1, opp2]
        log = Mock()
        mock_header = ['League', 'League CN', 'Home', 'Home CN', 'Home Score',
                       'Away Score', 'Away', 'Away CN']
        with patch('arbi.models.data_utils.ARBI_SUMMARY_HEADER', mock_header):
            log_opps_details(log, opps)

        expected_calls = [
            call({'League': 'Premier League', 'League CN': '\xe8\x8b\xb1\xe8\xb6\x85',
             'Home': 'Man U', 'Home CN': '\xe6\x9b\xbc\xe8\x81\x94', 'Home Score': 0,
             'Away Score': 0, 'Away': 'Arsenal', 'Away CN': '\xe9\x98\xbf\xe6\xa3\xae\xe7\xba\xb3'}),
            call({'League': 'Italian A', 'League CN': '\xe6\x84\x8f\xe7\x94\xb2',
             'Home': 'Milan', 'Home CN': '\xe7\xb1\xb3\xe5\x85\xb0', 'Home Score': -1,
             'Away Score': -1, 'Away': 'Inter', 'Away CN': '\xe5\x9b\xbd\xe9\x99\x85'}),
        ]
        log.info.assert_has_calls(expected_calls)