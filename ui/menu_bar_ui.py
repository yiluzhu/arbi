from PySide import QtGui, QtCore
from arbi.constants import ARBI_SUMMARY_HEADER, MINI_PROFIT, BOOKIE_ID_MAP
from arbi.feeds.vip.constants import ACCOUNT_MAP
from arbi.ui.engine_inspector_ui import EngineInspectorUI
from arbi.ui.constants import ENGINE_INSPECTOR_UI_REFRESH_INVERVAL


class AccountPanelUI(QtGui.QWidget):
    def __init__(self, model):
        super(AccountPanelUI, self).__init__()
        self.model = model

        send_orders_cb, exec_system_on_localhost_cb, table_view_update_cb, wait_for_vip_host_info_from_exec_sys_cb, use_parallel_computing_cb = self.get_general_components()
        vip_group_box = self.get_vip_group_box()
        yy_group_box = self.get_yy_group_box()
        profit_threshold_layout = self.get_profit_threshold_layout()
        close_button_layout = self.get_close_button_layout()

        widgets = [send_orders_cb, exec_system_on_localhost_cb, table_view_update_cb,
                   wait_for_vip_host_info_from_exec_sys_cb, use_parallel_computing_cb, vip_group_box, yy_group_box]
        layouts = [profit_threshold_layout, close_button_layout]
        overall_layout = self.get_overall_layout(widgets, layouts)

        self.setLayout(overall_layout)

        self.setWindowTitle('General Settings')

    def set_use_betfair_mock_data_cb(self, state):
        if state == QtCore.Qt.Checked:
            self.use_betfair_mock_data_cb.setEnabled(True)
        elif state == QtCore.Qt.Unchecked:
            self.use_betfair_mock_data_cb.setEnabled(False)

    def get_general_components(self):
        # send orders check box
        self.send_orders_cb = QtGui.QCheckBox('Send orders to real execution system')
        self.send_orders_cb.setChecked(True)
        # exec system at local host
        self.exec_system_on_localhost_cb = QtGui.QCheckBox('Execution system is running on local host')
        self.exec_system_on_localhost_cb.setChecked(True)
        # enable/disable table view update
        self.table_view_update_cb = QtGui.QCheckBox('Enable table view update')
        # "wait for vip ip and port from exec system" flag
        self.wait_for_vip_host_info_from_exec_sys_cb = QtGui.QCheckBox('Wait for VIP host info from execution system')
        self.wait_for_vip_host_info_from_exec_sys_cb.setChecked(True)
        # Whether to use multiprocessing to run arbitrage strategies
        self.use_parallel_computing_cb = QtGui.QCheckBox('Use parallel computing to run arbitrage strategies')

        return self.send_orders_cb, self.exec_system_on_localhost_cb, self.table_view_update_cb, self.wait_for_vip_host_info_from_exec_sys_cb, self.use_parallel_computing_cb

    def get_vip_group_box(self):
        vip_group_box = QtGui.QGroupBox('VIP Feed')
        vip_group_box_layout = QtGui.QVBoxLayout()
        # enable vip feed check box
        self.enable_vip_feed_cb = QtGui.QCheckBox('Enable VIP feed')
        self.enable_vip_feed_cb.setChecked(True)
        self.enable_vip_feed_cb.setEnabled(False)
        # save history flag check box
        self.save_vip_history_flag_cb = QtGui.QCheckBox('Save VIP data to history file')
        # use mock data check box
        self.use_vip_mock_data_cb = QtGui.QCheckBox('Use VIP mock data')
        # account index
        vip_account_index_layout = QtGui.QHBoxLayout()
        vip_account_index_layout.addWidget(QtGui.QLabel('VIP Account:'))
        self.vip_account_group = QtGui.QButtonGroup(self)
        for index in [0, 1]:
            name = ACCOUNT_MAP[index][0]
            btn = QtGui.QRadioButton(name)
            if index == 1:
                btn.setChecked(True)
            self.vip_account_group.addButton(btn, index)
            vip_account_index_layout.addWidget(btn)
        vip_group_box_layout.addWidget(self.enable_vip_feed_cb)
        vip_group_box_layout.addWidget(self.use_vip_mock_data_cb)
        vip_group_box_layout.addWidget(self.save_vip_history_flag_cb)
        vip_group_box_layout.addLayout(vip_account_index_layout)
        vip_group_box.setLayout(vip_group_box_layout)

        return vip_group_box

    def get_yy_group_box(self):
        betfair_group_box = QtGui.QGroupBox('Betfair Feed')
        betfair_group_box_layout = QtGui.QVBoxLayout()
        # save history flag check box
        self.save_betfair_history_flag_cb = QtGui.QCheckBox('Save YY data to history file')
        # use mock data check box
        self.use_betfair_mock_data_cb = QtGui.QCheckBox('Use YY mock data')
        # enable YY feed check box
        self.enable_yy_feed_cb = QtGui.QCheckBox('Enable YY feed')
        self.enable_yy_feed_cb.stateChanged.connect(self.set_use_betfair_mock_data_cb)

        self.enable_yy_feed_cb.setChecked(True)

        betfair_group_box_layout.addWidget(self.enable_yy_feed_cb)
        betfair_group_box_layout.addWidget(self.use_betfair_mock_data_cb)
        betfair_group_box_layout.addWidget(self.save_betfair_history_flag_cb)
        betfair_group_box.setLayout(betfair_group_box_layout)

        return betfair_group_box

    def get_profit_threshold_layout(self):
        profit_threshold_layout = QtGui.QHBoxLayout()
        profit_threshold_layout.addWidget(QtGui.QLabel('Set profit threshold to (default is {0}):'.format(MINI_PROFIT * 100)))
        self.profit_threshold_field = QtGui.QLineEdit()
        self.profit_threshold_field.setFixedWidth(50)
        self.profit_threshold_field.setText(str(MINI_PROFIT * 100))
        profit_threshold_layout.addWidget(self.profit_threshold_field)
        profit_threshold_layout.addWidget(QtGui.QLabel(' %'))

        return profit_threshold_layout

    def get_close_button_layout(self):
        close_button = QtGui.QPushButton('Close')
        close_button.clicked.connect(self.close)
        close_button_layout = QtGui.QHBoxLayout()
        close_button_layout.addStretch(1)
        close_button_layout.addWidget(close_button)

        return close_button_layout

    def get_overall_layout(self, widgets, layouts):
        overall_layout = QtGui.QVBoxLayout()
        for widget in widgets:
            overall_layout.addWidget(widget)
        for layout in layouts:
            overall_layout.addLayout(layout)

        return overall_layout

    def closeEvent(self, event):
        self.model.send_orders = self.send_orders_cb.isChecked()
        self.model.exec_system_on_localhost = self.exec_system_on_localhost_cb.isChecked()
        self.model.table_view_update = self.table_view_update_cb.isChecked()
        self.model.vip_account_index = self.vip_account_group.checkedId()
        self.model.wait_for_vip_host_info = self.wait_for_vip_host_info_from_exec_sys_cb.isChecked()
        self.model.use_parallel_computing = self.use_parallel_computing_cb.isChecked()

        self.set_feeds_configs()
        self.set_profit_threshold(event)

    def set_feeds_configs(self):
        self.model.vip_feed_enabled = self.enable_vip_feed_cb.isChecked()
        self.model.yy_feed_enabled = self.enable_yy_feed_cb.isChecked()
        self.model.use_vip_mock_data = self.use_vip_mock_data_cb.isChecked()
        self.model.use_betfair_mock_data = self.use_betfair_mock_data_cb.isChecked()
        self.model.save_vip_history_flag = self.save_vip_history_flag_cb.isChecked()
        self.model.save_betfair_history_flag = self.save_betfair_history_flag_cb.isChecked()

    def set_profit_threshold(self, event):
        try:
            profit_threshold = float(self.profit_threshold_field.text().strip()) / 100
        except Exception:
            msg_box = QtGui.QMessageBox()
            msg_box.setText('Invalid profit threshold: "{0}"'.format(self.profit_threshold_field.text()))
            msg_box.exec_()
            event.ignore()
        else:
            self.model.profit_threshold = profit_threshold
            event.accept()


