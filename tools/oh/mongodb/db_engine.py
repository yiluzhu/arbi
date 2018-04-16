import mock
import time
import logging
import datetime

from pymongo import MongoClient, errors


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class DBEngine(object):
    def __init__(self, use_mock_db=False):
        self.client = mock.MagicMock() if use_mock_db else MongoClient(serverSelectionTimeoutMS=500)
        log.info(self.client.server_info())

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        now_year = str(now.year)
        now_month = str(now.strftime("%B").lower()[:3])
        self.db = self.client['odds' + now_year]
        self.collection = self.db[now_month]
        self.matches_with_too_many_odds = []

    def select_month(self, month):
        self.collection = self.db[month]

    def retrieve_one_doc(self, match_id):
        return self.collection.find_one({'id': match_id})

    def insert_one_doc(self, doc):
        self.collection.insert_one(doc)

    @staticmethod
    def initialize_one_doc(match_info_dict):
        # We assume we always run this function before the match kicks off, therefore the scores are always 0:0
        doc = {
            '_id': match_info_dict['match_id'],
            'league': match_info_dict['league_name'],
            'home': match_info_dict['home_team_name'],
            'away': match_info_dict['away_team_name'],
            'match_hk_time': match_info_dict['match_hk_time'],
            'home_score_ts': [],
            'home_red_card_ts': [],
            'away_score_ts': [],
            'away_red_card_ts': [],
            'odds': {},
        }
        return doc

    def save_prices(self, price_dict):
        for match_id, prices in price_dict.iteritems():
            if match_id in self.matches_with_too_many_odds:
                continue

            update = {}
            for event_type, odds_type, handicap, bookie, timestamp, price in prices:
                ts_str = str(timestamp)
                if len(ts_str) == 12:
                    continue

                level1 = '{}_{}'.format(event_type, odds_type)
                level2 = str(handicap).replace('.', '_')
                epoch_seconds = (timestamp - datetime.datetime(1970, 1, 1)).total_seconds()

                # cut off milliseconds from timestamp as the key should not contain dot which is used as separator in mongodb
                update['odds.{}.{}.{}.{}'.format(level1, level2, bookie, ts_str[:-7])] = [epoch_seconds, price]

            try:
                self.collection.find_one_and_update({'_id': match_id}, {'$set': update})
            except errors.OperationFailure as e:  # Resulting document after update is larger than 16777216
                log.warning('Failed to update odds for match %s, details: %s', match_id, e.details)
                self.matches_with_too_many_odds.append(match_id)

    def save_new_match(self, match_info_dict):
        match_id = match_info_dict['match_id']
        if not self.collection.find_one({'_id': match_id}):
            doc = self.initialize_one_doc(match_info_dict)
            self.collection.insert_one(doc)

    def save_events(self, match_id, event_names):
        ts_str = str(datetime.datetime.utcnow() + datetime.timedelta(hours=8))
        ts = time.time()
        for event_name in event_names:
            assert event_name.startswith(('home scores', 'away scores'))
            goals = event_name[-1]
            side = event_name[:4]
            for _ in range(int(goals)):
                update = {
                    '$push': {
                        '{}_score_ts'.format(side): [ts_str, ts]
                    }
                }
                self.collection.find_one_and_update({'_id': match_id}, update)

    def get_data_in_date_range(self, start_date, end_date):
        t0 = time.time()
        cursor = self.collection.find({'match_hk_time': {'$gt': start_date, '$lt': end_date}})
        log.info('Found {} docs in DB in {} seconds'.format(cursor.count(), time.time() - t0))
        return cursor

    def __del__(self):
        try:
            self.client.close()
        except:
            pass
