from arbi.models.opportunity import ArbiOpportunity, convert_raw_odds_to_effective_odds
from arbi.constants import BOOKIE_COMMISSION_MAP, BOOKIE_NAME_CN_MAP, BOOKIE_ID_MAP


class TCArbiOpportunity(ArbiOpportunity):

    def get_summary(self):
        bookies = [BOOKIE_ID_MAP[selection.bookie_id] for selection in self.selections]
        commissions = [BOOKIE_COMMISSION_MAP.get(bookie, 0) for bookie in bookies]
        bookie_cns = [BOOKIE_NAME_CN_MAP.get(bookie, bookie) for bookie in bookies]

        ret = sum([[
                       selection.odds_type, selection.subtype, selection.f_ht, bookies[i], bookie_cns[i], selection.stake,
                       selection.odds,
                       selection.odds if selection.bookie_id == '99' else convert_raw_odds_to_effective_odds(selection.odds, commissions[i]),
                       str(commissions[i] * 100) + ' %', bool(selection.lay_flag)
                   ]
                   for i, selection in enumerate(self.selections)], [])

        return ['Sporttery No Rebate', self.strat_id, '{0} %'.format(self.profit * 100), self.occur_at_hk_str] + \
              [self.match_info[x] for x in ['league_name', 'league_name_simp',
                                            'home_team_name', 'home_team_name_simp', 'home_team_score',
                                            'away_team_score', 'away_team_name', 'away_team_name_simp']] + ret