class StratsPanelUI(QtGui.QWidget):
    def __init__(self, model):
        super(StratsPanelUI, self).__init__()
        self.model = model

        # Direct arb
        direct_arb_group_box = QtGui.QGroupBox('Direct Arb')
        direct_arb_group_box_layout = QtGui.QVBoxLayout()

        self.direct_arb_cb = QtGui.QCheckBox('Direct Arb Simple')
        self.direct_arb_cb.setChecked(self.model.use_direct_arb)
        self.direct_arb_combined_cb = QtGui.QCheckBox('Direct Arb Combined')
        self.direct_arb_combined_cb.setChecked(self.model.use_direct_arb_combined)

        direct_arb_group_box_layout.addWidget(self.direct_arb_cb)
        direct_arb_group_box_layout.addWidget(self.direct_arb_combined_cb)
        direct_arb_group_box.setLayout(direct_arb_group_box_layout)

        # Correlated arb
        correlated_arb_group_box = QtGui.QGroupBox('Correlated Arb')
        correlated_arb_group_box_layout = QtGui.QVBoxLayout()

        self.correlated_arb_AHvs2_cb = QtGui.QCheckBox('AH vs 2')
        self.correlated_arb_AHvs2_cb.setChecked(self.model.use_correlated_arb_AHvs2)
        self.correlated_arb_AHvsXvs2_cb = QtGui.QCheckBox('AH vs X vs 2')
        self.correlated_arb_AHvsXvs2_cb.setChecked(self.model.use_correlated_arb_AHvsXvs2)
        self.correlated_arb_EHvsEHXvsAH_cb = QtGui.QCheckBox('EH vs EHX vs AH')
        self.correlated_arb_EHvsEHXvsAH_cb.setChecked(self.model.use_correlated_arb_EHvsEHXvsAH)

        correlated_arb_group_box_layout.addWidget(self.correlated_arb_AHvs2_cb)
        correlated_arb_group_box_layout.addWidget(self.correlated_arb_AHvsXvs2_cb)
        correlated_arb_group_box_layout.addWidget(self.correlated_arb_EHvsEHXvsAH_cb)
        correlated_arb_group_box.setLayout(correlated_arb_group_box_layout)

        # Cross handicap arb
        self.cross_handicap_arb_cb = QtGui.QCheckBox('Cross Handicap (This is NOT risk free)')
        self.cross_handicap_arb_cb.setChecked(self.model.use_cross_handicap_arb)
        self.cross_handicap_arb_cb.stateChanged.connect(self.set_use_async_for_cross_handicap_arb_cb)
        self.use_async_for_cross_handicap_arb_cb = QtGui.QCheckBox('Run Cross Handicap Arb Strat in separate process')
        self.use_async_for_cross_handicap_arb_cb.setEnabled(self.model.use_cross_handicap_arb)
        self.use_async_for_cross_handicap_arb_cb.setChecked(self.model.use_cross_handicap_arb)

        # Close button
        close_button = QtGui.QPushButton('Close')
        close_button.clicked.connect(self.close)
        close_button_layout = QtGui.QHBoxLayout()
        close_button_layout.addStretch(1)
        close_button_layout.addWidget(close_button)

        # Overall layout
        overall_layout = QtGui.QVBoxLayout()
        overall_layout.addWidget(direct_arb_group_box)
        overall_layout.addWidget(correlated_arb_group_box)
        overall_layout.addWidget(self.cross_handicap_arb_cb)
        overall_layout.addWidget(self.use_async_for_cross_handicap_arb_cb)
        overall_layout.addLayout(close_button_layout)
        self.setLayout(overall_layout)

        self.setWindowTitle('Choose Arb Strats')

    def set_use_async_for_cross_handicap_arb_cb(self, state):
        if state == QtCore.Qt.Checked:
            self.use_async_for_cross_handicap_arb_cb.setEnabled(True)
            self.use_async_for_cross_handicap_arb_cb.setChecked(True)
        elif state == QtCore.Qt.Unchecked:
            self.use_async_for_cross_handicap_arb_cb.setEnabled(False)
            self.use_async_for_cross_handicap_arb_cb.setChecked(False)

    def closeEvent(self, event):
        self.model.use_direct_arb = self.direct_arb_cb.isChecked()
        self.model.use_direct_arb_combined = self.direct_arb_combined_cb.isChecked()
        self.model.use_correlated_arb_AHvs2 = self.correlated_arb_AHvs2_cb.isChecked()
        self.model.use_correlated_arb_AHvsXvs2 = self.correlated_arb_AHvsXvs2_cb.isChecked()
        self.model.use_correlated_arb_EHvsEHXvsAH = self.correlated_arb_EHvsEHXvsAH_cb.isChecked()
        self.model.use_cross_handicap_arb = self.cross_handicap_arb_cb.isChecked()
        self.model.use_async_for_cross_handicap_arb = self.use_async_for_cross_handicap_arb_cb.isChecked()
        event.accept()


