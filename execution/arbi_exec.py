import time
import socket
import logging
import datetime
from threading import Thread, Event
from arbi.utils import gzip_string, unzip_string, get_body_size, get_hk_time_now, create_packet_header, merge_dict
from arbi.constants import VERSION, BOOKIE_IDS_WITH_LAY_PRICES
from arbi.feeds.betfair.constants import BETFAIR_USERNAME, BETFAIR_PASSWORD
from arbi.execution.constants import (EXEC_HOST, EXEC_PORT, EXEC_READ_BLOCK_SIZE, BET_API_VERSION)


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class ExecMsgerConnectionError(Exception):
    """When this error happens, we reconnect"""


class ArbiExecMsgerThreadObj(object):
    def __init__(self, exec_msg_queue, send_orders_flag, exec_system_on_localhost_flag):
        self.create_exec_messenger_args = (send_orders_flag, exec_system_on_localhost_flag)
        self.exec_msg_queue = exec_msg_queue
        self.thread = None
        self.stop_event = Event()
        self.exec_messenger = None

    def create_exec_messenger(self, send_orders_flag, exec_system_on_localhost_flag):
        if send_orders_flag:
            host = '127.0.0.1' if exec_system_on_localhost_flag else EXEC_HOST
            try:
                exec_messenger = ArbiExecMessenger(host, EXEC_PORT)
            except socket.error as e:
                log.error('Cannot connect to execution system: {0}'.format(e))
                return
        else:
            exec_messenger = MockMessenger(None, None)

        return exec_messenger

    def start(self):
        self.stop_event.clear()
        self.thread = Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        log.info('Execution system messenger (thread id {}) starts.'.format(self.thread.ident))

        self.exec_messenger = self.create_exec_messenger(*self.create_exec_messenger_args)
        if not self.exec_messenger:
            log.info('Execution system messenger (thread id {}) is finished.'.format(self.thread.ident))
            return
        if not self.exec_messenger.login(BETFAIR_USERNAME, BETFAIR_PASSWORD, VERSION):
            log.info('Execution system messenger (thread id {}) is finished.'.format(self.thread.ident))
            return

        while not self.stop_event.is_set():
            try:
                bookie_id_and_status = self.exec_messenger.process_exec_msg()
            except ExecMsgerConnectionError:
                self.exec_msg_queue.put({'restart exec msger': True})
                break

            if bookie_id_and_status:
                self.exec_msg_queue.put(bookie_id_and_status)
            time.sleep(0.1)

        log.info('Execution system messenger (thread id {}) is finished.'.format(self.thread.ident))


