import time
import logging

from mock import Mock
from PySide.QtCore import QObject, Signal

from arbi.constants import THREAD_ALIVE_CHECK_INTERVAL
from arbi.feeds.vip.networking import VIPFeedThreadObj
from arbi.feeds.vip.constants import TC_TOOL_ACCOUNT, BACKUP_ACCOUNT
from arbi.feeds.betfair.feed import BetfairFeedThreadObj
from arbi.feeds.betfair.constants import BETFAIR_FEED_IP, BETFAIR_FEED_PORT, YY_UN4TC, YY_PW4TC
from arbi.tools.tc.web.sporttery import SportteryScraperThreadObj
from arbi.tools.tc.web.web_api import VIPMatchMappingAPI
from arbi.tools.tc.constants import TC_TOOL_VER, LOG_MEMORY_FREQUENCY, LOG_UNKNOWN_MATCH_ID_FREQUENCY, MAX_SOURCE_QUEUE_SIZE, SOURCE_QUEUE_CLEARANCE_SIZE
from arbi.utils import merge_dict, get_memory_usage
from arbi.arbi_discovery import ArbiDiscoveryThread


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class TCArbiDiscoverySignal(QObject):
    found = Signal(list)
    pkg_count = Signal(int)


class TCArbiDiscoveryThread(ArbiDiscoveryThread):
    def __init__(self, data_engine, arbi_spotter, menu_bar_model):
        super(TCArbiDiscoveryThread, self).__init__(data_engine, arbi_spotter, menu_bar_model)
        self.signal = TCArbiDiscoverySignal()
        self.exec_msger_queue = Mock()
        self.exec_msger_thread = Mock()
        self.api = VIPMatchMappingAPI()

        self.log_frequency_ts = 0
        self.log_memory_ts = 0

    def check_threads_alive(self):
        super(TCArbiDiscoveryThread, self).check_threads_alive()
        t = time.time()
        if t - self.threads_alive_last_checked > THREAD_ALIVE_CHECK_INTERVAL:
            if self.sporttery_scraper_thread and self.check_sporttery_thread_flag and not self.sporttery_scraper_thread.thread.is_alive():
                self.sporttery_scraper_thread.start()

    def update_engine_with_sporttery_data(self, sporttery_data):
        match_id_and_odds_dict_list = self.api.map_sporttery_data(sporttery_data)
        log.info('%s matches from Sporttery website successfully mapped.', len(match_id_and_odds_dict_list))

        t = time.time()
        if t - self.log_frequency_ts > LOG_UNKNOWN_MATCH_ID_FREQUENCY:
            log_flag = True
            self.log_frequency_ts = t
        else:
            log_flag = False

        for match_id, odds_dict in match_id_and_odds_dict_list:
            if match_id in self.engine.match_dict:
                match = self.engine.match_dict[match_id]
                if match.odds:
                    merge_dict(match.odds.odds_dict, odds_dict)
                    match.info['single_market_flag'] = 0  # single_market_flag
            elif log_flag:
                log.warning('VIP match mapping API returns unknown match id: {}'.format(match_id))

    def run_discovery_loop(self):
        log.info('TC Tool has started. Version: {}'.format(TC_TOOL_VER))

        if self.menu_bar_model.account_model.use_sporttery_mock_data:
            self.api.set_mock_request_flag()

        if self.menu_bar_model.account_model.vip_feed_enabled:
            self.run_vip_feed_thread()
        time.sleep(3)  # make sure exec msger thread and vip feed thread have done initialization
        if self.menu_bar_model.account_model.yy_feed_enabled:
            self.run_betfair_feed_thread()
        self.run_sporttery_scraper_thread()

        pkg_count = 0
        signalled_pkg_count = 0
        queue_empty_count = 0
        self.threads_alive_last_checked = time.time()
        self.init_data_engine_match_dict()

        while self.is_running:
            self.check_threads_alive()

            if self.source_queue.empty():
                queue_empty_count += 1
                if self.break_loop_count and queue_empty_count >= self.break_loop_count:
                    break
                time.sleep(1)
                continue
            else:
                self.engine.clear_in_running_matches()
                while not self.source_queue.empty():
                    qsize = self.source_queue.qsize()
                    if qsize > MAX_SOURCE_QUEUE_SIZE:
                        self.clear_source_queue_partially(SOURCE_QUEUE_CLEARANCE_SIZE)

                    self.update_engine_with_new_odds()

                    pkg_count += 1
                    if signalled_pkg_count != pkg_count and pkg_count and pkg_count % 500 == 0:
                        self.signal.pkg_count.emit(pkg_count)
                        signalled_pkg_count = pkg_count

            self.log_memory()

            r_arbi_opps = self.arbi_spotter.spot_arbi()
            arbi_opps = self.filter_arbi_opps(r_arbi_opps)
            if arbi_opps:
                self.signal_table_view_update(arbi_opps)

        self.signal.pkg_count.emit(pkg_count)

    def clear_source_queue_partially(self, size):
        log.warning('Source queue size hit %s, memory used: %s MB', self.source_queue.qsize(), get_memory_usage())
        for i in xrange(size):
            self.source_queue.get()
        log.warning('Removed %s items from source queue, memory used: %s MB', size, get_memory_usage())

    def log_memory(self):
        t = time.time()
        if t - self.log_memory_ts > LOG_MEMORY_FREQUENCY:
            self.log_memory_ts = t
            log.info('Memory used {} MB.'.format(get_memory_usage()))

    def update_engine_with_new_odds(self):
        record_list = self.source_queue.get()
        if isinstance(record_list, dict):
            if record_list.get('sporttery'):
                self.update_engine_with_sporttery_data(record_list.get('football'))
            else:
                # vip init dict, ignore
                pass
        else:
            self.engine.update_match_dict(record_list)

    def signal_table_view_update(self, arbi_opps):
        arbi_summary = [opp.get_summary() for opp in arbi_opps]
        self.signal.found.emit(arbi_summary)

    def filter_arbi_opps(self, arbi_opps):
        """Apply various of rules to filter out the opportunities that we don't want
        """
        arbi_opps = self.filter_non_sporttery_opps(arbi_opps)
        return arbi_opps

    def filter_non_sporttery_opps(self, arbi_opps):
        """An arb opp must involve sporttery."""
        sporttery_opps = [arbi_opp for arbi_opp in arbi_opps if '99' in arbi_opp.involved_bookie_ids]
        all_opps = []
        for opp in sporttery_opps:
            all_opps.append(opp)
            opp_without_rebate = self.arbi_spotter.recalculate_without_sporttery_rebate(opp)
            if opp_without_rebate:
                all_opps.append(opp_without_rebate)

        return all_opps

    def run(self):
        # Runtime setup
        self.arbi_spotter.profit_threshold = self.menu_bar_model.account_model.profit_threshold
        self.arbi_spotter.initialize_strats()
        self.check_vip_thread_flag = (not self.menu_bar_model.account_model.use_vip_mock_data) and self.menu_bar_model.account_model.vip_feed_enabled
        self.check_betfair_thread_flag = (not self.menu_bar_model.account_model.use_betfair_mock_data) and self.menu_bar_model.account_model.yy_feed_enabled
        self.check_exec_msger_thread_flag = False
        self.check_sporttery_thread_flag = not self.menu_bar_model.account_model.use_sporttery_mock_data

        # Reset data
        self.is_running = True
        self.engine.clear_data()

        # Discovery loop
        self.run_discovery_loop()

    def run_vip_feed_thread(self):
        model = self.menu_bar_model.account_model
        self.vip_feed_thread = VIPFeedThreadObj(self.source_queue,
                                                model.use_vip_mock_data,
                                                (model.vip_mock_data_pkg_num, None),
                                                (model.vip_ip, model.vip_port),
                                                TC_TOOL_ACCOUNT,
                                                #BACKUP_ACCOUNT,
                                                model.save_vip_history_flag,
                                                sports_supported=('football', 'basketball'),
                                                )
        self.vip_feed_thread.start()

    def run_betfair_feed_thread(self):
        model = self.menu_bar_model.account_model
        self.betfair_feed_thread = BetfairFeedThreadObj(self.source_queue,
                                              model.use_betfair_mock_data,
                                              (model.betfair_mock_data_pkg_num, None),
                                              (BETFAIR_FEED_IP, BETFAIR_FEED_PORT),
                                              (YY_UN4TC, YY_PW4TC),
                                              model.save_betfair_history_flag,
                                            )
        self.betfair_feed_thread.start()

    def run_sporttery_scraper_thread(self):
        self.sporttery_scraper_thread = SportteryScraperThreadObj(self.source_queue, self.menu_bar_model.account_model)
        self.sporttery_scraper_thread.start()

    def stop(self):
        super(TCArbiDiscoveryThread, self).stop()
        if self.sporttery_scraper_thread:
            self.sporttery_scraper_thread.stop_event.set()

    def init_arbi_spotter_unavailable_bookie_ids(self):
        pass

    def process_exec_msger_queue(self):
        pass

    def run_exec_msger_thread(self, restart=False):
        pass
