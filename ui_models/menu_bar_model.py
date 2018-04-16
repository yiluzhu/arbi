from arbi.constants import MINI_PROFIT
from arbi.feeds.vip.constants import HOSTS, PORTS
from arbi.feeds.betfair.constants import BETFAIR_FEED_IP, BETFAIR_FEED_PORT
from arbi.strats.correlated_arbi import AHvsXvs2Strategy, AHvs2Strategy
from arbi.strats.correlated_arbi_eh import EHvsEHXvsAHStrategy
from arbi.strats.direct_arbi import DirectArbiStrategy
from arbi.strats.direct_arbi_combined import DirectArbiCombinedStrategy
from arbi.strats.cross_handicap_arbi import CrossHandicapArbiStrategy


class MenuBarModel(object):
    def __init__(self):
        self.filter_panel_model = FilterPanelModel()
        self.account_model = AccountModel()
        self.strats_panel_model = StratsPanelModel()


class StratsPanelModel(object):
    def __init__(self):
        self.use_direct_arb = True
        self.use_direct_arb_combined = False
        self.use_correlated_arb_AHvs2 = True
        self.use_correlated_arb_AHvsXvs2 = True
        self.use_correlated_arb_EHvsEHXvsAH = False
        self.use_cross_handicap_arb = False
        self.use_async_for_cross_handicap_arb = True

    def get_enabled_strats(self):
        flag_map = [
            (DirectArbiStrategy, self.use_direct_arb),
            (DirectArbiCombinedStrategy, self.use_direct_arb_combined),
            (AHvsXvs2Strategy, self.use_correlated_arb_AHvsXvs2),
            (AHvs2Strategy, self.use_correlated_arb_AHvs2),
            (EHvsEHXvsAHStrategy, self.use_correlated_arb_EHvsEHXvsAH),
            (CrossHandicapArbiStrategy, self.use_cross_handicap_arb),
        ]
        return [key for key, value in flag_map if value]


class AccountModel(object):
    def __init__(self):
        self.vip_feed_enabled = True
        self.yy_feed_enabled = True
        self.use_vip_mock_data = False
        self.use_betfair_mock_data = False
        self.send_orders = True
        self.exec_system_on_localhost = True
        self.table_view_update = False
        self.vip_mock_data_pkg_num = 'packets2000with_timestamp_100ms'
        self.betfair_mock_data_pkg_num = 'packets2000with_timestamp_100ms'
        self.vip_account_index = 1
        self.wait_for_vip_host_info = True
        self.profit_threshold = MINI_PROFIT
        self.save_vip_history_flag = False
        self.save_betfair_history_flag = False

        self.vip_ip = HOSTS[0]
        self.vip_port = PORTS[0]
        self.yy_ip = BETFAIR_FEED_IP
        self.yy_port = BETFAIR_FEED_PORT

        self.use_parallel_computing = False


class FilterPanelModel(object):
    def __init__(self):
        self.filtered_bookies = []
        self.filtered_leagues = []
        self.filtered_teams = []

    def set_filtered_bookies(self, bookie_check_box_list):
        self.filtered_bookies = [check_box.text() for check_box in bookie_check_box_list if check_box.isChecked()]

    def set_filtered_leagues(self, text):
        self.filtered_leagues = [name.strip() for name in text.splitlines() if name.strip()]

    def set_filtered_teams(self, text):
        self.filtered_teams = [name.strip() for name in text.splitlines() if name.strip()]
