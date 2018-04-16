from mock import Mock
from unittest2 import TestCase
from arbi.ui.arbi_pro_ui import ArbiProView
from arbi.ui_models.engine_inspector_model import DataEngineTableModel
from arbi.ui_models.menu_bar_model import StratsPanelModel
from arbi.tests.utils import set_qapp


class ArbiProUITest(TestCase):
    @classmethod
    def setUpClass(cls):
        set_qapp()

    # def test_TimedMsgBox(self):
    #     TimedMsgBox(timeout=1).exec_()

    def test_ArbiProView(self):
        model = Mock()
        model.menu_bar_model.account_model.vip_account_index = 0
        model.menu_bar_model.account_model.vip_ip = '12.34.56.78'
        model.menu_bar_model.account_model.vip_port = 12345
        model.menu_bar_model.strats_panel_model = StratsPanelModel()
        model.engine_table_model = DataEngineTableModel(None, [])

        view = ArbiProView(model)
        view.initialize_view(None, None, '')
        view.start()
        view.stop()
