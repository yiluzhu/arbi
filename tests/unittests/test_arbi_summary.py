import os
import time
import datetime
import StringIO
from mock import patch, call, ANY
from unittest2 import TestCase, main
from arbi.arbi_summary import ArbiSummaryTableModel, ArbiSummaryLogger
from arbi.models.opportunity import ArbiOpportunity
from arbi.constants import ROOT_PATH


class SummaryTableModelTest(TestCase):
    def test(self):
        table_model = ArbiSummaryTableModel([], ['a'])


class SummaryLoggerTest(TestCase):
    # def test(self):
    #     test_path = os.path.join(ROOT_PATH, 'tests', 'test_arbi_opps_folder')
    #     file_obj = StringIO.StringIO()
    #     logger = ArbiSummaryLogger(test_path, file_obj)
    #
    #     occur_at_utc = datetime.datetime.strptime('20150504 18:05:09', '%Y%m%d %H:%M:%S')
    #
    #     opp1 = ArbiOpportunity({'league_name': u'Ukraine U21', 'league_name_simp': u'\u4e4cU21',
    #                             'home_team_name': u'Donetsk U21', 'home_team_name_simp': u'\u5f53\u5c3c\u65af\u514bU21', 'home_team_score': u'1',
    #                             'away_team_score': u'0', 'away_team_name':u'Olimpik.D U21', 'away_team_name_simp': u'\u5965\u6797\u5339\u514b\u987f\u6d85\u8328\u514bU21'},
    #                             occur_at_utc, '1', (0.02, (('AH Home', 0.5, 'FT', '2', 65.272, 1.66, 'a!A', False), ('AH Away', -0.5, 'FT', '5', 34.728, 3.12, 'b!B', False))))
    #
    #     opp2 = ArbiOpportunity({'league_name': u'ATVL', 'league_name_simp': u'ATVL',
    #                             'home_team_name': u'Tilford Zebras', 'home_team_name_simp': u'Tilford Zebras', 'home_team_score': u'4',
    #                             'away_team_score': u'0', 'away_team_name':u'Glenorchy Knights', 'away_team_name_simp': u'Glenorchy Knights'},
    #                             occur_at_utc, '1', (0.03, (('OU Over', 5.5, 'FT', '2', 55.2, 2.29, 'a!A', False), ('OU Under', 5.5, 'FT', '5', 44.8, 1.90, 'b!B', False))))
    #
    #     logger.save([opp1, opp2])
    #     file_obj.flush()
    #     print file_obj.read()

    def test(self):
        test_path = os.path.join(ROOT_PATH, 'tests', 'test_arbi_opps_folder')
        file_obj = StringIO.StringIO()
        logger = ArbiSummaryLogger(test_path, file_obj)

        arbi_summary_list = [
            [[False, 1, '8.438 %',  '20150504 18:05:09', 0.006, u'Ukraine U21', u'Ukraine U21', u'Donetsk U21', u'Donetsk U21', u'5', u'0', u'Olimpik.D U21', u'Olimpik.D U21', 'OU', 5.5, 'FT', 'crown_d', u'crown_d', 65.272, 1.66, '0 %', 'pinnacle', u'pinnacle', 34.728, 3.12, '0.25 %']],
            [[False, 2, '13.153 %', '20150504 18:05:09', 0.006, u'Ukraine U21', u'Ukraine U21', u'Donetsk U21', u'Donetsk U21', u'5', u'0', u'Olimpik.D U21', u'Olimpik.D U21', 'OU', 5.75, 'FT', 'ssbet', 'ssbet', 56.522, 2.0, '0 %', 'pinnacle', u'pinnacle', 43.478, 2.6, '0.25 %']],
            [[False, 3, '1.018 %',  '20150504 18:05:09', 0.006, u'Ukraine U21', u'Ukraine U21', u'Donetsk U21', u'Donetsk U21', u'5', u'0', u'Olimpik.D U21', u'Olimpik.D U21', 'AH', -0.5, 'FT', 'sin88', 'sin88', 56.691, 1.78, '0 %', 'pinnacle', u'pinnacle', 43.309, 2.33, '0.25 %']],
            [[False, 4, '3.634 %',  '20150504 18:05:09', 0.005, u'ATVL', u'ATVL', u'Tilford Zebras', u'Tilford Zebras', u'4', u'0', u'Glenorchy Knights', u'Glenorchy Knights', 'OU', 4.5, 'FT', 'isn', u'isn', 45.255, 2.29, '0 %', 'ssbet', 'ssbet', 54.745, 1.893, '0 %']],
        ]
        with patch('arbi.arbi_summary.log') as mock_log:
            results = [logger.save(arbi_summary) for arbi_summary in arbi_summary_list]

        calls = [
            call('Found 1 new opportunities in tc tool.'),
            call('Found arb: False,1,8.438 %,20150504 18:05:09,0.006,Ukraine U21,Ukraine U21,Donetsk U21,Donetsk U21,5,0,Olimpik.D U21,Olimpik.D U21,OU,5.5,FT,crown_d,crown_d,65.272,1.66,0 %,pinnacle,pinnacle,34.728,3.12,0.25 %'),
            call('Found 1 new opportunities in tc tool.'),
            call('Found arb: False,2,13.153 %,20150504 18:05:09,0.006,Ukraine U21,Ukraine U21,Donetsk U21,Donetsk U21,5,0,Olimpik.D U21,Olimpik.D U21,OU,5.75,FT,ssbet,ssbet,56.522,2.0,0 %,pinnacle,pinnacle,43.478,2.6,0.25 %'),
            call('Found 1 new opportunities in tc tool.'),
            call('Found arb: False,3,1.018 %,20150504 18:05:09,0.006,Ukraine U21,Ukraine U21,Donetsk U21,Donetsk U21,5,0,Olimpik.D U21,Olimpik.D U21,AH,-0.5,FT,sin88,sin88,56.691,1.78,0 %,pinnacle,pinnacle,43.309,2.33,0.25 %'),
        ]
        mock_log.info.assert_has_calls(calls)

        expected = [
            None,
            [[False, 1, '8.438 %',  '20150504 18:05:09', 0.006, u'Ukraine U21', u'Ukraine U21', u'Donetsk U21', u'Donetsk U21', u'5', u'0', u'Olimpik.D U21', u'Olimpik.D U21', 'OU', 5.5, 'FT', 'crown_d', u'crown_d', 65.272, 1.66, '0 %', 'pinnacle', u'pinnacle', 34.728, 3.12, '0.25 %']],
            [[False, 2, '13.153 %', '20150504 18:05:09', 0.006, u'Ukraine U21', u'Ukraine U21', u'Donetsk U21', u'Donetsk U21', u'5', u'0', u'Olimpik.D U21', u'Olimpik.D U21', 'OU', 5.75, 'FT', 'ssbet', 'ssbet', 56.522, 2.0, '0 %', 'pinnacle', u'pinnacle', 43.478, 2.6, '0.25 %']],
            [[False, 3, '1.018 %',  '20150504 18:05:09', 0.006, u'Ukraine U21', u'Ukraine U21', u'Donetsk U21', u'Donetsk U21', u'5', u'0', u'Olimpik.D U21', u'Olimpik.D U21', 'AH', -0.5, 'FT', 'sin88', 'sin88', 56.691, 1.78, '0 %', 'pinnacle', u'pinnacle', 43.309, 2.33, '0.25 %']],
        ]

        self.assertEqual(results, expected)

    def test_filter_out_saved_opps_no_filter(self):
        ArbiSummaryLogger.create_storage_file = lambda *args: None
        logger = ArbiSummaryLogger('')
        disappeared_opps_pairs = [('part opp1', 'full opp1'), ('part opp2', 'full opp2')]
        result = logger.filter_out_saved_opps(disappeared_opps_pairs)

        self.assertEqual(result, ['full opp1', 'full opp2'])
        self.assertEqual(logger.historic_arbi_opp_filter_dict, {'last cleaned': ANY, 'part opp1': ANY, 'part opp2': ANY})

    def test_filter_out_saved_opps_filter1(self):
        ArbiSummaryLogger.create_storage_file = lambda *args: None
        logger = ArbiSummaryLogger('')
        logger.historic_arbi_opp_filter_dict.update({'part opp1': time.time()})
        disappeared_opps_pairs = [('part opp1', 'full opp1'), ('part opp2', 'full opp2')]
        result = logger.filter_out_saved_opps(disappeared_opps_pairs)

        self.assertEqual(result, ['full opp2'])
        self.assertEqual(logger.historic_arbi_opp_filter_dict, {'last cleaned': ANY, 'part opp1': ANY, 'part opp2': ANY})

    def test_filter_out_saved_opps_filter2(self):
        ArbiSummaryLogger.create_storage_file = lambda *args: None
        logger = ArbiSummaryLogger('')
        logger.historic_arbi_opp_filter_dict.update({'part opp1': time.time(), 'part opp2': time.time()})
        disappeared_opps_pairs = [('part opp1', 'full opp1'), ('part opp2', 'full opp2')]
        result = logger.filter_out_saved_opps(disappeared_opps_pairs)

        self.assertEqual(result, [])
        self.assertEqual(logger.historic_arbi_opp_filter_dict, {'last cleaned': ANY, 'part opp1': ANY, 'part opp2': ANY})

    def test_filter_out_saved_opps_filter_clean(self):
        ArbiSummaryLogger.create_storage_file = lambda *args: None
        logger = ArbiSummaryLogger('')
        logger.historic_arbi_opp_filter_dict.update({'part opp1': time.time() - 60 * 60 * 24})
        disappeared_opps_pairs = [('part opp1', 'full opp1'), ('part opp2', 'full opp2')]
        result = logger.filter_out_saved_opps(disappeared_opps_pairs)

        self.assertEqual(result, ['full opp1', 'full opp2'])
        self.assertEqual(logger.historic_arbi_opp_filter_dict, {'last cleaned': ANY, 'part opp1': ANY, 'part opp2': ANY})



