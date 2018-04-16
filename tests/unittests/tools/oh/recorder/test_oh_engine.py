import datetime
from mock import patch, Mock
from unittest2 import TestCase
from arbi.models.record import YYUpdateOddsRecord, VIPUpdateOddsRecord
from arbi.tools.oh.recorder.oh_engine import OHEngine


class OHEngineTest(TestCase):

    def test_save_update_records(self):
        oh = OHEngine({'use_mock_mongodb': True})
        oh.db_engine = Mock()
        # [update_id, 'et', 'ot', 'match_id', 'bookie_id', 'bet_data', 'o1', 'o2', 'o3', 'lay_flag']
        record1 = VIPUpdateOddsRecord('123|0|5|001|69|1A!2|1.93|2.01|-6')
        record1.timestamp = ts1 = datetime.datetime(2016, 5, 16, 14, 27, 43, 987000)
        record2 = VIPUpdateOddsRecord('125|0|4|001|2|1A!3|1.95|2.00|12')
        record2.timestamp = ts2 = datetime.datetime(2016, 5, 16, 14, 27, 45, 987000)
        # ['update_id', 'lay_flag', 'et', 'ot', 'dish', 'match_id', 'bookie_id', 'bet_data', 'o1', 'o2', 'o3']
        record3 = YYUpdateOddsRecord('124|1|1|0||002|5|2B!3|3.02|3.92|3.00')
        record3.timestamp = ts3 = datetime.datetime(2016, 5, 17, 2, 47, 6, 389000)
        for record in [record1, record2, record3]:
            record.post_validation_work()
            record.produce_prices_value()

        oh.save_update_records([record1, record2, record3])

        # match_id, event_type, odds_type, handicap, bookie, timestamp_str, record.prices
        price_dict = {
            '001': [
                ('FT', 'AH', -1.5, 'pinnacle', ts1, [1.93, 2.01]),
                ('FT', 'OU', 3, 'sbobet', ts2, [1.95, 2.00]),
            ],
            '002': [('HT', '1x2', None, 'ibcbet', ts3, [3.02, 3.92, 3.0])],
        }
        oh.db_engine.save_prices.assert_called_once_with(price_dict)
