import time
import logging
from arbi.feeds.base_feed import BaseFeed, BaseFeedThreadObj, FeedConnectionError
from arbi.feeds.betfair.constants import BET_API_VERSION
from arbi.models.record import YYUpdateOddsRecord, IncorrectLengthRecord
from arbi.utils import gzip_string, create_packet_header


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class BetfairFeed(BaseFeed):
    FEED_NAME = 'Betfair'

    def get_login_string(self, username, password):
        msg = 'DL^{0}^{1}^{2}'.format(BET_API_VERSION, username, password)
        zmsg = gzip_string(msg)
        return self.create_packet(zmsg)

    def create_packet(self, stream):
        size = len(stream)
        head = create_packet_header(size)
        return head + stream + '[END]'

    def login_succeeded(self, login_result):
        return len(login_result) == 1 and login_result[0].lower() == 'true'


class BetfairFeedThreadObj(BaseFeedThreadObj):
    FEED_NAME = 'Betfair'
    FEED_CLASS = BetfairFeed

    def run_loop(self):
        while not self.queue.has_put_init_dict_in:
            time.sleep(1)

        while not self.stop_event.is_set():
            try:
                packet = self.data_feed.get_one_packet()
            except StopIteration:
                log.info('stop iteration.')
                break
            except FeedConnectionError:
                break

            if self.save_history_flag:
                self.save_history(packet)

            record_list = self.get_record_list_from_packet(packet)
            if record_list:
                self.queue.put(record_list)

    def get_records(self, packet):
         for record_str in packet:
            try:
                record = YYUpdateOddsRecord(record_str)
            except IncorrectLengthRecord as e:
                log.error('Record has incorrect length: {}'.format(e))
            else:
                if record.is_valid():
                    record.post_validation_work()
                    yield record
