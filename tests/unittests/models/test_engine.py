import datetime
from mock import Mock, patch
from Queue import Queue
from unittest2 import TestCase
from arbi.models.engine import DataEngine
from arbi.feeds.vip.networking import VIPFeedThreadObj


class DataEngineTest(TestCase):
    def test(self):
        queue = None
        use_mock_data = True
        mock_data_pkg_num_or_data_gen = None, None
        host_port = '', ''
        username_password = '', ''
        save_history_flag = False
        thread_obj = VIPFeedThreadObj(queue, use_mock_data, mock_data_pkg_num_or_data_gen, host_port,
                                      username_password, save_history_flag)
        thread_obj.is_match_in_7_days = lambda record: True
        packets = [
            ['O0|0|972960|2|1624750!A21696851|1.840|3.650|3.850',
             'M972960|891|Europa Cup|\xc5\xb7\xb0\xd4\xb1\xad|\x9aW\xb0\xd4\xb0\xa0|1348|Wolfsburg|\xce\xd6\xb6\xfb\xb7\xf2\xcb\xb9\xb1\xa4|\xce\xd6\xa0\x96\xb7\xf2\xcb\xb9\xb1\xa4|1012|Napoli|\xc4\xc7\xb2\xbb\xc0\xd5\xcb\xb9|\xc4\xc3\xb2\xa3\xc0\xef|2015-04-17 03:05:00|#6F00DD|0|0|0||1|-1|-1'],
            ['o11866|0|0|972960|5|4338773245!A127367|1.750|3.550|4.100'],
            ['M972960|891|Europa Cup|\xc5\xb7\xb0\xd4\xb1\xad|\x9aW\xb0\xd4\xb0\xa0|1348|Wolfsburg|\xce\xd6\xb6\xfb\xb7\xf2\xcb\xb9\xb1\xa4|\xce\xd6\xa0\x96\xb7\xf2\xcb\xb9\xb1\xa4|1012|Napoli|\xc4\xc7\xb2\xbb\xc0\xd5\xcb\xb9|\xc4\xc3\xb2\xa3\xc0\xef|2015-04-17 03:05:00|#6F00DD|1|0|0|ht|1|-1|-1',
             'o11867|0|0|972960|2|1234567890!A123456|1.810|3.600|3.950'],
            ['M972960|891|Europa Cup|\xc5\xb7\xb0\xd4\xb1\xad|\x9aW\xb0\xd4\xb0\xa0|1348|Wolfsburg|\xce\xd6\xb6\xfb\xb7\xf2\xcb\xb9\xb1\xa4|\xce\xd6\xa0\x96\xb7\xf2\xcb\xb9\xb1\xa4|1012|Napoli|\xc4\xc7\xb2\xbb\xc0\xd5\xcb\xb9|\xc4\xc3\xb2\xa3\xc0\xef|2015-04-17 03:05:00|#6F00DD|1|1|0|2h 5|1|-1|-1']
        ]
        engine = DataEngine()
        self.assertEqual(engine.match_dict, {})

        # initial stage
        mock_time1 = 12345
        with patch('time.time', return_value=mock_time1):
            match_dict = thread_obj.initialize_match_dict(packets[0])
        engine.init_match_dict(match_dict)

        expected_match_info = {'match_id': u'972960', 'away_team_name': u'Napoli', 'home_team_red_card': u'-1', 'home_team_name': u'Wolfsburg', 'match_hk_time': u'2015-04-17 03:05:00', 'away_team_name_trad': u'\u62ff\u73bb\u91cc', 'home_team_name_trad': u'\u6c83\u723e\u592b\u65af\u5821', 'group_color': u'#6F00DD', 'away_team_id': u'1012', 'away_team_name_simp': u'\u90a3\u4e0d\u52d2\u65af', 'away_team_red_card': u'-1', 'is_in_running': False, 'running_time': u'', 'league_id': u'891', 'will_run': u'1', 'league_name_simp': u'\u6b27\u9738\u676f', 'home_team_id': u'1348', 'home_team_name_simp': u'\u6c83\u5c14\u592b\u65af\u5821', 'league_name_trad': u'\u6b50\u9738\u76c3', 'league_name': u'Europa Cup', 'away_team_score': -1, 'home_team_score': -1}
        # last_update in odds dict should be when the odds object was created, which is mock_time1 in this case
        expected_odds_dict = {('FT', '1x2'): {None: {u'2': ([1.84, 3.65, 3.85], '1624750!A21696851', mock_time1)}}}

        self.assertEqual(len(engine.match_dict), 1)
        match = engine.match_dict.values()[0]
        self.assertEqual(match.info, expected_match_info)
        self.assertEqual(match.odds.odds_dict, expected_odds_dict)

        # update stage
        record_list = thread_obj.get_update_record_list(packets[1])
        mock_time2 = 12367
        with patch('time.time', return_value=mock_time2):
            engine.update_match_dict(record_list)
        # last_update in odds dict can be different for different bookies
        expected_odds_dict = {('FT', '1x2'): {None: {'2': ([1.84, 3.65, 3.85], '1624750!A21696851', mock_time1),
                                                      '5': ([1.75, 3.55, 4.10], '4338773245!A127367', mock_time2),
                                                     }}
                             }
        self.assertEqual(match.odds.odds_dict, expected_odds_dict)

        # update again
        record_list = thread_obj.get_update_record_list(packets[2])
        mock_time3 = 12389
        with patch('time.time', return_value=mock_time3):
            engine.update_match_dict(record_list)

        expected_match_info = {'match_id': u'972960', 'away_team_name': u'Napoli', 'home_team_red_card': u'-1', 'home_team_name': u'Wolfsburg', 'match_hk_time': u'2015-04-17 03:05:00', 'away_team_name_trad': u'\u62ff\u73bb\u91cc', 'home_team_name_trad': u'\u6c83\u723e\u592b\u65af\u5821', 'group_color': u'#6F00DD', 'away_team_id': u'1012', 'away_team_name_simp': u'\u90a3\u4e0d\u52d2\u65af', 'away_team_red_card': u'-1', 'is_in_running': True, 'running_time': u'ht', 'league_id': u'891', 'will_run': u'1', 'league_name_simp': u'\u6b27\u9738\u676f', 'home_team_id': u'1348', 'home_team_name_simp': u'\u6c83\u5c14\u592b\u65af\u5821', 'league_name_trad': u'\u6b50\u9738\u76c3', 'league_name': u'Europa Cup', 'away_team_score': 0, 'home_team_score': 0}
        expected_odds_dict = {('FT', '1x2'): {None: {'2': ([1.81, 3.60, 3.95], '1234567890!A123456', mock_time3),
                                                      '5': ([1.75, 3.55, 4.10], '4338773245!A127367', mock_time2),
                                                     }}
                             }
        self.assertEqual(match.info, expected_match_info)
        self.assertEqual(match.odds.odds_dict, expected_odds_dict)

        # update scores should clear all prices
        record_list = thread_obj.get_update_record_list(packets[3])
        engine.update_match_dict(record_list)

        expected_match_info = {'match_id': u'972960', 'away_team_name': u'Napoli', 'home_team_red_card': u'-1', 'home_team_name': u'Wolfsburg', 'match_hk_time': u'2015-04-17 03:05:00', 'away_team_name_trad': u'\u62ff\u73bb\u91cc', 'home_team_name_trad': u'\u6c83\u723e\u592b\u65af\u5821', 'group_color': u'#6F00DD', 'away_team_id': u'1012', 'away_team_name_simp': u'\u90a3\u4e0d\u52d2\u65af', 'away_team_red_card': u'-1', 'is_in_running': True, 'running_time': u'2h 5', 'league_id': u'891', 'will_run': u'1', 'league_name_simp': u'\u6b27\u9738\u676f', 'home_team_id': u'1348', 'home_team_name_simp': u'\u6c83\u5c14\u592b\u65af\u5821', 'league_name_trad': u'\u6b50\u9738\u76c3', 'league_name': u'Europa Cup', 'away_team_score': 0, 'home_team_score': 1}
        self.assertEqual(match.info, expected_match_info)
        self.assertEqual(match.odds.odds_dict, {})

    def test_clear_unneeded_matches(self):
        engine = DataEngine()
        then = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
        match1 = Mock(match_info_last_updated=then, info={
            'running_time': '2h 47', 'league_name': 'A', 'home_team_name': 't1', 'away_team_name': 't2'})
        match2 = Mock(match_info_last_updated=then, info={
            'running_time': 'ht', 'league_name': 'A', 'home_team_name': 't3', 'away_team_name': 't4'})
        match3 = Mock(match_info_last_updated=then, info={
            'running_time': '1h 30', 'league_name': 'A', 'home_team_name': 't5', 'away_team_name': 't6'})
        engine.match_dict = {'001': match1, '002': match2, '003': match3}
        engine.last_clear_time = then

        engine.clear_unneeded_matches()
        expected = {'002': match2, '003': match3}
        self.assertEqual(engine.match_dict, expected)

    def test_clear_in_running_matches(self):
        engine = DataEngine()
        match1 = Mock(is_in_running=False)
        match2 = Mock(is_in_running=True)
        match3 = Mock(is_in_running=True)
        engine.match_dict = {'001': match1, '002': match2, '003': match3}

        engine.clear_in_running_matches()
        expected = {'001': match1}
        self.assertEqual(engine.match_dict, expected)

    def test_match_dict_update_scores_correctly(self):
        template = 'M1078200|396|Ger U19|\xb5\xc2U19\xc1\xaa|\xb5\xc2U19\xc2\x93|12340|Freiburg U19|\xb8\xa5\xc0\xd7\xb1\xa4U19|\xd9M\xc0\xd7\xb1\xa4U19|12203|Mainz U19|\xc3\xc0\xd2\xf0\xb4\xc4U19|\xbe\x92\xb6\xf7\xcb\xb9U19|2015-11-07 18:00:00|#9966CC|1|{}|{}|{}|1|0|0'
        scores_and_time = [
            (0, 0, '2h 20'), (0, 0, '2h 22'), (1, 0, '2h 24'), (2, 0, '2h 26'), (2, 1, '2h 28'),
            (2, 2, '2h 30'), (3, 2, '2h 32'), (3, 2, '2h 34'),
        ]

        packet_gen = ([template.format(home_score, away_score, match_time)] for home_score, away_score, match_time in scores_and_time)

        source_queue = Queue()
        use_mock_data = True
        mock_data_pkg_num_or_data_gen = None, packet_gen
        ip_and_port = '', 0
        username_password = '', ''
        save_history_flag = False
        thread_obj = VIPFeedThreadObj(source_queue, use_mock_data, mock_data_pkg_num_or_data_gen, ip_and_port,
                                      username_password, save_history_flag)
        thread_obj.start(thread_daemon=False)

        engine = DataEngine()

        for i, (home_score, away_score, match_time) in enumerate(scores_and_time):
            record_list = source_queue.get()
            if i:
                engine.update_match_dict(record_list)
            else:
                engine.init_match_dict(record_list)

            info = engine.match_dict['1078200'].info
            self.assertEqual(info['home_team_score'], home_score)
            self.assertEqual(info['away_team_score'], away_score)
            self.assertEqual(info['running_time'], match_time)
