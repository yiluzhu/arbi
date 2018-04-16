"""
TC stands for Ti Cai Wang(www.sporttery.cn/). We use TC Tool to discover opportunities between sporttery and other bookies.
Because sporttery has basketball, TC tool can do basketball too.
"""
import os
import datetime
import logging
from PySide.QtGui import QApplication

from arbi.constants import ROOT_PATH
from arbi.tools.tc.ui.tc_view import TCView
from arbi.tools.tc.tc_model import TCModel
from arbi.tools.tc.constants import TC_TOOL_VER


def setup_local_logfile():
    path = os.path.join(ROOT_PATH, 'logs')
    if not os.path.exists(path):
        os.mkdir(path)
    log_file_name = 'tc_log_{0}.log'.format(datetime.datetime.utcnow().strftime('%Y%m%d_%H-%M-%S'))
    logging.basicConfig(filename=os.path.join(path, log_file_name),
                        level=logging.INFO,
                        format='%(asctime)s %(message)s')


class TCApp(object):
    def __init__(self):
        QApplication.setStyle('Plastique')
        self.qt_app = QApplication([])
        model = TCModel()
        self.view = TCView(model)
        self.view.initialize_view(model.table_model, model.table_model_for_history, TC_TOOL_VER)

    def run(self):
        self.view.show()
        self.qt_app.exec_()


if __name__ == '__main__':
    setup_local_logfile()
    app = TCApp()
    app.run()
