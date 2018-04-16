import os
import time
import mock
from Queue import Queue
from unittest2 import TestCase
from arbi.feeds.vip.networking import VIPFeed, VIPFeedThreadObj
from arbi.feeds.base_feed import FeedConnectionError
from arbi.constants import ROOT_PATH
from arbi.tests.utils import simplify_dict
from arbi.models.record import VIPUpdateOddsRecord, MatchInfoRecord, InitOddsRecord


class VIPFeedThreadObjTest(TestCase):
    # A lot of code have been tested in test_data.py
    def ceate_thread_obj(self, source_queue=None, use_mock_data=True, data_gen=None, match_in_7_days=True):
        source_queue = source_queue
        use_mock_data = use_mock_data
        mock_data_pkg_num_or_data_gen = None, data_gen
        host_port = '', 0
        username_password = '', ''
        save_history_flag = False
        thread_obj = VIPFeedThreadObj(source_queue, use_mock_data, mock_data_pkg_num_or_data_gen, host_port,
                                      username_password, save_history_flag)
        if match_in_7_days:
            thread_obj.is_match_in_7_days = lambda record: True
        return thread_obj

    def test_create_data_feed(self):
        thread_obj = self.ceate_thread_obj(use_mock_data=False)
        data_feed = thread_obj.create_data_feed()
        self.assertIsNone(data_feed)

    def test_match_in_7_days(self):
        thread_obj = self.ceate_thread_obj(match_in_7_days=False)
        match_record = mock.Mock(record_dict={'match_hk_time': '2015-04-12 23:45:00'})
        self.assertEqual(thread_obj.is_match_in_7_days(match_record), True)

    def test_match_not_in_7_days(self):
        thread_obj = self.ceate_thread_obj(match_in_7_days=False)
        match_record = mock.Mock(record_dict={'match_hk_time': '2099-04-12 23:45:00'})
        self.assertEqual(thread_obj.is_match_in_7_days(match_record), False)

    def test_get_match_records_and_init_odds_records(self):
        packet = [
            'O0|4|101|2|0!A|1.840|3.650|6.0',
            'M101||Europa Cup||||Wolfsburg||||Napoli|||||1|0|0|1h 5|||'
        ]

        thread_obj = self.ceate_thread_obj()
        match_record_list, init_odds_record_list = thread_obj.get_match_records_and_init_odds_records(packet)

        self.assertEqual(len(match_record_list), 1)
        expected_match_record_dict = {
            'match_id': u'101', 'league_name': u'Europa Cup', 'home_team_name': u'Wolfsburg', 'away_team_name': u'Napoli',
            'running_time': u'1h 5', 'away_team_score': 0, 'home_team_score': 0,
        }
        cared_keys = expected_match_record_dict.keys()
        self.assertEqual(simplify_dict(match_record_list[0].record_dict, cared_keys), expected_match_record_dict)

        self.assertEqual(len(init_odds_record_list), 1)
        expected_init_odds_record_dict = {
            'event_type': 'FT', 'odds_type': 'OU', 'match_id': '101', 'bookie_id': '2',
            'bet_data': u'0!A', 'o1': 1.84, 'o2': 3.65, 'o3': 6.0,
        }
        cared_keys = expected_init_odds_record_dict.keys()
        self.assertEqual(simplify_dict(init_odds_record_list[0].record_dict, cared_keys), expected_init_odds_record_dict)

    def test_init_packet_contains_multiple_init_odds_for_the_same_match(self):
        packet = [
            'M101||Europa Cup||||Wolfsburg||||Napoli|||||1|0|0|1h 5|||',
            'O0|4|101|2|0!A|1.840|2.100|10.0',  # OU
            'O0|5|101|5|1!A|1.940|2.000|2.0',  # AH
            'O0|0|101|7|2!A|2.990|2.950|2.900',  # 1x2
        ]

        packet_gen = (packet for i in range(1))

        source_queue = Queue()
        thread_obj = self.ceate_thread_obj(source_queue=source_queue, data_gen=packet_gen)
        thread_obj.start(thread_daemon=False)

        init_dict = source_queue.get()
        self.assertEqual(len(init_dict), 1)
        self.assertIn('101', init_dict)
        expected_odds_dict = {
            ('FT', 'OU'): {2.5: {'2': ([1.84, 2.1], '0!A', mock.ANY)}},
            ('FT', 'AH'): {0.5: {'5': ([1.94, 2.0], '1!A', mock.ANY)}},
            ('FT', '1x2'): {None: {'7': ([2.99, 2.95, 2.9], '2!A', mock.ANY)}},
        }
        self.assertEqual(init_dict['101'].odds.odds_dict, expected_odds_dict)

    def test_do_not_support_basketball(self):
        data = ['M1135514|35|NBA|NBA|NBA|799|L.A. Clippers|Kuai Chuan|Kuai Ting|821|A.Hawks|Lao Ying|Ying Dui|2016-03-06 11:30:00|#ff0000|1|0|0||1|-1|-1',
                'M1135514|35|NBA|NBA|NBA|799|L.A. Clippers|Kuai Chuan|Kuai Ting|821|A.Hawks|Lao Ying|Ying Dui|2016-03-06 11:30:00|#ff0000|1|0|0||1|-1|-1',
                'o1234|0|0|1135514|24|2!A2|4.550|3.440|2.0',
                ]
        packet_gen = ([d] for d in data)

        source_queue = Queue()
        thread_obj = self.ceate_thread_obj(source_queue=source_queue, data_gen=packet_gen)
        thread_obj.start(thread_daemon=False)

        init_dict = source_queue.get()
        self.assertEqual(init_dict, {})  # init_dict does not have basketball match
        # data[1] is not here as basketball is not supported
        record_list = source_queue.get()
        self.assertEqual(len(record_list), 1)
        self.assertEqual(record_list[0].record_str, data[2])

    def test_support_basketball(self):
        data = ['M1135514|35|NBA|NBA|NBA|799|L.A. Clippers|Kuai Chuan|Kuai Ting|821|A.Hawks|Lao Ying|Ying Dui|2016-03-06 11:30:00|#ff0000|1|0|0||1|-1|-1',
                'M1135514|35|NBA|NBA|NBA|799|L.A. Clippers|Kuai Chuan|Kuai Ting|821|A.Hawks|Lao Ying|Ying Dui|2016-03-06 11:30:00|#ff0000|1|0|0||1|-1|-1',
                'o1234|0|0|1135514|24|2!A2|4.550|3.440|2.0',
                ]

        packet_gen = ([d] for d in data)

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

        for i, record_str in enumerate(data):
            record_list = source_queue.get()
            if i:
                self.assertTrue(isinstance(record_list, list))
                self.assertEqual(record_list[0].record_str, record_str)
            else:
                self.assertTrue(isinstance(record_list, dict))
                self.assertEqual(len(record_list), 1)
                self.assertNotEqual(record_list, {})
                self.assertIn('1135514', record_list)

    def test_update_vip_update_id(self):
        thread_obj = self.ceate_thread_obj(use_mock_data=False)
        self.assertEqual(thread_obj.vip_data_update_id_dict, {})

        record = InitOddsRecord('O0|0|972960|2|1624750!A21696851|1.840|3.650|3.850')
        self.assertTrue(thread_obj.update_vip_update_id(record))
        self.assertEqual(thread_obj.vip_data_update_id_dict, {'972960': 0})

        record = VIPUpdateOddsRecord('o11866|0|0|972960|5|4338773245!A127367|1.750|3.550|4.100')
        self.assertTrue(thread_obj.update_vip_update_id(record))
        self.assertEqual(thread_obj.vip_data_update_id_dict, {'972960': 11866})

        record = VIPUpdateOddsRecord('o11865|0|0|972960|5|4338773245!A127367|1.750|3.550|4.100')
        self.assertFalse(thread_obj.update_vip_update_id(record))
        self.assertEqual(thread_obj.vip_data_update_id_dict, {'972960': 11866})


