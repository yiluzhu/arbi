"""
This script runs analytic system. You must run mock_exec_system.py first before run this script.
"""

import time
from arbi.arbi_pro import ArbiProModel


def run_analytic_system():
    app = ArbiProModel()
    app.arbi_discovery.check_vip_thread_alive_if_it_is_time = lambda: None

    config = app.menu_bar_model.account_model
    config.use_vip_mock_data = True
    config.use_betfair_mock_data = True
    config.send_orders = True
    config.exec_system_on_localhost = True
    config.table_view_update = True
    config.vip_mock_data_pkg_num = 'with_timestamp/2015-10-24 201054_1minutes'
    config.betfair_mock_data_pkg_num = None
    config.wait_for_vip_host_info = False
    config.profit_threshold = 0.01
    config.save_vip_history_flag = False
    config.save_betfair_history_flag = False

    app.start()
    time.sleep(5)
    while True:
        time.sleep(1)
        # hk_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        # for match_id, match in app.engine.match_dict.iteritems():
        #     print hk_time, match_id, match.info['home_team_score'], match.info['away_team_score']

        if not app.arbi_discovery.vip_feed_thread.thread.is_alive():
            app.arbi_discovery.break_loop_count = 2
        if not app.arbi_discovery.isRunning():
            app.stop()
            time.sleep(1)
            break


if __name__ == '__main__':
    run_analytic_system()