class ColumnHidePanelUI(QtGui.QWidget):
    def __init__(self, table_view, table_view_for_history):
        super(ColumnHidePanelUI, self).__init__()
        self.table_view = table_view
        self.table_view_for_history = table_view_for_history

        # Column check boxes
        self.column_check_box_list = []
        column_cb_layout = QtGui.QVBoxLayout()
        for name in ARBI_SUMMARY_HEADER:
            check_box = QtGui.QCheckBox(name)
            check_box.setChecked(True)
            self.column_check_box_list.append(check_box)
            column_cb_layout.addWidget(check_box)

        # Close button
        close_button = QtGui.QPushButton('Close')
        close_button.clicked.connect(self.close)
        close_button_layout = QtGui.QHBoxLayout()
        close_button_layout.addStretch(1)
        close_button_layout.addWidget(close_button)

        # Overall layout
        overall_layout = QtGui.QVBoxLayout()
        overall_layout.addLayout(column_cb_layout)
        overall_layout.addLayout(close_button_layout)
        self.setLayout(overall_layout)

        self.setWindowTitle('Show/Hide Columns')

    def hide_columns(self, column_names):
        for index, check_box in enumerate(self.column_check_box_list):
            if check_box.text() in column_names:
                check_box.setChecked(False)
                self.table_view.setColumnHidden(index, not check_box.isChecked())
                self.table_view_for_history.setColumnHidden(index, not check_box.isChecked())

    def closeEvent(self, event):
        for index, check_box in enumerate(self.column_check_box_list):
            self.table_view.setColumnHidden(index, not check_box.isChecked())
            self.table_view_for_history.setColumnHidden(index, not check_box.isChecked())

        event.accept()


