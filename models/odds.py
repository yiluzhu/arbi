import time
import logging
from collections import namedtuple
from arbi.utils import merge_dict
from arbi.constants import BOOKIE_ID_MAP


log = logging.getLogger(__name__)
#log.setLevel(logging.WARN)
log.addHandler(logging.StreamHandler())


class UnknownBookieId(Exception):
    """
    The bookie id is not in our bookie map
    """


class UnknownOddsType(Exception):
    """
    The odds type is unknown.
    """

# namedtuple is compatible to tuple
BookieOddsInfo = namedtuple('BookieOddsInfo', 'prices bet_data last_updated')


class Odds(object):
    """
    All odds from all bookies for a specific match.
    It includes all event_type and odds_type.

    :param record_dict: Record.record_dict in record.py
    """
    def __init__(self, record_dict, goal_diff=None):
        odds_details = self.get_odds_details(record_dict)
        if odds_details:
            event_type, odds_type, bookie_id, bet_data, odds_type_value, prices = odds_details
            if bookie_id in ('7', '7 lay') and odds_type == 'AH':
                # We count goal difference when import AH prices for betfair,
                # as betfair AH rules are different from traditional AH rules.
                # The imported AH prices will be compatible with traditional AH rules.
                if goal_diff is None:
                    # ignore this price as there is not enough information to decide handicap.
                    log.error('Instantiate Odds object with betfair record, but no goal difference provided. Program should not run to here.')
                    self.odds_dict = {}
                    return
                else:
                    odds_type_value += goal_diff

            self.odds_dict = {
                (event_type, odds_type): {
                    odds_type_value: {
                        bookie_id: BookieOddsInfo(prices, bet_data, time.time())
                    }
                }
            }
        else:
            self.odds_dict = {}

    def update_with_dict(self, record_dict, goal_diff=None):
        odds_details = self.get_odds_details(record_dict)
        if odds_details:
            event_type, odds_type, bookie_id, bet_data, odds_type_value, prices = odds_details
            if bookie_id in ('7', '7 lay') and odds_type == 'AH':
                if goal_diff is None:
                    return
                else:
                    odds_type_value += goal_diff
            merge_dict(self.odds_dict,
                {
                    (event_type, odds_type): {
                        odds_type_value: {
                            bookie_id: BookieOddsInfo(prices, bet_data, time.time())
                        }
                    }
                }
            )

    def get_odds_details(self, record_dict):
        event_type = record_dict['event_type']
        odds_type = record_dict['odds_type']
        bookie_id = record_dict['bookie_id']
        bet_data = record_dict['bet_data']
        lay_flag = record_dict['lay_flag']
        dish = record_dict['dish']

        if bookie_id not in BOOKIE_ID_MAP:
            #  Our source feeds send odds for all bookies including those we can't bet. We filter them out here
            return

        if bookie_id == '7' and lay_flag:
            bookie_id = '7 lay'

        prices = [record_dict[x] for x in (['o1', 'o2', 'o3'] if odds_type in ['1x2', 'EH'] else ['o1', 'o2'])]

        return event_type, odds_type, bookie_id, bet_data, dish, prices
