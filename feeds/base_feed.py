import os
import socket
import time
import logging
import datetime
from threading import Thread, Event

from arbi.constants import ROOT_PATH
from arbi.feeds.vip.constants import TIME_THRESHOLD_TO_GET_ONE_PACKET, READ_BLOCK_SIZE
from arbi.utils import unzip_string, get_body_size


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


MOCK_DATA_PATH = os.path.join(ROOT_PATH, 'mock_data', '{}', '{}.txt')


class FeedConnectionError(Exception):
    """Raise this error when we want to reconnect"""


class BaseFeedThreadObj(object):
    TT_SIGNAL = 'Terminate Thread'
    FEED_NAME = None
    FEED_CLASS = None

    def __init__(self, queue, use_mock_data, mock_data_pkg_num_and_data_gen_and_time, host_port, username_password,
                 save_history_flag):
        self.queue = queue
        self.create_data_feed_args = (use_mock_data, mock_data_pkg_num_and_data_gen_and_time, host_port, username_password)
        self.data_feed = None
        self.thread = None
        self.stop_event = Event()
        self.save_history_flag = save_history_flag
        self.history_file = None

    def create_data_feed(self):
        use_mock_data, mock_data_pkg_num_and_data_gen, host_port, username_password = self.create_data_feed_args
        if use_mock_data:
            mock_data_pkg_num, data_gen = mock_data_pkg_num_and_data_gen
            data_feed = MockFeed(mock_data_pkg_num, data_gen, self.FEED_NAME.lower())

            username_password = '', ''
        else:
            try:
                data_feed = self.FEED_CLASS(*host_port)
            except socket.error as e:
                log.error('Cannot connect to {} data feed({}): {}'.format(host_port, self.FEED_NAME, e))
                return

        if data_feed.login(*username_password):
            return data_feed

    def start(self, delay=0, thread_daemon=True):
        """To create the thread here rather than sub class Thread allows us to restart thread without create new instance
        """
        self.stop_event.clear()
        self.thread = Thread(target=self.run)
        self.thread.daemon = thread_daemon
        self.delay = delay
        self.thread.start()

    def run_pre_loop(self):
        if self.delay:
            log.error('*** Lost connection to {} server. Reconnect in {} seconds. ***'.format(
                self.FEED_NAME, self.delay))
            time.sleep(self.delay)
            if self.stop_event.is_set():
                return self.TT_SIGNAL
            log.error('*** Reconnecting... ***')

        log.info('{} feed (thread id {}) starts.'.format(self.FEED_NAME, self.thread.ident))

        if self.save_history_flag:
            self.prepare_history_file()

        try:
            self.data_feed = self.create_data_feed()
        except FeedConnectionError:
            return self.TT_SIGNAL

        if not self.data_feed:
            log.warning('*** {} feed does not exist. Thread (id {}) is finished ***'.format(
                self.FEED_NAME, self.thread.ident))
            return self.TT_SIGNAL

    def run_loop(self):
        raise NotImplementedError

    def run_post_loop(self):
        if self.save_history_flag:
            self.close_history_file()

        log.info('{} feed (thread id {}) is finished.'.format(self.FEED_NAME, self.thread.ident))

    def run(self):
        signal = self.run_pre_loop()
        if signal == self.TT_SIGNAL:
            log.error('Error in pre loop for {}. Terminate thread.'.format(self.FEED_NAME))
            return
        self.run_loop()
        self.run_post_loop()

    def get_record_list_from_packet(self, packet):
        """Return a list of record objects"""
        assert isinstance(packet, list), 'Expected type: list, got type: {}'.format(type(packet))
        return list(self.get_records(packet))

    def get_records(self, packet):
        raise NotImplementedError

    def prepare_history_file(self):
        name = str(datetime.datetime.utcnow() + datetime.timedelta(hours=8)).replace(':', '').split('.')[0] + ' timestamp'
        dirname = 'history/' + self.FEED_NAME.lower()
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        self.history_file = open('{}/{}.txt'.format(dirname, name), 'w')

    def close_history_file(self):
        try:
            self.history_file.close()
        except:
            pass

    def save_history(self, packet):
        timestamp = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        self.history_file.write(str(timestamp) + '  ' + str(packet) + '\n')

    def __del__(self):
        self.close_history_file()


