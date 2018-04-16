import logging
import time
import datetime
from PySide.QtCore import QObject, Signal

from arbi import constants
from arbi.models.engine import DataEngine
from arbi.utils import get_memory_usage
from arbi.tools.tc.models.tc_arbi_spotter import TCArbiSpotter
from arbi.tools.tc.ui_models.tc_menu_bar_model import TCMenuBarModel
from arbi.tools.tc.tc_arbi_discovery import TCArbiDiscoveryThread
from arbi.arbi_summary import ArbiSummaryTableModel, ArbiSummaryLogger
from arbi.ui_models.engine_inspector_model import DataEngineTableModel, DATA_ENGINE_TABLE_HEADER


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class ViewSignal(QObject):
    """This is how the model talks to the view"""
    historic_opps_count = Signal(int)


class TCModel(object):
    def __init__(self):
        self.menu_bar_model = TCMenuBarModel()
        self.view_signal = ViewSignal()

        self.engine = DataEngine()
        self.arbi_spotter = TCArbiSpotter(self.engine.match_dict, self.menu_bar_model)
        self.arbi_summary_logger = ArbiSummaryLogger()
        self.table_model = ArbiSummaryTableModel([], constants.ARBI_SUMMARY_HEADER)
        self.table_model_for_history = ArbiSummaryTableModel([], constants.ARBI_SUMMARY_HEADER)
        self.engine_table_model = DataEngineTableModel(self.engine, DATA_ENGINE_TABLE_HEADER)

        self.tc_arbi_discovery = TCArbiDiscoveryThread(self.engine, self.arbi_spotter, self.menu_bar_model)
        self.tc_arbi_discovery.signal.found.connect(self.update_table_view)
        self.tc_arbi_discovery.signal.pkg_count.connect(self.update_pkt_count)

    def update_pkt_count(self, pkt_count):
        log.info('-- pkt_count -- {0}'.format(pkt_count))
        if self.table_model.table != [[]]:
            # if we didn't clear it, the old content would be in the table view forever
            self.table_model.update([[]])
        if pkt_count % 5000 == 0:
            log.info('System has been running for {}, used memory {} MB'.format(
                str(datetime.timedelta(seconds=int(time.time() - self.start_time))), get_memory_usage()))
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
        self.arbi_summary_logger.clear_data()
        self.tc_arbi_discovery.start()

    def stop(self):
        log.info('TC Tool has been stopped manually.')
        self.tc_arbi_discovery.stop()
        self.arbi_summary_logger.finish()