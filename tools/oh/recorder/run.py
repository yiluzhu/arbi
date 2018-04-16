"""Run OH recorder which saves odds history into database."""

import os
import datetime
import logging
import argparse

from arbi.tools.oh.recorder.oh_engine import OHEngine
from arbi.constants import ROOT_PATH


def setup_local_logfile():
    path = os.path.join(ROOT_PATH, 'logs')
    if not os.path.exists(path):
        os.mkdir(path)
    log_file_name = 'oh_recorder_log_{0}.log'.format(datetime.datetime.utcnow().strftime('%Y%m%d_%H-%M-%S'))
    logging.basicConfig(filename=os.path.join(path, log_file_name),
                        level=logging.INFO,
                        format='%(asctime)s %(message)s')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OH recorder')
    parser.add_argument('-x', '--use_vip_mock_data', action='store_true', help='Use mock data for VIP feed')
    parser.add_argument('-y', '--use_yy_mock_data', action='store_true', help='Use mock data for YY feed')
    parser.add_argument('-m', '--use_mock_mongodb', action='store_true', help='Use mock mongodb client')
    parser.add_argument('-d', '--disable_yy_feed', action='store_true', help='Disable YY feed')
    args = parser.parse_args()

    settings = {
        'use_vip_mock_data': args.use_vip_mock_data,
        'use_yy_mock_data': args.use_yy_mock_data,
        'use_mock_mongodb': args.use_mock_mongodb,
        'disable_yy_feed': args.disable_yy_feed,
    }
    setup_local_logfile()

    engine = OHEngine(settings)
    engine.run()