class VIPFeedTest(TestCase):
    def test(self):
        def mock_read_data():
            time.sleep(0.2)
            return []

        with mock.patch('arbi.feeds.base_feed.socket'):
            feed = VIPFeed('', '')

        feed.read_data = mock_read_data

        with mock.patch('arbi.feeds.base_feed.TIME_THRESHOLD_TO_GET_ONE_PACKET', 0.1):
            feed.login('', '')
            feed.get_one_packet()

        feed.logout()

    def test_read_data(self):
        with mock.patch('arbi.feeds.base_feed.socket'):
            feed = VIPFeed('', '')

        with open(os.path.join(ROOT_PATH, 'mock_data/vip/stream1000.txt')) as f:
            feed.rfile = f
            feed.get_one_packet()  # the first time returns login successful message

            with self.assertRaises(FeedConnectionError):
                feed.get_one_packet()


# class MockFeedTest(TestCase):
#     def test(self):
#         queue = Queue()
#         use_mock_data = True
#         mock_data_pkg_num_or_data_gen = 'test_with_timestamp', None
#         host_port = '', ''
#         username_password = '', ''
#         save_history_flag = False
#         thread_obj = VIPFeedThreadObj(queue, use_mock_data, mock_data_pkg_num_or_data_gen, host_port,
#                                       username_password, save_history_flag)
#         thread_obj.start()
#         time.sleep(2)
#         self.assertFalse(queue.empty())