class BaseFeed(object):
    FEED_NAME = None

    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.rfile = self.socket.makefile('rb', -1)
        self.wfile = self.socket.makefile('wb', 0)

    def login(self, username, password):
        login_result = self._login(username, password)
        if self.login_succeeded(login_result):
            log.info('Successfully login to {} data feed: {}'.format(self.FEED_NAME, login_result))
            return True
        else:
            log.critical('Failed to login to {} data feed: {}'.format(self.FEED_NAME, login_result))
            return False

    def _login(self, username, password):
        login_string = self.get_login_string(username, password)
        self.wfile.write(login_string)
        return self.read_data()

    def get_login_string(self, username, password):
        raise NotImplementedError

    def login_succeeded(self, login_result):
        raise NotImplementedError

    def get_one_packet(self):
        t0 = time.time()
        packet = self.read_data()

        elapsed = time.time() - t0
        if elapsed > TIME_THRESHOLD_TO_GET_ONE_PACKET:
            log.info('It took {0} seconds to read {1} records'.format(elapsed, len(packet)))

        return packet

    def logout(self):
        self.rfile.close()
        self.wfile.close()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def read_data(self):
        try:
            head = self.rfile.read(4)
        except (socket.error, socket.timeout) as e:
            log.error('Failed to get data from {} feed: {}'.format(self.FEED_NAME, e))
            raise FeedConnectionError

        try:
            size = get_body_size(head)
        except Exception as e:
            log.error('Error in decoding packet header: {0}'.format(e))
            raise FeedConnectionError

        if size > 0:
            zdata = ''
            try:
                while size > READ_BLOCK_SIZE:  # could hit OverflowError if read all data in one go by f.read(size)
                    zdata += self.rfile.read(READ_BLOCK_SIZE)
                    size -= READ_BLOCK_SIZE
                else:
                    zdata += self.rfile.read(size)
            except (socket.error, socket.timeout) as e:
                udata = None
                log.error('Error when read {} data feed body: {}'.format(self.FEED_NAME, e))
            else:
                udata = unzip_string(zdata)

            if udata is None:
                log.error('Error when unzip {} data.'.format(self.FEED_NAME))
                raise FeedConnectionError
            else:
                data = udata.strip().split("\n")
        else:
            data = []

        return data


class MockFeed(object):
    def __init__(self, data_size_name, data_packet_gen, feed_name):
        self.sleep_before_read_flag = False

        if data_size_name:
            if 'timestamp' in data_size_name:
                path = MOCK_DATA_PATH.format(feed_name, data_size_name)
                self.sleep_before_read_flag = True
                self.data_gen = self.get_data_gen_with_timestamp(path)
            else:
                data_size_name = 'packets' + data_size_name
                with open(MOCK_DATA_PATH.format(feed_name, data_size_name)) as f:
                    self.data_gen = (eval(line) for line in f.readlines())
            log.info('Use mock data for {} from file "{}"'.format(feed_name, data_size_name))
        elif data_packet_gen:
            self.data_gen = data_packet_gen
            log.info('Use injected mock data generator for {}'.format(feed_name))
        else:
            self.data_gen = None

    def get_data_gen_with_timestamp(self, path):
        previous_timestamp = None
        with open(path) as f:
            for line in f.readlines():
                timestamp_str, packet_str = line.split('  ', 1)
                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                packet = eval(packet_str)
                sleep_time = (timestamp - previous_timestamp).total_seconds() if previous_timestamp else 0
                previous_timestamp = timestamp
                yield sleep_time, packet

    def login(self, username, password):
        return True

    def logout(self):
        pass

    def get_one_packet(self):
        val = next(self.data_gen)
        if self.sleep_before_read_flag:
            time.sleep(val[0])
            return val[1]
        else:
            return val
