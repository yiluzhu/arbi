"""
The timestamp for each odds at the moment (2016.10.16) is like:
    "2016-09-09 12:28:56": [2.02, 1.98]
We want to convert it to new format which is like:
    "2016-09-09 12:28:56": [123456.789, [2.02, 1.98]]
where 123456.789 is the epoch time of "2016-09-09 12:28:56"

Be aware that keys can't be tuple or int or float, only string. Otherwise you get this error:
    bson.errors.InvalidDocument: documents must have only string keys
"""
import time
import datetime
from pymongo import MongoClient


client = MongoClient(serverSelectionTimeoutMS=500)
db = client['odds2016']
epoch = datetime.datetime(1970, 1, 1)
t0 = time.time()
count = 0
for mon in ['aug']:
    collection = db[mon]
    cursor = list(collection.find({}))
    for doc in cursor:
        match_id = doc['_id']
        odds = doc['odds']
        for bet_type, price_info in odds.iteritems():
            for sub_type, bookies_and_prices in price_info.iteritems():
                for bookie, price_dict in bookies_and_prices.iteritems():
                    for ts_str, price_list in price_dict.iteritems():
                        if len(ts_str) == 12:
                            continue
                        if isinstance(price_list[1], list):
                            continue
                        try:
                            ts = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                        except Exception as e:
                            print '--1--', match_id, ts_str
                            print e
                            continue
                        tseconds = (ts - epoch).total_seconds()
                        query = 'odds.{}.{}.{}.{}'.format(bet_type, sub_type, bookie, ts_str)
                        collection.find_one_and_update({'_id': match_id}, {'$set': {query: [tseconds, price_list]}})
                        count += 1

print 'It took {} seconds to update {} odds records'.format(time.time() - t0, count)
