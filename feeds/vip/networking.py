# -*- coding: GBK -*-

import logging
import datetime
from arbi.models.record import InitOddsRecord, VIPUpdateOddsRecord, MatchInfoRecord, IncorrectLengthRecord
from arbi.feeds.vip.constants import SOCKET_TIMEOUT_IN_SECONDS
from arbi.models.match import Match
from arbi.feeds.base_feed import BaseFeedThreadObj, BaseFeed, FeedConnectionError


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class VIPFeed(BaseFeed):
    FEED_NAME = 'VIP'

    def __init__(self, host, port):
        super(VIPFeed, self).__init__(host, port)
        self.socket.settimeout(SOCKET_TIMEOUT_IN_SECONDS)

    def get_login_string(self, username, password):
        return 'V021{0},{1}\n'.format(username, password)

    def login_succeeded(self, login_result):
        return len(login_result) == 1 and login_result[0][0] == '1'


class VIPFeedThreadObj(BaseFeedThreadObj):
    FEED_NAME = 'VIP'
    FEED_CLASS = VIPFeed

    def __init__(self, queue, use_mock_data, mock_data_pkg_num_and_data_gen_and_time, host_port, username_password,
                 save_history_flag, sports_supported=frozenset(['football'])):
        super(VIPFeedThreadObj, self).__init__(queue, use_mock_data, mock_data_pkg_num_and_data_gen_and_time,
                                               host_port, username_password, save_history_flag)
        self.record_type_map = {
            'M': MatchInfoRecord,
            'O': InitOddsRecord,
            'o': VIPUpdateOddsRecord,
        }
        self.vip_data_update_id_dict = {}
        self.sports_supported = sports_supported

    def initialize_data_feed(self):
        log.info('Start initializing VIP feed data...')
        try:
            packet = self.data_feed.get_one_packet()
        except FeedConnectionError:
            log.info('Error in initializing VIP feed data.')
            return

        if self.save_history_flag:
            self.save_history(packet)

        init_dict = self.initialize_match_dict(packet)
        log.info('Initializing VIP feed data finished.')
        return init_dict

    def initialize_match_dict(self, packet):
        """A match can only be initialized by MatchInfoRecord.
        InitOddsRecord must have corresponding MatchInfoRecord.
        """
        match_records, init_odds_records = self.get_match_records_and_init_odds_records(packet)
        init_dict = self.process_match_records(match_records)
        init_dict = self.process_init_odds_records(init_odds_records, init_dict)

        return init_dict

    def process_init_odds_records(self, init_odds_records, init_dict):
        for init_odds_record in init_odds_records:
            match_id = init_odds_record.record_dict['match_id']
            if match_id in init_dict:
                init_dict[match_id].init_update(init_odds_record)

        return init_dict

    def process_match_records(self, match_records):
        init_dict = {}

        for match_record in match_records:
            match_id = match_record.record_dict['match_id']
            if match_id in init_dict:
                init_dict[match_id].init_update(match_record)
            else:
                init_dict[match_id] = Match(match_record)

        return init_dict

    def run_loop(self):
        while not self.stop_event.is_set():
            try:
                packet = self.data_feed.get_one_packet()
            except StopIteration:
                log.info('stop iteration.')
                break
            except FeedConnectionError:
                log.error('Feed connection error in VIP feed.')
                break

            if len(packet) == 1 and packet[0] == 'LOGOUT\x00':
                log.critical('You have been logged out')
                break

            if self.save_history_flag:
                self.save_history(packet)

            record_list = self.get_update_record_list(packet)

            if record_list:
                self.queue.put(record_list)

    def run_pre_loop(self):
        signal = super(VIPFeedThreadObj, self).run_pre_loop()
        if signal is self.TT_SIGNAL:
            return self.TT_SIGNAL

        init_dict = self.initialize_data_feed()
        if init_dict is None:
            return self.TT_SIGNAL
        else:
            self.queue.put(init_dict)
            self.queue.has_put_init_dict_in = True

    def _get_records(self, packet):
        for record_str in packet:
            record_type = record_str[0]
            if record_type not in self.record_type_map:
                # There could be validation record strings in the packet, e.g. 'p1234567'
                # We don't care about them.
                continue

            record_class = self.record_type_map[record_type]
            try:
                record = record_class(record_str)
            except Exception as e:
                log.error('Error when create record for str {}: {}'.format(record_str, e))
            else:
                # match_id = record.record_dict['match_id']
                # if isinstance(record, VIPUpdateOddsRecord):
                #     update_id = record.record_dict['update_id']
                #     if match_id in self.vip_data_update_id_dict:
                #         if self.vip_data_update_id_dict[match_id] < update_id:
                #             self.vip_data_update_id_dict[match_id] = update_id
                #         else:
                #             # received out of date data, ignore
                #             continue
                #     else:
                #         log.error('Found VIPUpdateOddsRecord for unknown match: {}'.format(match_id))
                #         continue
                # else:
                #     if match_id not in self.vip_data_update_id_dict:
                #         self.vip_data_update_id_dict[match_id] = 0

                if self.update_vip_update_id(record) and record.is_valid():
                    yield record

    def update_vip_update_id(self, record):
        match_id = record.record_dict['match_id']
        if isinstance(record, VIPUpdateOddsRecord):
            update_id = record.record_dict['update_id']
            if match_id in self.vip_data_update_id_dict:
                if self.vip_data_update_id_dict[match_id] < update_id:
                    self.vip_data_update_id_dict[match_id] = update_id
                else:
                    # received out of date data, ignore
                    return False
            else:
                log.error('Found VIPUpdateOddsRecord for unknown match: {}'.format(match_id))
                return False
        else:
            if match_id not in self.vip_data_update_id_dict:
                self.vip_data_update_id_dict[match_id] = 0

        return True

    def get_update_record_list(self, packet):
        """Return a list of record objects"""
        assert isinstance(packet, list), 'Expected type: list, got type: {}'.format(type(packet))
        update_record_list = []
        for record in self._get_records(packet):
            if isinstance(record, MatchInfoRecord):
                if not self.is_sport_type_supported(record) or not self.is_match_in_7_days(record):
                    continue
            elif isinstance(record, InitOddsRecord):
                log.error('Should not have InitOddsRecord in update packet: {}'.format(
                    record.record_str))
                continue
            record.post_validation_work()
            update_record_list.append(record)

        return update_record_list

    def get_match_records_and_init_odds_records(self, packet):
        """Given a packet, return a list of match records and a list of init odds records.
        The match records will be processed first, then the init odds records.

        :param packet: a feed packet
        """
        match_records = []
        init_odds_records = []

        for record in self._get_records(packet):
            if isinstance(record, MatchInfoRecord):
                if self.is_sport_type_supported(record) and self.is_match_in_7_days(record):
                    record.post_validation_work()
                    match_records.append(record)
            elif isinstance(record, InitOddsRecord):
                record.post_validation_work()
                init_odds_records.append(record)
            else:
                log.error('Should not have VIPUpdateOddsRecord in initial packet: {}'.format(
                    record.record_str))

        return match_records, init_odds_records

    def is_sport_type_supported(self, match_record):
        sport_type = match_record.get_sport_type()
        if sport_type in self.sports_supported:
            return True
        else:
            log.info('Ignore unsupported match record (id {}, league {})'.format(
                match_record.record_dict['match_id'], match_record.record_dict['league_name']))
            return False

    def is_match_in_7_days(self, match_record):
        match_hk_time_str = match_record.record_dict['match_hk_time']
        match_hk_time = datetime.datetime.strptime(match_hk_time_str, '%Y-%m-%d %H:%M:%S')
        return datetime.datetime.utcnow() + datetime.timedelta(days=7, hours=8) > match_hk_time
