import mock
import time
import datetime
from Queue import Queue
from unittest2 import TestCase
from arbi.models.engine import DataEngine
from arbi.execution.arbi_exec import ExecMsgerConnectionError, ArbiExecMessenger, MockMessenger
from arbi.models.arbi_spotter import ArbiSpotter
from arbi.arbi_discovery import ArbiDiscoveryThread


class ArbiDiscoveryTest(TestCase):
    def setUp(self):
        mock_account_model = mock.Mock()
        mock_account_model.use_vip_mock_data = True
        mock_account_model.send_orders = False
        mock_account_model.exec_system_on_localhost = False
        mock_account_model.wait_for_vip_host_info = False
        mock_account_model.save_vip_history_flag = False
        mock_account_model.save_betfair_history_flag = False
        mock_account_model.vip_mock_data_pkg_num = '_test1'
        mock_account_model.betfair_mock_data_pkg_num = '_test1'
        mock_account_model.vip_account_index = 99
        mock_account_model.profit_threshold = 0.01
        self.menu_bar_model = mock.Mock()
        self.menu_bar_model.account_model = mock_account_model

        self.occur_at_utc = datetime.datetime(2015, 4, 15, 20, 35, 22, 1000)

        self.engine = DataEngine()
        self.arbi_spotter = ArbiSpotter(self.engine.match_dict)
        self.arbi_spotter.initialize_strats()

    def test(self):
        def mock_run_exec_msger_thread():
            arbi_discovery.exec_msger_thread = mock.Mock()

        arbi_discovery = ArbiDiscoveryThread(self.engine, self.arbi_spotter, self.menu_bar_model)
        arbi_discovery.run_exec_msger_thread = mock_run_exec_msger_thread
        arbi_discovery.signal_table_view_update = lambda x: None
        arbi_discovery.exec_msger_queue = Queue()
        arbi_discovery.break_loop_count = 2

        arbi_discovery.run()

        arbi_discovery.exec_msger_thread.exec_messenger.send.assert_called_with(mock.ANY)

    def test2(self):
        arbi_discovery = ArbiDiscoveryThread(self.engine, self.arbi_spotter, self.menu_bar_model)
        arbi_discovery.signal_table_view_update = lambda x: None

        arbi_discovery.break_loop_count = 2

        arbi_discovery.run()

    def test_normal_run(self):
        self.menu_bar_model.account_model.vip_mock_data_pkg_num = '2000'

        arbi_discovery = ArbiDiscoveryThread(self.engine, self.arbi_spotter, self.menu_bar_model)
        arbi_discovery.signal_table_view_update = lambda x: None

        arbi_discovery.break_loop_count = 10

        with mock.patch('arbi.arbi_discovery.HEARTBEAT_INTERVAL', 0.5):
            arbi_discovery.run()

    def test_betfair_back_and_AH(self):
        # vip data: sbo 2.06, 1.86,
        #           ibc 2.02, 1.90
        # betfair data: back 1.92, 2.02,
        #                lay 2.00, 2.08
        self.menu_bar_model.account_model.vip_mock_data_pkg_num = '_betfair_test'
        self.menu_bar_model.account_model.betfair_mock_data_pkg_num = '_betfair_test'

        arbi_discovery = ArbiDiscoveryThread(self.engine, self.arbi_spotter, self.menu_bar_model)
        arbi_discovery.signal_table_view_update = lambda x: None

        arbi_discovery.break_loop_count = 10

        with mock.patch.object(MockMessenger, 'write') as mock_write:
            arbi_discovery.run()
        mock_write.assert_called_once_with(mock.ANY)

    def test_restart_exec_thread(self):
        self.menu_bar_model.account_model.vip_mock_data_pkg_num = '2000'

        arbi_discovery = ArbiDiscoveryThread(self.engine, self.arbi_spotter, self.menu_bar_model)
        arbi_discovery.signal_table_view_update = lambda x: None

        arbi_discovery.break_loop_count = 20
        patch1 = mock.patch('arbi.execution.arbi_exec.MockMessenger', MockMessengerForReconnection)
        patch2 = mock.patch('arbi.arbi_discovery.EXEC_RECONNECT_DELAY', 1)
        patch3 = mock.patch('arbi.arbi_discovery.EMPTY_SRC_Q_SLEEP_TIME', 0.1)
        with patch1, patch2, patch3:
            arbi_discovery.run()


class MockMessengerForReconnection(ArbiExecMessenger):
    def __init__(self, *args, **kwargs):
        super(MockMessengerForReconnection, self).__init__(*args, **kwargs)
        self.counter = 0

    def __del__(self):
        pass

    def login(self, username, password, version):
        return True

    def write(self, text):
        pass

    def _connect(self):
        pass

    def read_exec_msg(self):
        while True:
            time.sleep(0.5)
            self.counter += 1
            if self.counter == 5:
                raise ExecMsgerConnectionError
            else:
                return []