class ArbiExecMessenger(object):
    bet_type_map = {
            ('FT', 'OU Over') : 0,
            ('FT', 'OU Under'): 1,
            ('HT', 'OU Over') : 2,
            ('HT', 'OU Under'): 3,
            ('FT', 'AH Home') : 4,
            ('FT', 'AH Away') : 5,
            ('HT', 'AH Home') : 6,
            ('HT', 'AH Away') : 7,
            ('FT', '1x2 Home'): 8,
            ('FT', '1x2 Away'): 9,
            ('FT', '1x2 Draw'): 10,
            ('HT', '1x2 Home'): 11,
            ('HT', '1x2 Away'): 12,
            ('HT', '1x2 Draw'): 13,
            ('FT', 'EH Home') : 14,
            ('FT', 'EH Away') : 15,
            ('FT', 'EH Draw') : 16,
    }

    def __init__(self, host, port):
        self.host_port = (host, port)
        self.cooldown_opps = {}
        self.release_non_exist_cooldown_type1_count = 0
        self.release_non_exist_cooldown_type2_count = 0
        self.release_cooldown_count = 0
        self._connect()

        self.heartbeat_pkt = self.create_packet(gzip_string('NH^OK'))

    def login(self, username, password, version):
        msg = 'NL^{0}^{1}^{2}^{3}'.format(BET_API_VERSION, username, password, version)
        zmsg = gzip_string(msg)
        packet = self.create_packet(zmsg)
        self.write(packet)
        try:
            login_result = self.read_exec_msg()
        except ExecMsgerConnectionError:
            log.critical('Connection error when login to execution system')
            return False

        if len(login_result) == 1 and login_result[0].lower() == 'true':
            log.info('Successfully login to execution system: {0}'.format(login_result))
            return True
        else:
            log.critical('Failed to login to execution system: {0}'.format(login_result))
            return False

    def write(self, text):
        self.wfile.write(text)
        self.wfile.flush()

    def send_heartbeat(self):
        try:
            self.write(self.heartbeat_pkt)
        except (socket.error, AttributeError):
            raise ExecMsgerConnectionError

    def send(self, arbi_opps):
        """Send arbitrage opportunity to execution system."""
        bet_order_list = self.get_bet_order_list(arbi_opps)
        bet_order_str = '\n'.join(bet_order_list)
        zipped_orders = gzip_string(bet_order_str)
        packet = self.create_packet(zipped_orders)
        try:
            self.write(packet)
            self.log_delay(arbi_opps)
        except (socket.error, AttributeError):
            raise ExecMsgerConnectionError

    def log_delay(self, arbi_opps):
        delay = datetime.datetime.utcnow() - arbi_opps[0].occur_at_utc
        log.info('{} opportunities occurred at {} are {} ms delayed.'.format(
            len(arbi_opps), arbi_opps[0].occur_at_utc, delay.microseconds / 1000))

    def _connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.host_port)
        self.wfile = self.socket.makefile('wb', 0)
        self.rfile = self.socket.makefile('rb', -1)

    def filter_by_bookie_cooldown(self, arbi_opps):
        """Bookie cooldown.  When a arbitrage opportunity is sent, the involved bookies go to cool down by
        default, i.e. they can't be used until they update their prices.
        """
        return [arbi_opp for arbi_opp in arbi_opps if not self.any_bookie_in_cooldown(arbi_opp)]

    def any_bookie_in_cooldown(self, arbi_opp):
        """Is any bookie in cooldown?
        Yes -> return True
        No  -> return False and add the arbi_opp to self.cooldown_opps dict which looks like:
            {
                (timetype, match_id, htpt, atpt): {B1: price1, B2: price2, B3 ...},
                ...
            }
            where B1, B2, B3 are like: B{bookmaker_id}|{BetType}|{Dish}, e.g. B2|4|-5, B52|5|5
            Note: B1, B2, B3 are not necessarily selections for the same opportunity
        """
        time_type = self._get_time_type(arbi_opp)
        match_id = arbi_opp.match_info['match_id']
        htpt = arbi_opp.match_info['home_team_score']
        atpt = arbi_opp.match_info['away_team_score']
        bookie_info_and_price_pairs = [('B{}|{}|{}'.format(s.bookie_id, self._get_bet_type(s), '' if s.odds_type == '1x2' else int(s.subtype * 4)), s.odds)
                                       for s in arbi_opp.selections]

        bookie_price_dict = self.cooldown_opps.get((time_type, match_id, htpt, atpt))
        if bookie_price_dict:
            if any([price == bookie_price_dict.get(bookie_info) for bookie_info, price in bookie_info_and_price_pairs]):
                return True
            else:
                bookie_price_dict.update(dict(bookie_info_and_price_pairs))
                return False
        else:
            self.cooldown_opps[(time_type, match_id, htpt, atpt)] = dict(bookie_info_and_price_pairs)
            return False

    def get_bet_order_list(self, arbi_opps):
        """Given a list of ArbiOpportunity objects, return a list of string where each string is an bet order.

        :param arbi_opps: a list of ArbiOpportunity objects
        :return: a list of string in which each string is like "NB^{timetype}^{match_id}^{htpt}^{atpt}^[Odd1]^[Odd2]..."
                in which Odd is like:
                "O{bookmaker_id}|{bet_data}|{BetType}|{Dish}|{Odd}|{StakeRatio}"
        """
        return [self.convert_opp_to_str(arbi_opp) for arbi_opp in arbi_opps]

    def convert_opp_to_str(self, arbi_opp):
        """Given a arbitrage opportunity, return its bet order string
        """
        time_type = self._get_time_type(arbi_opp)
        match_id = arbi_opp.match_info['match_id']
        home_score = arbi_opp.match_info['home_team_score']
        away_score = arbi_opp.match_info['away_team_score']
        order = 'NB^{0}^{1}^{2}^{3}^{4}^{5}^{6}'.format(arbi_opp.strat_id, time_type, match_id, home_score,
                                                        away_score, arbi_opp.profit * 100, arbi_opp.occur_at_hk_str)
        for selection in arbi_opp.selections:
            bet_type = self._get_bet_type(selection)
            dish = '' if selection.odds_type == '1x2' else int(selection.subtype * 4)

            bet_data = selection.bet_data.replace('A', '').replace('B', '')
            bet_info = '^O{0}|{1}|{2}|{3}|{4}|{5}|{6}'.format(selection.bookie_id, bet_data, bet_type, dish,
                                                          selection.odds, selection.stake, int(selection.lay_flag))
            order += bet_info

        return order

    def _get_bet_type(self, selection):
        odds_type = selection.odds_type + ' ' + selection.subtype if selection.odds_type == '1x2' else selection.odds_type
        return self.bet_type_map[(selection.f_ht, odds_type)]

    def _get_time_type(self, arbi_opp):
        if arbi_opp.match_info['is_in_running']:
            time_type = 1
        else:
            hk_now = get_hk_time_now()
            match_hk_time = datetime.datetime.strptime(arbi_opp.match_info['match_hk_time'], '%Y-%m-%d %H:%M:%S')
            if hk_now.date() == match_hk_time.date() or \
                    (match_hk_time.date() - hk_now.date() == datetime.timedelta(days=1) and
                     match_hk_time.time() < datetime.time(hour=12) < hk_now.time()):
                time_type = 0
            else:
                # match for tomorrow morning
                time_type = 2

        return time_type

    def create_packet(self, stream):
        size = len(stream)
        head = create_packet_header(size)
        return head + stream + '[END]'

    def process_exec_msg(self):
        """Three type of messages for two issues:
        1. Bookie unavailable for some reason, e.g. their betting website is down.
        Message format: NS^<bookie_id>^<status>^<bet_period>,
            status: 0 means unavailable, 1 means available again.
            bet_period: 1: dead ball, 2: running ball, 0: both
        e.g. NS^2^0^2 means sbo running ball are temporarily unavailable

        2. Bookie unlock.  When a arbitrage opportunity is sent, the involved bookies get cool down by
        default, i.e. they can't be used until their prices are updated. Exec system can send orders to cancel cool down.
            NR^{timetype}^{match_id}^{htpt}^{atpt}^[B1]^[B2]
            where B{bookmaker_id}|{BetType}|{Dish}
        e.g. NR^2^1014182^-1^-1^B2|4|-5^B52|5|5

        3. Switch vip server.  Format: ND^{ip}^{port} e.g. ND^110.173.53.154^8090

        4. Switch YY server. Format: NY^{ip}^{port} e.g. ND^110.173.53.154^8090
        """
        exec_msg_dict = {}
        for msg in self.read_exec_msg():
            if msg.startswith('NS^'):
                bookie_id_and_status = {}
                self.process_exec_ns_msg(bookie_id_and_status, msg)
                if bookie_id_and_status:
                    if 'bookie id and status' in exec_msg_dict:
                        merge_dict(exec_msg_dict['bookie id and status'], bookie_id_and_status)
                    else:
                        exec_msg_dict['bookie id and status'] = bookie_id_and_status

            elif msg.startswith('NR^'):
                _, time_type, match_id, htpt, atpt, bookie_info_str = msg.split('^', 5)
                bookie_info_list = bookie_info_str.split('^')

                bookie_price_dict = self.cooldown_opps.get((time_type, match_id, htpt, atpt))
                if bookie_price_dict:
                    for bookie_info in bookie_info_list:
                        if bookie_info in bookie_price_dict:
                            bookie_price_dict.pop(bookie_info)
                            self.release_cooldown_count += 1
                        else:
                            log.warn('Trying to release an opportunity  that is not in cool down. Ignore.')
                            self.release_non_exist_cooldown_type1_count += 1
                else:
                    log.warn('Trying to release an opportunity that is not in cool down. Ignore.')
                    self.release_non_exist_cooldown_type2_count += 1

            elif msg.startswith('ND^'):
                _, ip, port = msg.split('^', 3)
                exec_msg_dict['switch vip server'] = ip, int(port)
            elif msg.startswith('NY^'):
                _, ip, port = msg.split('^', 3)
                exec_msg_dict['switch yy server'] = ip, int(port)

        return exec_msg_dict

    def process_exec_ns_msg(self, bookie_id_and_status, msg):
        try:
            _, bookie_id, status, bet_period = msg.split('^')
        except ValueError as e:
            log.error('Wrong format for message from exec system: "{}"'.format(e))
            return

        if status not in ['0', '1']:
            log.error('Wrong status for message from exec system: "{}"'.format(msg))
            return

        if bet_period not in ['0', '1', '2']:
            log.error('Wrong bet period for message from exec system: "{}"'.format(msg))
            return

        status = {'0': False, '1': True}[status]
        if bet_period == '0':
            bet_period_status = {'dead ball': status, 'running ball': status}
        elif bet_period == '1':
            bet_period_status = {'dead ball': status}
        else:  # bet_period == '2':
            bet_period_status = {'running ball': status}

        if bookie_id in BOOKIE_IDS_WITH_LAY_PRICES:
            merge_dict(bookie_id_and_status, {bookie_id + ' lay': bet_period_status})
        merge_dict(bookie_id_and_status, {bookie_id: bet_period_status})

    def read_exec_msg(self):
        try:
            head = self.rfile.read(4)
        except socket.error as e:
            log.error('Error in reading execution message header: {0}'.format(e))
            raise ExecMsgerConnectionError
        try:
            size = get_body_size(head)
        except Exception as e:
            log.error('Error in decoding execution message header: {0}'.format(e))
            size = 0

        if size > 0:
            zdata = ''
            try:
                while size > EXEC_READ_BLOCK_SIZE:
                    zdata += self.rfile.read(EXEC_READ_BLOCK_SIZE)
                    size -= EXEC_READ_BLOCK_SIZE
                else:
                    zdata += self.rfile.read(size)
            except socket.error as e:
                udata = None
                log.error('Error in reading execution message body: {0}'.format(e))
            else:
                udata = unzip_string(zdata)

            if udata is None:
                log.error('Error when unzip exec system data.')
                data = []
            else:
                data = udata.strip().split("\n")
        else:
            data = []

        return data

    def close_socket(self):
        try:
            self.rfile.close()
            self.wfile.close()
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except Exception as e:
            log.info('Ignore this error: {}'.format(e))

    def __del__(self):
        try:
            self.close_socket()
        except:
            pass


class MockMessenger(ArbiExecMessenger):
    def __init__(self, *args, **kwargs):
        # self.unavailable_opps = {}
        self.do_switch_counter = 0
        self.host_counter = 0
        super(MockMessenger, self).__init__(*args, **kwargs)
        log.info('Use mock execution system messenger.')

    def __del__(self):
        pass

    def login(self, username, password, version):
        return True

    def write(self, text):
        pass

    def _connect(self):
        pass

    def reconnect(self):
        pass

    def send_heartbeat(self):
        pass

    def process_exec_msg(self):
        return {}

        # Uncomment out to test switching yy server
        # from arbi.feeds.betfair.constants import BETFAIR_FEED_IP, BETFAIR_FEED_PORT
        # while True:
        #     time.sleep(1)
        #     self.do_switch_counter += 1
        #     if self.do_switch_counter % 20 == 0:
        #         ip = BETFAIR_FEED_IP if self.host_counter % 2 else '12.34.56.78'
        #         port = BETFAIR_FEED_PORT if self.host_counter % 2 else 12345
        #         self.host_counter += 1
        #         return {'switch yy server': (ip, int(port))}
        #     else:
        #         return {}
