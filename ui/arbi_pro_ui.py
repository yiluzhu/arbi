"""
Main UI
"""
from PySide.QtCore import Qt
from PySide.QtGui import QTableView, QVBoxLayout, QHBoxLayout, QMainWindow, QPushButton, QFrame, QLabel, QWidget, QLayout
from arbi.feeds.vip.constants import ACCOUNT_MAP
from arbi.feeds.betfair.constants import BETFAIR_USERNAME
from arbi.ui.menu_bar_ui import MenuBarUI
from arbi.constants import SCREEN_SIZE_SMALL, SCREEN_SIZE, ARBI_SUMMARY_HEADER, DEFAULT_COLUMN_WIDTH, COLUMN_WIDTH_DICT
from arbi.constants import HIDDEN_COLUMNS


class BaseView(QMainWindow):

    def __init__(self, model):
        super(BaseView, self).__init__()
        self.model = model
        self.model.view_signal.historic_opps_count.connect(self.update_historic_opps_count)

    def initialize_table_views(self, table_model, table_model_for_history):
        # Table view for real time opportunities
        table_view = QTableView()
        table_view.setModel(table_model)
        table_view.setSortingEnabled(True)
        self.set_table_view_column_width(table_view)

        # Table view for real time opportunities
        table_view_for_history = QTableView()
        table_view_for_history.setModel(table_model_for_history)
        table_view_for_history.setSortingEnabled(True)
        self.set_table_view_column_width(table_view_for_history)

        return table_view, table_view_for_history

    def create_historic_opps_panel(self):
        self.historic_opps_count = QLabel('0')
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Historic Opportunities:'))
        layout.addStretch()
        layout.addWidget(self.historic_opps_count)
        layout.addWidget(QLabel(' rows in total'))
        return layout

    def create_buttons(self):
        # Start and Stop button
        self.start_button = QPushButton('START')
        self.start_button.clicked.connect(self.start)
        self.stop_button = QPushButton('STOP')
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        button_layout.addStretch()
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()

        return button_layout

    def initialize_view(self, table_model, table_model_for_history, version):
        raise NotImplementedError

    def set_menu_bar(self, table_view, table_view_for_history):
        raise NotImplementedError

    def create_layout(self, *args):
        main_layout = QVBoxLayout()
        for item in args:
            if isinstance(item, QWidget):
                main_layout.addWidget(item)
            elif isinstance(item, QLayout):
                main_layout.addLayout(item)

        return main_layout

    def set_layout(self, layout, title, screen_size):
        frame = QFrame()
        frame.setLayout(layout)
        self.setCentralWidget(frame)

        self.setWindowTitle(title)
        self.resize(*screen_size)
        self.move(0, 0)

    def set_table_view_column_width(self, table_view):
        for header in ARBI_SUMMARY_HEADER:
            idx = ARBI_SUMMARY_HEADER.index(header)
            width = COLUMN_WIDTH_DICT.get(header.strip('123'), DEFAULT_COLUMN_WIDTH)
            table_view.setColumnWidth(idx, width)

    def update_historic_opps_count(self, count):
        self.historic_opps_count.setText(str(count))

    def start(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.model.start()

    def stop(self):
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.model.stop()

    def closeEvent(self, event):
        try:
            self.stop()
        except:
            pass

        self.menuBar().close()
        event.accept()


class ArbiProView(BaseView):

    def __init__(self, model):
        super(ArbiProView, self).__init__(model)
        self.model.view_signal.update_vip_host_display.connect(self.update_vip_host_address_display)
        self.model.view_signal.update_yy_host_display.connect(self.update_yy_host_address_display)

    def initialize_view(self, table_model, table_model_for_history, version):
        table_view, table_view_for_history = self.initialize_table_views(table_model, table_model_for_history)
        self.set_menu_bar(table_view, table_view_for_history)

        historic_opps_layout = self.create_historic_opps_panel()
        info_layout = self.create_info_panel()
        button_layout = self.create_buttons()

        layout = self.create_layout(historic_opps_layout, table_view_for_history,
                                    QLabel('Real time Opportunities:'), table_view, info_layout, button_layout)
        self.set_layout(layout, 'ArbiPro {0}'.format(version), SCREEN_SIZE)

    def set_menu_bar(self, table_view, table_view_for_history):
        menu_bar = MenuBarUI(self.model, table_view, table_view_for_history)
        menu_bar.hide_columns(HIDDEN_COLUMNS)
        self.setMenuBar(menu_bar)

    def create_info_panel(self):
        self.vip_account_info = QLabel()
        self.vip_ip_port_info = QLabel()
        self.vip_ip_port_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.yy_account_info = QLabel()
        self.yy_ip_port_info = QLabel()
        self.yy_ip_port_info.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.refresh_text_for_info_panel()

        info_layout = QVBoxLayout()
        for account_info, ip_port_info in [(self.vip_account_info, self.vip_ip_port_info),
                                           (self.yy_account_info, self.yy_ip_port_info)]:
            sub_info_layout = QHBoxLayout()
            sub_info_layout.addWidget(account_info)
            sub_info_layout.addStretch()
            sub_info_layout.addWidget(ip_port_info)
            info_layout.addLayout(sub_info_layout)

        return info_layout

    def refresh_text_for_info_panel(self):
        model = self.model.menu_bar_model.account_model
        self.vip_account_info.setText('VIP Account ID: {}'.format(ACCOUNT_MAP[model.vip_account_index][0]))
        self.vip_ip_port_info.setText('VIP Server Address: {}:{}'.format(model.vip_ip, model.vip_port))
        self.yy_account_info.setText('YY Account ID: {}'.format(BETFAIR_USERNAME))
        self.yy_ip_port_info.setText('YY Server Address: {}:{}'.format(model.yy_ip, model.yy_port))

    def update_vip_host_address_display(self, ip_and_port_str):
        self.vip_ip_port_info.setText('VIP Server Address: {}'.format(ip_and_port_str))

    def update_yy_host_address_display(self, ip_and_port_str):
        self.yy_ip_port_info.setText('YY Server Address: {}'.format(ip_and_port_str))

    def start(self):
        self.refresh_text_for_info_panel()
        super(ArbiProView, self).start()