class FilterPanelUI(QtGui.QWidget):
    def __init__(self, model):
        super(FilterPanelUI, self).__init__()

        self.model = model

        # Bookie filter
        self.bookie_check_box_list = []
        bookie_filter_layout = QtGui.QVBoxLayout()
        for name in sorted(BOOKIE_ID_MAP.values()):
            check_box = QtGui.QCheckBox(name)
            check_box.setChecked(True)
            self.bookie_check_box_list.append(check_box)
            bookie_filter_layout.addWidget(check_box)
        self.model.set_filtered_bookies(self.bookie_check_box_list)

        bookie_filter_group = QtGui.QGroupBox("Filtered Bookies(tick to keep)")
        bookie_filter_group.setLayout(bookie_filter_layout)

        # Team filter
        league_filter_label = QtGui.QLabel('Filtered Leagues(name to keep, blank to keep all): ')
        self.league_filter_edit = QtGui.QPlainTextEdit()
        league_filter_layout = QtGui.QVBoxLayout()
        league_filter_layout.addWidget(league_filter_label)
        league_filter_layout.addWidget(self.league_filter_edit)

        # Team filter
        team_filter_label = QtGui.QLabel('Filtered Teams(name to keep, blank to keep all): ')
        self.team_filter_edit = QtGui.QPlainTextEdit()
        team_filter_layout = QtGui.QVBoxLayout()
        team_filter_layout.addWidget(team_filter_label)
        team_filter_layout.addWidget(self.team_filter_edit)

        # Close button
        close_button = QtGui.QPushButton('Close')
        close_button.clicked.connect(self.close)
        close_button_layout = QtGui.QHBoxLayout()
        close_button_layout.addStretch(1)
        close_button_layout.addWidget(close_button)

        # Filter panel layout
        filter_panel_layout = QtGui.QHBoxLayout()
        filter_panel_layout.addWidget(bookie_filter_group)
        filter_panel_layout.addLayout(league_filter_layout)
        filter_panel_layout.addLayout(team_filter_layout)

        # Overall layout
        overall_layout = QtGui.QVBoxLayout()
        overall_layout.addLayout(filter_panel_layout)
        overall_layout.addLayout(close_button_layout)
        self.setLayout(overall_layout)

        self.setWindowTitle('Edit Filters')

    def closeEvent(self, event):
        self.model.set_filtered_bookies(self.bookie_check_box_list)
        self.model.set_filtered_leagues(self.league_filter_edit.toPlainText())
        self.model.set_filtered_teams(self.team_filter_edit.toPlainText())
        event.accept()


