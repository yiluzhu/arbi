import datetime
from collections import namedtuple
from arbi.constants import BOOKIE_COMMISSION_MAP, BOOKIE_NAME_CN_MAP, BOOKIE_ID_MAP, SPORTTERY_REBATE


Selection = namedtuple('Selection', ['odds_type', 'subtype', 'f_ht', 'bookie_id', 'stake', 'odds',
                                     'bet_data', 'lay_flag'])


class ArbiOpportunity(object):
    match_info_keys = ['match_id', 'league_name', 'league_name_simp',
                       'home_team_name', 'home_team_name_simp', 'away_team_name', 'away_team_name_simp',
                       'home_team_score', 'away_team_score', 'is_in_running', 'match_hk_time', 'running_time']

    def __init__(self, match_info, occur_at_utc, strat_id, opportunity):
        self.match_info = match_info
        self.occur_at_utc = occur_at_utc
        self.strat_id = strat_id
        self.occur_at_hk_str = str(occur_at_utc + datetime.timedelta(hours=8))[:-3]
        self.profit, selections = opportunity
        self.selections = [Selection(*s) for s in selections]

    @property
    def involved_bookie_ids(self):
        return [selection.bookie_id for selection in self.selections]

    def __eq__(self, other):
        return self.match_info['match_id'] == other.match_info['match_id'] and \
            self.strat_id == other.strat_id and self.selections == other.selections

    def get_summary(self):
        bookies = [BOOKIE_ID_MAP[selection.bookie_id] for selection in self.selections]
        commissions = [BOOKIE_COMMISSION_MAP.get(bookie, 0) for bookie in bookies]
        bookie_cns = [BOOKIE_NAME_CN_MAP.get(bookie, bookie) for bookie in bookies]
        single_market_flag = self.match_info.get('single_market_flag', 0)

        ret = sum([[
                       selection.odds_type, selection.subtype, selection.f_ht, bookies[i], bookie_cns[i], selection.stake,
                       convert_effective_odds_to_raw_odds(selection.odds) if selection.bookie_id == '99' else selection.odds,
                       selection.odds if selection.bookie_id == '99' else convert_raw_odds_to_effective_odds(selection.odds, commissions[i]),
                       str(commissions[i] * 100) + ' %', bool(selection.lay_flag)
                   ]
                   for i, selection in enumerate(self.selections)], [])

        ret = [bool(single_market_flag), self.strat_id, '{0} %'.format(self.profit * 100), self.occur_at_hk_str] + \
              [self.match_info[x] for x in ['league_name', 'league_name_simp',
                                            'home_team_name', 'home_team_name_simp', 'home_team_score',
                                            'away_team_score', 'away_team_name', 'away_team_name_simp']] + ret

        return ret

    def __repr__(self):
        return str(self.get_summary())


def convert_raw_odds_to_effective_odds(raw_odds, commission):
    return round(raw_odds * (1 + commission), 3)


def convert_effective_odds_to_raw_odds(effective_odds, ret_pct=SPORTTERY_REBATE):
    return round((effective_odds - 1) * (1 - ret_pct) + 1, 2)
