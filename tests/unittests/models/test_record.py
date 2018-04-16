from mock import patch, ANY
from Queue import Queue
from unittest2 import TestCase
from arbi.models.engine import DataEngine
from arbi.models.match import Match
from arbi.feeds.vip.networking import VIPFeedThreadObj
from arbi.feeds.betfair.feed import BetfairFeedThreadObj
from arbi.models.record import MatchInfoRecord


class RecordTest(TestCase):
    #todo need to test all methods in all record classes

    def test_update_YYUpdateOddsRecord(self):
        queue = None
        use_mock_data = True
        mock_data_pkg_num_or_data_gen = None, None
        host_port = '', ''
        username_password = '', ''
        save_history_flag = False
        thread_obj = BetfairFeedThreadObj(queue, use_mock_data, mock_data_pkg_num_or_data_gen, host_port,
                                          username_password, save_history_flag)

        packets = [
            ['M972960|891|Europa Cup|Europa Cup|Europa Cup|1348|Wolfsburg|Wolfsburg|Wolfsburg|1012|Napoli|Napoli|Napoli|2015-04-17 03:05:00|#6F00DD|0|0|0||1|-1|-1'],
            ['o11866|0|0|9|-2|972960|7|4338773245!A127367|2.90|3.00|3.10'],
            ['o11867|1|0|9|-2|972960|7|1234567890!A123456|2.95|3.05|3.15'],
        ]

        engine = DataEngine()
        engine.match_dict = {'972960': Match(MatchInfoRecord(packets[0][0]))}
        mock_time = 12367

        # update 1
        record_list = thread_obj.get_record_list_from_packet(packets[1])
        self.assertNotEqual(record_list, [])

        with patch('time.time', return_value=mock_time):
            engine.update_match_dict(record_list)

        expected_odds_dict = {('FT', 'EH'): {-0.5: {'7': ([2.90, 3.00, 3.10], '4338773245!A127367', mock_time)}}}
        self.assertEqual(engine.match_dict['972960'].odds.odds_dict, expected_odds_dict)

        # update 2
        record_list = thread_obj.get_record_list_from_packet(packets[2])
        self.assertNotEqual(record_list, [])

        with patch('time.time', return_value=mock_time):
            engine.update_match_dict(record_list)

        expected_odds_dict = {('FT', 'EH'): {-0.5: {'7': ([2.90, 3.00, 3.10], '4338773245!A127367', mock_time),
                                                   '7 lay': ([2.95, 3.05, 3.15], '1234567890!A123456', mock_time),
                                                   }}
                             }
        self.assertEqual(engine.match_dict['972960'].odds.odds_dict, expected_odds_dict)

    def test_loading_1or2_update_record(self):
        data = ['M1135514|35|NBA|NBA|NBA|799|L.A. Clippers|Kuai Chuan|Kuai Ting|821|A.Hawks|Lao Ying|Ying Dui|2016-03-06 11:30:00|#ff0000|1|0|0||1|-1|-1',
                'O0|6|1135514|5|1624750!B21698258|1.830|2.170|0.000',
                ]

        packet_gen = (data for i in range(1))

        source_queue = Queue()
        use_mock_data = True
        mock_data_pkg_num_or_data_gen = None, packet_gen
        ip_and_port = '', 0
        username_password = '', ''
        save_history_flag = False

        thread_obj = VIPFeedThreadObj(source_queue, use_mock_data, mock_data_pkg_num_or_data_gen, ip_and_port,
                                  username_password, save_history_flag,
                                  sports_supported=frozenset(['football', 'basketball']))
        thread_obj.start(thread_daemon=False)

        expected_odds_dict = {('FT', '1or2'): {None: {'5': ([1.83, 2.17], '1624750!B21698258', ANY)}}}
        init_dict = source_queue.get()
        self.assertEqual(init_dict['1135514'].odds.odds_dict, expected_odds_dict)