class MenuBarUI(QtGui.QMenuBar):
    def __init__(self, arbi_pro_model, table_view, table_view_for_history, account_panel_ui_class=AccountPanelUI):
        super(MenuBarUI, self).__init__()

        # Settings
        change_filter_action = QtGui.QAction('&Edit Filters', self)
        change_filter_action.triggered.connect(self.change_filter)
        change_filter_action.setDisabled(True)

        hide_column_action = QtGui.QAction('&Hide Columns', self)
        hide_column_action.triggered.connect(self.choose_columns)

        choose_account_action = QtGui.QAction('&General Settings', self)
        choose_account_action.triggered.connect(self.choose_account)

        choose_strats_action = QtGui.QAction('&Arb Strats', self)
        choose_strats_action.triggered.connect(self.choose_strats)

        settings_menu = self.addMenu('&Settings')
        settings_menu.addAction(choose_account_action)
        settings_menu.addAction(choose_strats_action)
        settings_menu.addAction(change_filter_action)
        settings_menu.addAction(hide_column_action)

        self.account_panel = account_panel_ui_class(arbi_pro_model.menu_bar_model.account_model)
        self.filter_panel = FilterPanelUI(arbi_pro_model.menu_bar_model.filter_panel_model)
        self.column_hide_panel = ColumnHidePanelUI(table_view, table_view_for_history)
        self.strats_panel = StratsPanelUI(arbi_pro_model.menu_bar_model.strats_panel_model)

        # Tools
        run_engine_inspector_action = QtGui.QAction('&Engine Inspector', self)
        run_engine_inspector_action.triggered.connect(self.run_engine_inspector)
        tools_menu = self.addMenu('&Tools')
        tools_menu.addAction(run_engine_inspector_action)

        self.engine_inspector_panel = EngineInspectorUI(arbi_pro_model.engine_table_model)

        self.show()

    def hide_columns(self, column_names):
        self.column_hide_panel.hide_columns(column_names)

    def run_engine_inspector(self):
        self.engine_inspector_panel.show()
        engine_inspector_panel_timer_id = self.engine_inspector_panel.startTimer(1000 * ENGINE_INSPECTOR_UI_REFRESH_INVERVAL)
        self.engine_inspector_panel.set_timer_id(engine_inspector_panel_timer_id)

    def choose_account(self):
        self.account_panel.show()

    def choose_strats(self):
        self.strats_panel.show()

    def change_filter(self):
        self.filter_panel.show()

    def choose_columns(self):
        self.column_hide_panel.show()

    def closeEvent(self, event):
        try:
            self.engine_inspector_panel.close()
        except:
            pass

        event.accept()
