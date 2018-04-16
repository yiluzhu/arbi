"""
Main model
"""
import time
import datetime
import logging

from PySide.QtCore import QObject, Signal

from arbi.models.engine import DataEngine
from arbi.models.arbi_spotter import ArbiSpotter
from arbi import constants
from arbi.ui_models.menu_bar_model import MenuBarModel
from arbi.ui_models.engine_inspector_model import DataEngineTableModel, DATA_ENGINE_TABLE_HEADER
from arbi.arbi_summary import ArbiSummaryTableModel, ArbiSummaryLogger
from arbi.arbi_discovery import ArbiDiscoveryThread


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class ViewSignal(QObject):
    """This is how the model talks to the view
    """
    update_vip_host_display = Signal(str)
    update_yy_host_display = Signal(str)
    historic_opps_count = Signal(int)

class ArbiProModel(object):
    def __init__(self):
        # UI models
        self.menu_bar_model = MenuBarModel()
        self.pkt_count = 0
        self.view_signal = ViewSignal()

        self.engine = DataEngine()
        self.arbi_spotter = ArbiSpotter(self.engine.match_dict, menu_bar_model=self.menu_bar_model)
        self.arbi_summary_logger = ArbiSummaryLogger()
        self.table_model = ArbiSummaryTableModel([], constants.ARBI_SUMMARY_HEADER)
        self.table_model_for_history = ArbiSummaryTableModel([], constants.ARBI_SUMMARY_HEADER)
        self.engine_table_model = DataEngineTableModel(self.engine, DATA_ENGINE_TABLE_HEADER)

        self.arbi_discovery = ArbiDiscoveryThread(self.engine, self.arbi_spotter, self.menu_bar_model)
        self.arbi_discovery.finished.connect(self.post_work)
        self.arbi_discovery.signal.found.connect(self.update_table_view)
        self.arbi_discovery.signal.pkg_count.connect(self.update_pkt_count)
        self.arbi_discovery.signal.switch_vip_server.connect(self.update_vip_host_display)
        self.arbi_discovery.signal.switch_yy_server.connect(self.update_yy_host_display)

    def record_init_finished_time(self, timestamp):
        """The timestamp when processing of initial packet finished.
        """
        self.init_finished_time = timestamp

    def update_vip_host_display(self, ip_and_port_str):
        self.view_signal.update_vip_host_display.emit(ip_and_port_str)

    def update_yy_host_display(self, ip_and_port_str):
        self.view_signal.update_yy_host_display.emit(ip_and_port_str)

    def update_pkt_count(self, count_tuple):
        self.pkt_count, average_queue_size = count_tuple
        log.info('-- pkt_count:%s, average_queue_size: %s', self.pkt_count, average_queue_size)
        if self.menu_bar_model.account_model.table_view_update and self.pkt_count % 500 == 0 and self.table_model.table != [[]]:
            # if we didn't clear it, the old content would be in the table view forever
            self.table_model.update([[]])
        if self.pkt_count % 4000 == 0:
            log.info('System has been running for {0}'.format(
                str(datetime.timedelta(seconds=int(time.time() - self.start_time)))))
            log.info('Total number of matches in the system: {}'.format(len(self.engine.match_dict)))

    def update_table_view(self, arbi_summary):
        history_arbi_summary = self.arbi_summary_logger.save(arbi_summary)
        self.table_model.update(arbi_summary)
        if history_arbi_summary:
            self.table_model_for_history.append(history_arbi_summary)
            self.view_signal.historic_opps_count.emit(self.table_model_for_history.rowCount(None))

    def start(self):
        self.start_time = time.time()
        self.table_model.clear_data()
        self.arbi_discovery.start()

    def post_work(self):
        finish_time = time.time()
        log.info('Total running time: {} seconds. Total packets processed: {}'.format(
            finish_time - self.start_time, self.pkt_count))

    def stop(self):
        log.info('Application has been stopped manually.')
        self._stop()

    def _stop(self):
        self.arbi_discovery.stop()
