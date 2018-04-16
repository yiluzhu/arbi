import time
import datetime
import logging


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class PriceSensor(object):
    """This is able to sense events like: price increased/decreased X points in Y seconds"""

    @staticmethod
    def validate_ts_and_prices(ts_str, ts_and_prices, time_period, scores_ts):
        if len(ts_str) == 12:  # the length should be 19, e.g. 2016-07-01 03:41:24
            # We consistently receive invalid timestamp like  2016-07-01 0
            return

        ts_epoch, prices = ts_and_prices
        if any([price == 0 or price >= 3 for price in prices]) or any([abs(ts_epoch - ts) < time_period for ts in scores_ts]):
            return

        return ts_epoch, prices

    def find(self, price_ts_list, price_vol, time_period, scores_ts):
        """Find the situations where price movement is larger than the threshold in give time period
        """
        res = []
        window = []  # latest first, like tsn, tsn-1, ..., t0

        for ts_str, ts_and_prices in price_ts_list:
            ts_and_prices = self.validate_ts_and_prices(ts_str, ts_and_prices, time_period, scores_ts)

            if ts_and_prices:
                ts_epoch, prices = ts_and_prices
            else:
                continue

            if window:
                # Find the index of the timestamp from where its distance to current timestamp is within time frame
                index = None
                for i, (ts_in_window, price) in enumerate(window):
                    if ts_epoch - ts_in_window <= time_period:
                        index = i
                        break

                if index is None:
                    window = []
                elif index:
                    del window[:index]
                # else:  # index == 0
                #     pass

                if window:
                    ts0, price0 = window[0]
                    price_movement = round(abs(prices[0] - price0), 3)
                    if price_movement >= price_vol:
                        duration = ts_epoch - ts0
                        ts0_str = str(datetime.datetime.utcfromtimestamp(ts0))
                        res.append([duration, price_movement, ts0_str, ts_str, price0, prices[0]])

            window.append((ts_epoch, prices[0]))

        return res

    def find_all_situations(self, cursor, price_vol, time_period_in_seconds):
        total_res = []
        t0 = time.time()
        for doc in cursor:
            # the format of doc is defined in db_engine.initialize_one_doc()
            match_id = doc['_id']
            league = doc['league']
            home_team = doc['home']
            away_team = doc['away']
            match_hk_time = doc['match_hk_time']
            odds = doc['odds']
            if 'home_score_ts' in doc and 'home_score_ts' in doc:
                scores_ts = [ts for ts_str, ts in doc['home_score_ts'] + doc['away_score_ts']]
            else:
                scores_ts = []

            for bet_type, price_info in odds.iteritems():
                event_type, odds_type = bet_type.split('_')
                for sub_type, bookies_and_prices in price_info.iteritems():
                    for bookie, price_ts_dict in bookies_and_prices.iteritems():
                        price_ts_list = sorted(price_ts_dict.items())
                        res = self.find(price_ts_list, price_vol, time_period_in_seconds, scores_ts)
                        for row in res:
                            total_res.append([match_id, league, home_team, away_team, match_hk_time, event_type, odds_type, sub_type, bookie] + row)
        log.info('Found {} rows of results in {} seconds'.format(len(total_res), time.time() - t0))
        return total_res


HEADERS = ['Match ID', 'League', 'Home Team', 'Away Team', 'Kick off Time', 'F/HT',
           'Odds Type', 'Sub Type', 'Bookie', 'In Seconds', 'Vol', 'From Time', 'To Time', 'From Price', 'To Price']
