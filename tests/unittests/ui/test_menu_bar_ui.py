from mock import patch, Mock
from unittest2 import TestCase
from PySide import QtGui
from arbi.ui.menu_bar_ui import MenuBarUI, AccountPanelUI
from arbi.ui_models.menu_bar_model import MenuBarModel, AccountModel
from arbi.ui_models.engine_inspector_model import DataEngineTableModel
from arbi.tests.utils import set_qapp


class MenuBarUITest(TestCase):
    @classmethod
    def setUpClass(cls):
        set_qapp()

    def test_MenuBarUI(self):
        arbi_pro_model = Mock()
        arbi_pro_model.menu_bar_model = MenuBarModel()
        arbi_pro_model.engine_table_model = DataEngineTableModel(None, [])
        table_view = QtGui.QTableView()
        table_view_for_history = QtGui.QTableView()
        menu_bar_ui = MenuBarUI(arbi_pro_model, table_view, table_view_for_history)

        menu_bar_ui.choose_account()
        menu_bar_ui.account_panel.close()

        menu_bar_ui.choose_strats()
        menu_bar_ui.strats_panel.close()

        menu_bar_ui.change_filter()
        menu_bar_ui.filter_panel.close()

        menu_bar_ui.choose_columns()
        menu_bar_ui.column_hide_panel.close()

    def test_AccountPanelUI(self):
        account_panel_ui = AccountPanelUI(AccountModel())
        account_panel_ui.profit_threshold_field.setText('non-float')
        with patch('arbi.ui.menu_bar_ui.QtGui.QMessageBox'):
            account_panel_ui.close()
