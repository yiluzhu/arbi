"""
Entrance to run the app
"""
import os
import datetime
import logging
from PySide.QtGui import QApplication

from arbi.ui.arbi_pro_ui import ArbiProView
from arbi.arbi_pro import ArbiProModel
from arbi.constants import ROOT_PATH, VERSION


def setup_local_logfile():
    path = os.path.join(ROOT_PATH, 'logs')
    if not os.path.exists(path):
        os.mkdir(path)
    log_file_name = 'main_log_{0}.log'.format(datetime.datetime.utcnow().strftime('%Y%m%d_%H-%M-%S'))
    logging.basicConfig(filename=os.path.join(path, log_file_name),
                        level=logging.INFO,
                        format='%(asctime)s %(message)s')


class ArbiProApp(object):
    """Wrapper to bind ArbiProModel and ArbiProView together"""
    def __init__(self):
        QApplication.setStyle('Plastique')
        self.qt_app = QApplication([])
        model = ArbiProModel()
        self.view = ArbiProView(model)
        self.view.initialize_view(model.table_model, model.table_model_for_history, VERSION)

    def run(self):
        self.view.show()
        self.qt_app.exec_()


if __name__ == '__main__':
    setup_local_logfile()
    app = ArbiProApp()
    app.run()
