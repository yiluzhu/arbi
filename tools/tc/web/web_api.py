import time
import logging
import requests
from importlib import import_module
from arbi.tools.tc.constants import VIP_MATCH_ID_MAPPING_BASE_URL


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

logging.getLogger('requests').setLevel(logging.WARNING)

LOG_FREQUENCY = 60 * 10


class VIPMatchMappingAPI(object):
    def __init__(self):
        self.vip_match_id_mapping_base_url = VIP_MATCH_ID_MAPPING_BASE_URL
        self.mock_request = False
        self.log_frequency_ts = 0

    def set_mock_request_flag(self):
        self.mock_request = True

    @staticmethod
    def process_sporttery_data(sporttery_data):
        params_list = []
        odds_dict_list = []
        for match_hk_time, league, home, away, odds_dict in sporttery_data:
            params_list.append(','.join([home, away, match_hk_time]))
            odds_dict_list.append(odds_dict)

        params = ';'.join(params_list)
        return params, odds_dict_list

    @staticmethod
    def _request(url, params):
        try:
            resp = requests.post(url, data={'params': params})
        except Exception as e:
            log.warning('Connection to vip match id mapping API closed: {}'.format(e))
        else:
            if resp.ok:
                return resp.json()

    def validate_api_response_data(self, data, params):
        if data is None:
            return False
        elif data and data['matchCount'] == 0:
            if data['Result'] == 'Error':
                log.error('Error when matching from VIP match ID API for: {}'.format(params.encode('utf8')))
            else:
                log.warning('No info found from VIP match ID API for: {}'.format(params.encode('utf8')))
            return False
        else:
            return True

    def map_sporttery_data(self, sporttery_data):
        params, odds_dict_list = self.process_sporttery_data(sporttery_data)

        if self.mock_request:
            url = self.vip_match_id_mapping_base_url + '?params=' + params
            data = self.load_mocked_vip_match_mapping_data(url.encode('utf8'))
        else:
            data = self._request(self.vip_match_id_mapping_base_url, params)

        if not self.validate_api_response_data(data, params):
            return []

        t = time.time()
        if t - self.log_frequency_ts > LOG_FREQUENCY:
            log_flag = True
            self.log_frequency_ts = t
        else:
            log_flag = False

        match_id_list = []
        for i, item in enumerate(data['Result']):
            info = item['matchInfo']
            if info:
                match_id_list.append(item['matchInfo'][0]['VIPmatchID'])
            else:
                match_hk_time, league, home, away = sporttery_data[i][:4]
                if log_flag:
                    log.warning(u'No VIP match ID found for match: {}, {}, {} vs {}'.format(league, match_hk_time, home, away))
                match_id_list.append('')

        assert len(match_id_list) == len(odds_dict_list)
        return [(match_id, odds_dict) for match_id, odds_dict in zip(match_id_list, odds_dict_list) if match_id]

    @staticmethod
    def load_mocked_vip_match_mapping_data(url):
        log.info('Use mock data for VIPMatchMappingAPI request.')
        odds_module_path = 'arbi.mock_data.sporttery.vip_match_mapping_api'
        module = import_module(odds_module_path)
        mock_data = module.mapping_data[url]
        return mock_data
