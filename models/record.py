"""
One record is a line that ends with \n
"""
import logging
import datetime
from arbi.constants import MAX_ODDS
from arbi.models.data_utils import is_match_basketball


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class IncorrectLengthRecord(Exception):
    """The record has unexpected number of fields
    """


class UnknownValueRecord(Exception):
    """The record has fields with unknown values
    """


class Record(object):
    keys = []

    def __init__(self, record_str):
        self.record_str = record_str.decode('gbk')
        record_list = self.record_str[1:].split('|')
        record_list = self.validate_record_format(record_list)
        self.record_dict = {k: v for k, v in zip(self.keys, record_list)}
        self.timestamp = datetime.datetime.utcnow() + datetime.timedelta(hours=8)  # when we received the record in HK time

    def validate_record_format(self, record_list):
        if len(record_list) != len(self.keys):
            raise IncorrectLengthRecord(
                    'Incorrect number of fields for {0} (Should be {2} but actually get {3}): {1}. '.format(
                    self.__class__.__name__, self.record_str, len(self.keys), len(record_list)))
        return record_list

    def is_valid(self):
        return True

    def post_validation_work(self):
        """After is_valid() is called, do this
        """
        pass


class MatchInfoRecord(Record):
    keys = ['match_id', 'league_id', 'league_name', 'league_name_simp', 'league_name_trad',
            'home_team_id', 'home_team_name', 'home_team_name_simp', 'home_team_name_trad', 'away_team_id',
            'away_team_name', 'away_team_name_simp', 'away_team_name_trad', 'match_hk_time', 'group_color',
            'is_in_running', 'home_team_score', 'away_team_score', 'running_time', 'will_run',
            'home_team_red_card', 'away_team_red_card']

    def __init__(self, record_str):
        super(MatchInfoRecord, self).__init__(record_str)
        self.refine_info()

    def get_sport_type(self):
        if is_match_basketball(self.record_dict):
            return 'basketball'
        else:
            return 'football'

    def refine_info(self):
        self.record_dict['home_team_score'] = int(self.record_dict['home_team_score'])
        self.record_dict['away_team_score'] = int(self.record_dict['away_team_score'])
        self.record_dict['is_in_running'] = {'0': False, '1': True}[self.record_dict['is_in_running']]

        if not self.record_dict['is_in_running']:
            self.record_dict['home_team_score'] = -1
            self.record_dict['away_team_score'] = -1


class OddsRecord(Record):
    keys = []

    def __init__(self, record_str):
        super(OddsRecord, self).__init__(record_str)
        self.prices = None
        self.convert_data_type()

    def is_valid(self):
        # check odds type
        if self.record_dict['ot'] not in ['0', '4', '5', '6', '9']:
            return False

        # check event type
        if self.record_dict['et'] not in ['0', '1']:
            log.warn("Unknown value for event_type: {1}. Possible values are: 0, 1".format(
                self.record_dict['et']))
            return False

        # check odds value
        for x in ['o1', 'o2']:
            odds = self.record_dict[x]
            if odds > MAX_ODDS:
                log.debug('Odds {0} is too big. The record is {1}'.format(odds, self.record_str))
                self.record_dict[x] = 0

        return True

    def post_validation_work(self):
        self.explain_odds_record()
        self.produce_dish_value()
        self.produce_prices_value()

    def explain_odds_record(self):
        explain_map = {
            ('ot', 'odds_type'): {
                '0': '1x2',
                '4': 'OU',
                '5': 'AH',
                '6': '1or2',
                '9': 'EH',
            },
            ('et', 'event_type'): {
                '0': 'FT',
                '1': 'HT',
            },
        }
        for names, values in explain_map.items():
            short_name, full_name = names
            symbol = self.record_dict[short_name]
            self.record_dict[full_name] = values[symbol]

    def produce_dish_value(self):
        """This is only for VIP data. YY data has this function overridden
        """
        odds_type = self.record_dict['odds_type']
        if odds_type in ('AH', 'OU'):
            self.record_dict['dish'] = self.record_dict['o3'] / 4.0
        elif odds_type in ('1x2', '1or2'):
            self.record_dict['dish'] = None
            self.prices = [self.record_dict['o1'], self.record_dict['o2']]
        else:
            log.warn('Unknown odds type for VIP data: {0}'.format(odds_type))

    def produce_prices_value(self):
        odds_type = self.record_dict['odds_type']
        o1 = self.record_dict['o1']
        o2 = self.record_dict['o2']
        o3 = self.record_dict['o3']

        if odds_type in ('AH', 'OU', '1or2'):
            self.prices = [o1, o2]
        elif odds_type in ('1x2', 'EH'):
            self.prices = [o1, o2, o3]
        else:
            log.warn('Unknown odds type: {}'.format(odds_type))

    def convert_data_type(self):
        for x in ['o1', 'o2', 'o3']:
            value = self.record_dict[x]
            if value:
                self.record_dict[x] = float(value)

        self.record_dict['lay_flag'] = bool(int(self.record_dict['lay_flag']))

    def validate_record_format(self, record_list):
        if len(record_list) == len(self.keys) - 1:
            record_list.append(False)
        elif len(record_list) != len(self.keys):
            raise IncorrectLengthRecord(
                    'Incorrect number of fields for {0} (Should be {2} but actually get {3}): {1}. '.format(
                    self.__class__.__name__, self.record_str, len(self.keys), len(record_list)))

        return record_list


class InitOddsRecord(OddsRecord):
    keys = ['et', 'ot', 'match_id', 'bookie_id', 'bet_data', 'o1', 'o2', 'o3', 'lay_flag']


class VIPUpdateOddsRecord(OddsRecord):
    keys = ['update_id'] + InitOddsRecord.keys

    def convert_data_type(self):
        super(VIPUpdateOddsRecord, self).convert_data_type()
        self.record_dict['update_id'] = int(self.record_dict['update_id'])


class YYUpdateOddsRecord(OddsRecord):
    """Format:
    o{update_id}|{lay_flag}|{et}|{ot}|{dish}|{match_id}|{bookmaker_id}|{bet_data}|{o1}|{o2}|{o3}
    """
    keys = ['update_id', 'lay_flag', 'et', 'ot', 'dish', 'match_id', 'bookie_id', 'bet_data', 'o1', 'o2', 'o3']

    def produce_dish_value(self):
        dish = self.record_dict['dish']
        self.record_dict['dish'] = float(dish) / 4 if dish else None
