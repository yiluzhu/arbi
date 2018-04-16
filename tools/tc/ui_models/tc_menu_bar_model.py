from arbi.constants import MINI_PROFIT
from arbi.feeds.vip.constants import HOSTS, PORTS
from arbi.feeds.betfair.constants import BETFAIR_FEED_IP, BETFAIR_FEED_PORT
from arbi.ui_models.menu_bar_model import FilterPanelModel
from arbi.strats.correlated_arbi import AHvsXvs2Strategy, AHvs2Strategy
from arbi.strats.correlated_arbi_eh import EHvsEHXvsAHStrategy
from arbi.strats.direct_arbi_combined import DirectArbiCombinedStrategy
from arbi.strats.cross_handicap_arbi import CrossHandicapArbiStrategy
from arbi.tools.tc.strats.tc_direct_arbi import TCDirectArbiStrategy

class TCStratsPanelModel(object):
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
            (TCDirectArbiStrategy, self.use_direct_arb),
            (DirectArbiCombinedStrategy, self.use_direct_arb_combined),
            (AHvsXvs2Strategy, self.use_correlated_arb_AHvsXvs2),
            (AHvs2Strategy, self.use_correlated_arb_AHvs2),
            (EHvsEHXvsAHStrategy, self.use_correlated_arb_EHvsEHXvsAH),
            (CrossHandicapArbiStrategy, self.use_cross_handicap_arb),
        ]
        return [key for key, value in flag_map if value]


class TCMenuBarModel(object):
    def __init__(self):
        self.filter_panel_model = FilterPanelModel()
        self.account_model = TCAccountModel()
        self.strats_panel_model = TCStratsPanelModel()


class TCAccountModel(object):
    def __init__(self):
        self.vip_feed_enabled = True
        self.yy_feed_enabled = True
        self.use_vip_mock_data = False
        self.use_betfair_mock_data = False
        self.use_sporttery_mock_data = False
        self.vip_mock_data_pkg_num = 'tc_tool_manual_test_with_timestamp'
        self.betfair_mock_data_pkg_num = 'tc_tool_manual_test_with_timestamp'
        self.profit_threshold = MINI_PROFIT
        self.save_vip_history_flag = False
        self.save_betfair_history_flag = False

        self.vip_ip = HOSTS[0]
        self.vip_port = PORTS[0]
        self.yy_ip = BETFAIR_FEED_IP
        self.yy_port = BETFAIR_FEED_PORT

        self.use_parallel_computing = False
