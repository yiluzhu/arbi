import re
from PySide import QtGui
from arbi.feeds.vip.constants import HOSTS, PORTS
from arbi.ui.menu_bar_ui import AccountPanelUI


class TCAccountPanelUI(AccountPanelUI):
    def __init__(self, model):
        super(AccountPanelUI, self).__init__()
        self.model = model

        vip_group_box = self.get_vip_group_box()
        yy_group_box = self.get_yy_group_box()
        sporttery_group_box = self.get_sporttery_group_box()
        profit_threshold_layout = self.get_profit_threshold_layout()
        close_button_layout = self.get_close_button_layout()

        widgets = [vip_group_box, yy_group_box, sporttery_group_box]
        layouts = [profit_threshold_layout, close_button_layout]
        overall_layout = self.get_overall_layout(widgets, layouts)

        self.setLayout(overall_layout)

        self.setWindowTitle('General Settings')

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

        # vip server ip and port
        self.vip_ip_and_port_edit = QtGui.QLineEdit()
        self.vip_ip_and_port_edit.setText('{}:{}'.format(HOSTS[0], PORTS[0]))

        vip_group_box_layout.addWidget(self.enable_vip_feed_cb)
        vip_group_box_layout.addWidget(self.use_vip_mock_data_cb)
        vip_group_box_layout.addWidget(self.save_vip_history_flag_cb)
        vip_group_box_layout.addWidget(QtGui.QLabel('VIP Server IP and Port:'))
        vip_group_box_layout.addWidget(self.vip_ip_and_port_edit)
        vip_group_box.setLayout(vip_group_box_layout)

        return vip_group_box

    def get_sporttery_group_box(self):
        sporttery_group_box = QtGui.QGroupBox('Sporttery Feed')
        sporttery_group_box_layout = QtGui.QVBoxLayout()
        # use mock data check box
        self.use_sporttery_mock_data_cb = QtGui.QCheckBox('Use Sporttery Mock Data')
        sporttery_group_box_layout.addWidget(self.use_sporttery_mock_data_cb)
        sporttery_group_box.setLayout(sporttery_group_box_layout)

        return sporttery_group_box

    def closeEvent(self, event):
        self.model.use_sporttery_mock_data = self.use_sporttery_mock_data_cb.isChecked()

        self.set_feeds_configs()
        self.set_profit_threshold(event)

        ip_and_port_match_obj = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})',
                                         self.vip_ip_and_port_edit.text().strip())
        if ip_and_port_match_obj:
            self.model.vip_ip = ip_and_port_match_obj.groups()[0]
            self.model.vip_port = int(ip_and_port_match_obj.groups()[1])
            event.accept()
        else:
            msg_box = QtGui.QMessageBox()
            msg_box.setText('Invalid VIP server IP and Port: "{0}"'.format(self.vip_ip_and_port_edit.text()))
            msg_box.exec_()
            event.ignore()
