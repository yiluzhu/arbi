import time
import datetime
from pymongo import MongoClient

MONTH = ''
client = MongoClient(serverSelectionTimeoutMS=500)
db = client['odds2016']
collection = db[MONTH]


for i in range(1, 31):
    START_DATE = datetime.date(2016, 7, i)
    END_DATE = START_DATE + datetime.timedelta(days=1)
    cursor = collection.find({'match_hk_time': {'$gt': str(START_DATE), '$lt': str(END_DATE)}})
    count = 0
    for doc in cursor:
        count += sum([len(price_dict) for price_info in doc['odds'].values() for bookies_and_prices in price_info.values() for price_dict in bookies_and_prices.values()])

    print 'Day {} odds records: {}'.format(i, count)
