import time
import logging
from Queue import Queue
from PySide.QtCore import QThread, QObject, Signal
from arbi.utils import merge_dict
from arbi.constants import THREAD_ALIVE_CHECK_INTERVAL, PROCESS_EXEC_MSG_MAX_TIME, EMPTY_SRC_Q_SLEEP_TIME, BOOKIE_ID_MAP
from arbi.feeds.vip.networking import VIPFeedThreadObj
from arbi.feeds.vip.constants import RECONNECT_DELAY, ACCOUNT_MAP
from arbi.feeds.betfair.feed import BetfairFeedThreadObj
from arbi.feeds.betfair.constants import BETFAIR_FEED_IP, BETFAIR_FEED_PORT, BETFAIR_USERNAME, BETFAIR_PASSWORD
from arbi.execution.constants import HEARTBEAT_INTERVAL, EXEC_RECONNECT_DELAY
from arbi.execution.arbi_exec import ArbiExecMsgerThreadObj, ExecMsgerConnectionError


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class ArbiDiscoverySignal(QObject):
    found = Signal(list)
    pkg_count = Signal(tuple)
    switch_vip_server = Signal(str)
    switch_yy_server = Signal(str)


class ArbiDiscoveryThread(QThread):
    def __init__(self, data_engine, arbi_spotter, menu_bar_model):
        QThread.__init__(self, None)
        self.engine = data_engine
        self.arbi_spotter = arbi_spotter
        self.menu_bar_model = menu_bar_model
        self.signal = ArbiDiscoverySignal()
        self.heartbeat_time = time.time()
        self.source_queue = Queue()
        self.source_queue.has_put_init_dict_in = False

        self.exec_msger_queue = None
        self.exec_msger_thread = None
        self.vip_feed_thread = None
        self.betfair_feed_thread = None
        self.slow_strats_pool = None
        self.is_running = False
        self.threads_alive_last_checked = 0

        self.break_loop_count = 0  # this is a flag that is mainly used in tests

    def update_arbi_spotter_unavailable_bookie_ids(self, bookie_id_and_status):
        """Take bookie_id_and_status which looks like:
            {
                '2': {'running ball': True},
                '1': {'dead ball': False, 'running ball': True},
            }
        and update self.arbi_spotter.bookie_availability_dict which looks like:
            {
                '2': {'dead ball': True, 'running ball': False},
                '1': {'dead ball': True, 'running ball': False},
            }
        """
        merge_dict(self.arbi_spotter.bookie_availability_dict, bookie_id_and_status)

    def check_threads_alive(self):
        t = time.time()
        if t - self.threads_alive_last_checked > THREAD_ALIVE_CHECK_INTERVAL:
            self.threads_alive_last_checked = t
            if self.vip_feed_thread and self.check_vip_thread_flag and not self.vip_feed_thread.thread.is_alive():

                self.vip_feed_thread.start(delay=RECONNECT_DELAY)
            if self.betfair_feed_thread and self.check_betfair_thread_flag and not self.betfair_feed_thread.thread.is_alive():
                self.betfair_feed_thread.start(delay=5)
            if self.exec_msger_thread and self.check_exec_msger_thread_flag and not self.exec_msger_thread.thread.is_alive():
                self.run_exec_msger_thread(restart=True)

    def init_data_engine_match_dict(self):
        while self.is_running:
            if self.source_queue.empty():
                time.sleep(1)
            else:
                init_dict = self.source_queue.get()
                self.engine.init_match_dict(init_dict)
                return
            self.check_threads_alive()

    def run_discovery_loop(self):
        self.run_exec_msger_thread()
        if self.menu_bar_model.account_model.wait_for_vip_host_info:
            while not self.vip_feed_thread:
                self.process_exec_msger_queue()
                time.sleep(0.5)
        else:
            if self.menu_bar_model.account_model.vip_feed_enabled:
                self.run_vip_feed_thread()
        time.sleep(1)  # make sure exec msger thread and vip feed thread have done initialization
        if self.menu_bar_model.account_model.yy_feed_enabled:
            self.run_betfair_feed_thread()

        pkg_count = 0
        signalled_pkg_count = 0
        queue_empty_count = 0
        total_queue_size = 0
        total_queue_size_count = 0
        self.threads_alive_last_checked = time.time()

        self.init_data_engine_match_dict()

        while self.is_running:
            self.check_threads_alive()

            self.process_exec_msger_queue()

            if self.source_queue.empty():
                queue_empty_count += 1
                if self.break_loop_count and queue_empty_count >= self.break_loop_count:
                    break
                time.sleep(EMPTY_SRC_Q_SLEEP_TIME)
            else:
                self.engine.clear_unneeded_matches()
                total_queue_size += self.source_queue.qsize()
                total_queue_size_count += 1
                while not self.source_queue.empty():
                    record_list = self.source_queue.get()
                    self.engine.update_match_dict(record_list)
                    pkg_count += 1

                    if signalled_pkg_count != pkg_count and pkg_count and pkg_count % 100 == 0:
                        self.signal.pkg_count.emit((pkg_count, float(total_queue_size) / total_queue_size_count))
                        signalled_pkg_count = pkg_count

            r_arbi_opps = self.arbi_spotter.spot_arbi()
            if not self.exec_msger_thread.exec_messenger:
                continue  # error when connect with execution system

            arbi_opps = self.filter_arbi_opps(r_arbi_opps)

            current_time = time.time()
            if arbi_opps:
                try:
                    self.exec_msger_thread.exec_messenger.send(arbi_opps)
                except ExecMsgerConnectionError:
                    self.run_exec_msger_thread(restart=True)

                self.signal_table_view_update(arbi_opps)
                self.heartbeat_time = current_time
            elif current_time - self.heartbeat_time > HEARTBEAT_INTERVAL:
                try:
                    self.exec_msger_thread.exec_messenger.send_heartbeat()
                except ExecMsgerConnectionError:
                    self.run_exec_msger_thread(restart=True)

                self.heartbeat_time = current_time

        self.signal.pkg_count.emit(((pkg_count, float(total_queue_size) / total_queue_size_count)))

    def signal_table_view_update(self, arbi_opps):
        if self.menu_bar_model.account_model.table_view_update:
            arbi_summary = [opp.get_summary() for opp in arbi_opps]
            self.signal.found.emit(arbi_summary)

    def process_exec_msger_queue(self):
        bookie_status_dict = {}
        t0 = time.time()
        count = 0
        while not self.exec_msger_queue.empty():
            count += 1
            exec_msg_dict = self.exec_msger_queue.get()

            switch_vip_server = exec_msg_dict.get('switch vip server')
            if switch_vip_server:
                self.switch_vip_feed(switch_vip_server[0], switch_vip_server[1])

            switch_yy_server = exec_msg_dict.get('switch yy server')
            if switch_yy_server:
                self.switch_yy_feed(switch_yy_server[0], switch_yy_server[1])

            bookie_id_and_status = exec_msg_dict.get('bookie id and status')
            if bookie_id_and_status:
                bookie_status_dict.update(bookie_id_and_status)

            restart_exec_msger_thread = exec_msg_dict.get('restart exec msger')
            if restart_exec_msger_thread:
                self.run_exec_msger_thread(restart=True)

        if bookie_status_dict:
            self.update_arbi_spotter_unavailable_bookie_ids(bookie_status_dict)

        t = time.time()
        if t - t0 > PROCESS_EXEC_MSG_MAX_TIME:
            log.warning('It took {} seconds to process {} execution system messages'.format(t - t0, count))

    def filter_arbi_opps(self, arbi_opps):
        """Apply various of rules to filter out the opportunities that we don't want
        """
        #arbi_opps = self.filter_bookies_leagues_and_teams(arbi_opps)
        arbi_opps = self.exec_msger_thread.exec_messenger.filter_by_bookie_cooldown(arbi_opps)

        return arbi_opps

    def filter_bookies_leagues_and_teams(self, arbi_opps):
        """These are from menu and entered manually by users
        """
        filtered_bookies = self.menu_bar_model.filter_panel_model.filtered_bookies
        filtered_leagues = self.menu_bar_model.filter_panel_model.filtered_leagues
        filtered_teams = self.menu_bar_model.filter_panel_model.filtered_teams

        return [arbi_opp for arbi_opp in arbi_opps
                if
                all(BOOKIE_ID_MAP[bookie_id] in filtered_bookies for bookie_id in arbi_opp.involved_bookie_ids)
                and
                (filtered_leagues == [] or arbi_opp.match_info['league_name'] in filtered_leagues)
                and
                (filtered_teams == [] or (arbi_opp.match_info['home_team_name'] in filtered_teams or
                                          arbi_opp.match_info['away_team_name'] in filtered_teams))
                ]

    def init_arbi_spotter_unavailable_bookie_ids(self):
        all_unavailable_dict = {bookie_id: {'dead ball': False, 'running ball': False}
                                for bookie_id in BOOKIE_ID_MAP.keys()}
        self.arbi_spotter.bookie_availability_dict.update(all_unavailable_dict)

    def run(self):
        # Runtime setup
        self.arbi_spotter.profit_threshold = self.menu_bar_model.account_model.profit_threshold
        self.arbi_spotter.initialize_strats()
        self.check_vip_thread_flag = (not self.menu_bar_model.account_model.use_vip_mock_data)
        self.check_betfair_thread_flag = self.menu_bar_model.account_model.yy_feed_enabled
        self.check_exec_msger_thread_flag = self.menu_bar_model.account_model.send_orders
        self.vip_thread_last_checked = None
        self.exec_msger_thread_last_checked = None

        # Reset data
        self.is_running = True
        self.engine.clear_data()

        if not self.menu_bar_model.account_model.use_vip_mock_data:
            self.init_arbi_spotter_unavailable_bookie_ids()

        # Discovery loop
        self.run_discovery_loop()

    def run_vip_feed_thread(self):
        model = self.menu_bar_model.account_model
        self.vip_feed_thread = VIPFeedThreadObj(self.source_queue,
                                              model.use_vip_mock_data,
                                              (model.vip_mock_data_pkg_num, None),
                                              (model.vip_ip, model.vip_port),
                                              ACCOUNT_MAP[model.vip_account_index],
                                              model.save_vip_history_flag,
                                            )
        self.vip_feed_thread.start()

    def run_betfair_feed_thread(self):
        model = self.menu_bar_model.account_model
        self.betfair_feed_thread = BetfairFeedThreadObj(self.source_queue,
                                              model.use_betfair_mock_data,
                                              (model.betfair_mock_data_pkg_num, None),
                                              (model.yy_ip, model.yy_port),
                                              (BETFAIR_USERNAME, BETFAIR_PASSWORD),
                                              model.save_betfair_history_flag,
                                            )
        self.betfair_feed_thread.start()

    def run_exec_msger_thread(self, restart=False):
        """Restart exec msger thread can be triggered by the thread itself when it fails to read from exec system;
        or by arbi discovery when it fails to send data to exec system.
        """
        if restart:
            log.error('*** Lost connection to Execution System server. Reconnect in {} seconds. ***'.format(EXEC_RECONNECT_DELAY))
            self.exec_msger_thread.stop_event.set()
            time.sleep(EXEC_RECONNECT_DELAY)
            log.error('*** Reconnecting to Execution System server... ***')

        model = self.menu_bar_model.account_model
        self.exec_msger_queue = Queue()
        self.exec_msger_thread = ArbiExecMsgerThreadObj(self.exec_msger_queue,
                                                        model.send_orders, model.exec_system_on_localhost)
        self.exec_msger_thread.start()

    def switch_vip_feed(self, ip, port):
        if not self.menu_bar_model.account_model.vip_feed_enabled:
            log.info('VIP feed not enabled. Ignore switching command.')

        if self.vip_feed_thread:
            self.vip_feed_thread.stop_event.set()
        model = self.menu_bar_model.account_model
        model.vip_ip = ip
        model.vip_port = port
        host = '{}:{}'.format(ip, port)
        log.info('Switch to new VIP server {} in 5 seconds.'.format(host))

        time.sleep(5)
        self.signal.switch_vip_server.emit(host)
        self.run_vip_feed_thread()

    def switch_yy_feed(self, ip, port):
        if not self.menu_bar_model.account_model.yy_feed_enabled:
            log.info('YY feed not enabled. Ignore switching command.')

        if self.betfair_feed_thread:
            self.betfair_feed_thread.stop_event.set()
        model = self.menu_bar_model.account_model
        model.yy_ip = ip
        model.yy_port = port
        host = '{}:{}'.format(ip, port)
        log.info('Switch to new YY server {} in 5 seconds.'.format(host))

        time.sleep(5)
        self.signal.switch_yy_server.emit(host)
        self.run_betfair_feed_thread()

    def stop(self):
        self.is_running = False

        self.arbi_spotter.terminate_all_pools()

        if self.vip_feed_thread:
            self.vip_feed_thread.stop_event.set()
        if self.betfair_feed_thread:
            self.betfair_feed_thread.stop_event.set()
        self.exec_msger_thread.stop_event.set()
