from mock import patch
from unittest2 import TestCase, main
from arbi.main import ArbiProApp, setup_local_logfile


class SummaryTableModelTest(TestCase):
    def test(self):
        app = ArbiProApp()
        setup_local_logfile()


# if __name__ == '__main__':
#     main()