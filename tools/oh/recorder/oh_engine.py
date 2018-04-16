import time
import datetime
import logging
import cProfile
import StringIO
import pstats
from Queue import Queue

from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError

from arbi.feeds.vip.networking import VIPFeedThreadObj
from arbi.feeds.vip.constants import OH_TOOL_ACCOUNT, HOSTS, PORTS
from arbi.feeds.betfair.feed import BetfairFeedThreadObj
from arbi.feeds.betfair.constants import BETFAIR_FEED_PORT, BETFAIR_FEED_IP

from arbi.constants import VIP_ALL_BOOKIES_ID_MAP
from arbi.utils import get_memory_usage
from arbi.models.record import MatchInfoRecord, VIPUpdateOddsRecord, YYUpdateOddsRecord
from arbi.tools.oh.mongodb.db_engine import DBEngine
from arbi.tools.oh.constants import YY_PASSWORD_OH, YY_USERNAME_OH, MAX_SOURCE_QUEUE_SIZE, SOURCE_QUEUE_CLEARANCE_SIZE, SAVE_RECORDS_MAX_NUM


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

THREAD_ALIVE_CHECK_INTERVAL = 20
RECONNECT_DELAY = 20


class OHEngine(object):
    def __init__(self, settings):
        use_mock_db = settings.get('use_mock_mongodb', False)
        try:
            self.db_engine = DBEngine(use_mock_db)
        except ServerSelectionTimeoutError as e:
            log.error('Mongo DB server not available: {}'.format(e))
            self.mongo_server_running = False
            return
        else:
            log.info('Successfully connect to Mongo DB server!')
            self.mongo_server_running = True

        self.settings = settings
        self.source_queue = Queue()
        self.source_queue.has_put_init_dict_in = False

        self.vip_feed_thread = None
        self.yy_feed_thread = None
        self.break_loop_count = 0
        self.match_event_dict = {}  # {'001': {'home_red_card': 0: 'away_red_card': 0, 'home_score': 0, 'away_score': 0}}
        self.threads_alive_last_checked = 0

    def run(self):
        if not self.mongo_server_running:
            return

        start_time = time.time()
        self.run_vip_feed_thread()
        if not self.settings.get('disable_yy_feed'):
            self.run_yy_feed_thread()

        self.threads_alive_last_checked = time.time()
        init_dict = self.get_initial_match_dict()
        self.process_initial_match_dict(init_dict)

        queue_empty_count = 0
        pkg_count = 0
        logging_ts1 = time.time()
        logging_ts2 = time.time()

        # pr = cProfile.Profile()
        # s = StringIO.StringIO()
        # pr.enable()

        while True:
            self.check_threads_alive()

            if self.source_queue.empty():
                queue_empty_count += 1
                if queue_empty_count % 50 == 0:
                    log.info('Queue empty count: {}'.format(queue_empty_count))
                if self.break_loop_count and queue_empty_count >= self.break_loop_count:
                    log.info('Break Loop Count {} reached. Exit!'.format(self.break_loop_count))
                    break
                time.sleep(0.5)
            else:
                if self.source_queue.qsize() > MAX_SOURCE_QUEUE_SIZE:
                    self.clear_source_queue_partially(SOURCE_QUEUE_CLEARANCE_SIZE)
                record_list = []
                while not self.source_queue.empty():
                    lst = self.source_queue.get()
                    if isinstance(lst, dict):
                        # If vip feed failed it will automatically reconnect and re-send the init_dict.  We ignore the init_dict here.
                        continue
                    record_list += lst
                    pkg_count += 1
                    if len(record_list) > SAVE_RECORDS_MAX_NUM:
                        # Sometimes the queue always has data and we need to break the loop. Otherwise it would continue appending data and hit memory error
                        break

                if record_list:
                    self.save_update_records(record_list)
                t = time.time()
                if t - logging_ts1 > 300:  # 5 mins
                    log.info('packet count: %s, source queue size: %s, memory used: %s MB', pkg_count, self.source_queue.qsize(), get_memory_usage())
                    logging_ts1 = t
                if t - logging_ts2 > 1800:  # 30 mins
                    log.info('OH tool recorder has been running for %s', datetime.timedelta(seconds=int(t - start_time)))
                    logging_ts2 = t

        # pr.disable()
        # ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        # ps.print_stats()
        # print s.getvalue()

        log.info('Total packet count: %s, queue empty count: %s, run time: %s, source queue size: %s.',
            pkg_count, queue_empty_count, str(datetime.timedelta(seconds=int(time.time() - start_time))), self.source_queue.qsize())

    def clear_source_queue_partially(self, size):
        log.warning('Source queue size hit %s, memory used: %s MB', self.source_queue.qsize(), get_memory_usage())
        for i in xrange(size):
            self.source_queue.get()
        log.warning('Removed %s items from source queue, memory used: %s MB', size, get_memory_usage())

    def process_initial_match_dict(self, init_dict):
        docs = [self.db_engine.initialize_one_doc(match.info) for match_id, match in init_dict.iteritems()]
        log.info('Insert match information for each match...')
        insert_initial_match_info_succeeded_count = 0
        insert_initial_match_info_failed_count = 0
        for doc in docs:
            try:
                self.db_engine.insert_one_doc(doc)
            except DuplicateKeyError:
                insert_initial_match_info_failed_count += 1
            else:
                insert_initial_match_info_succeeded_count += 1
                self.match_event_dict[doc['_id']] = {'home_score': 0, 'away_score': 0}  # we could have home_red_card and away_red_card in the future

        log.info('Successfully inserting match info for {} matches, failed {} matches.'.format(
            insert_initial_match_info_succeeded_count, insert_initial_match_info_failed_count))

    def get_initial_match_dict(self):
        while True:
            if self.source_queue.empty():
                time.sleep(0.5)
            else:
                init_dict = self.source_queue.get()
                return init_dict
            self.check_threads_alive()

    def save_update_records(self, record_list):
        """Take a list of records and save them to database.

        :param record_list: a list of record objects
        """
        price_dict = {}
        for record in record_list:
            match_id = record.record_dict['match_id']
            if isinstance(record, (VIPUpdateOddsRecord, YYUpdateOddsRecord)):
                bookie_id = record.record_dict['bookie_id']
                bookie = VIP_ALL_BOOKIES_ID_MAP.get(bookie_id)
                if bookie:
                    event_type = record.record_dict['event_type']
                    odds_type = record.record_dict['odds_type']
                    handicap = record.record_dict['dish']

                    if match_id in price_dict:
                        price_dict[match_id].append((event_type, odds_type, handicap, bookie, record.timestamp, record.prices))
                    else:
                        price_dict[match_id] = [(event_type, odds_type, handicap, bookie, record.timestamp, record.prices)]

            elif isinstance(record, MatchInfoRecord):
                self.db_engine.save_new_match(record.record_dict)
                event_names = self.get_event_names(record.record_dict)
                if event_names:
                    self.db_engine.save_events(match_id, event_names)

        self.db_engine.save_prices(price_dict)

    def get_event_names(self, match_record_dict):
        event_names = []
        new_home_score = match_record_dict['home_team_score']
        new_away_score = match_record_dict['away_team_score']
        if match_record_dict['match_id'] in self.match_event_dict:
            event_info = self.match_event_dict[match_record_dict['match_id']]
            if event_info['home_score'] < new_home_score:
                # It should always score one goal but in case we missed one update, we record how many goals have been updated
                event_names.append('home scores {}'.format(new_home_score - event_info['home_score']))
                event_info['home_score'] = new_home_score
            if event_info['away_score'] < new_away_score:
                event_names.append('away scores {}'.format(new_away_score - event_info['away_score']))
                event_info['away_score'] = new_away_score

        return event_names

    def run_vip_feed_thread(self):
        self.vip_feed_thread = VIPFeedThreadObj(self.source_queue,
                                                self.settings.get('use_vip_mock_data', False),
                                                ('packets2000with_timestamp_100ms', None),
                                                (HOSTS[0], PORTS[0]),
                                                OH_TOOL_ACCOUNT,
                                                False,
                                                )
        self.vip_feed_thread.start()

    def run_yy_feed_thread(self):
        self.yy_feed_thread = BetfairFeedThreadObj(self.source_queue,
                                                   self.settings.get('use_yy_mock_data', False),
                                                   ('packets2000with_timestamp_100ms', None),
                                                   (BETFAIR_FEED_IP, BETFAIR_FEED_PORT),
                                                   (YY_USERNAME_OH, YY_PASSWORD_OH),
                                                   False,
                                                   )
        self.yy_feed_thread.start()

    def check_threads_alive(self):
        t = time.time()
        if t - self.threads_alive_last_checked > THREAD_ALIVE_CHECK_INTERVAL:
            self.threads_alive_last_checked = t
            if self.vip_feed_thread and not self.vip_feed_thread.thread.is_alive():
                self.vip_feed_thread.start(delay=RECONNECT_DELAY)
            if not self.settings.get('disable_yy_feed') and self.yy_feed_thread and not self.yy_feed_thread.thread.is_alive():
                self.yy_feed_thread.start(delay=RECONNECT_DELAY)
