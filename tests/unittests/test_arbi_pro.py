import time
from mock import Mock
from unittest2 import TestCase
from arbi.arbi_pro import ArbiProModel


class ArbiProModelTest(TestCase):

    # def test(self):
    #     model = ArbiProModel()
    #     model.arbi_discovery = Mock()
    #     model.menu_bar_model.account_model.send_orders = False
    #
    #     model.start()
    #     model.process_arbi_opps((100, []))
    #     model.process_arbi_opps((time.time(), 'OK'))
    #     model.pkt_count = 100000000
    #     model.init_finished_time = 1430000000
    #     model.post_work()

    def test_update_pkt_count(self):
        model = ArbiProModel()
        model.start_time = 1430000000
        model.update_pkt_count((100, 5.5))
        model.update_pkt_count((2000, 10.5))

    def test_start_with_exception(self):
        model = ArbiProModel()
        model.arbi_discovery = Mock()

        model.start()
        model.arbi_discovery.start.assert_not_called()

    def test_stop(self):
        model = ArbiProModel()
        model.arbi_discovery = Mock()
        model.stop()

        model.arbi_discovery.stop.assert_called_once_with()
