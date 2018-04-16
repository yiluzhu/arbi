from arbi import constants
from arbi.models.arbi_spotter import ArbiSpotter, run_one_strat
from arbi.models.calculations import calculate_stakes, convert_back_lay_prices
from arbi.models.opportunity import convert_effective_odds_to_raw_odds
from arbi.strats.direct_arbi import DirectArbiStrategy
from arbi.tools.tc.models.tc_opportunity import TCArbiOpportunity


def run_one_tc_strat(matches, strat):
    return {match.id: {strat.id: strat.spot_arbi(match)} for match in matches if match.odds and match.info}


class TCArbiSpotter(ArbiSpotter):
    def it_is_time_to_check_rb_prices_expiry(self):
        return False

    def check_running_ball_prices_expiry(self, odds_dict):
        pass

    def apply_strats(self, matches):
        dead_ball_matches = [match for match in matches if not match.is_in_running]
        raw_opps_dict = {}
        for name, strat in self.selected_strats_name_map.items():
            if name != 'CrossHandicapArbiStrategy':
                if strat.id == '1':
                    new_raw_opps_dict = run_one_tc_strat(dead_ball_matches, strat)
                else:
                    new_raw_opps_dict = run_one_strat(dead_ball_matches, strat, self.bookie_availability_dict)
                raw_opps_dict = self.update_raw_opps_dict(raw_opps_dict, new_raw_opps_dict)
                if name == 'DirectArbiStrategy':
                    new_raw_opps_dict = self.get_1or2_opps(dead_ball_matches)
                    raw_opps_dict = self.update_raw_opps_dict(raw_opps_dict, new_raw_opps_dict, do_assert=False)

        return raw_opps_dict

    def get_1or2_opps(self, matches):
        arbi_opps_dict = {}
        for match in matches:
            if match.odds and match.info:
                for (event_type, odds_type), odds_by_category in match.odds.odds_dict.iteritems():
                    if odds_type == '1or2':
                        arbi_opps = DirectArbiStrategy.spot_direct_arb_for_1or2(event_type, odds_by_category,
                                            self.bookie_availability_dict, 'dead ball', self.profit_threshold)
                        # 99 is the strat id for 1or2, which is only used for basketball at the moment.
                        # Cannot use 1 here as the opps generated by normal DirectArbiStrategy would get lost.
                        arbi_opps_dict[match.id] = {'99': arbi_opps}

        return arbi_opps_dict

    def recalculate_without_sporttery_rebate(self, arbi_opp):
        """For tc opportunities, we want to know whether the arb still stands if there was no rebate"""
        # TODO: complete for all strategies
        if arbi_opp.strat_id in ['1', '3']:
            green_arbi_opp = self.spot_arbi_recalculate(arbi_opp, self.profit_threshold)
            return green_arbi_opp

    @staticmethod
    def spot_arbi_recalculate(arbi_opp, profit_threshold):
        """Given an arbi opportunity that involves sporttery, calculate if the selection can still make arbitrage if sporttery has no rebate
        """
        selection1, selection2 = arbi_opp.selections
        swapped = False
        if selection2.bookie_id == '99':
            selection1, selection2 = selection2, selection1
            swapped = True

        odds1 = convert_effective_odds_to_raw_odds(selection1.odds)
        odds2 = convert_back_lay_prices(selection2.odds) if selection2.lay_flag else selection2.odds
        commission1 = 0
        commission2 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[selection2.bookie_id], 0)
        result = calculate_stakes(odds1, odds2, commission1, commission2, profit_threshold)
        if result:
            stake1, stake2, profit = result
            selection1 = (selection1.odds_type, selection1.subtype, selection1.f_ht, '99', stake1,
                          odds1, selection1.bet_data, False)
            selection2 = (selection2.odds_type, selection2.subtype, selection2.f_ht, selection2.bookie_id, stake2,
                          selection2.odds, selection2.bet_data, selection2.lay_flag)

            raw_opp = profit, (selection2, selection1) if swapped else (selection1, selection2)
            return TCArbiOpportunity(arbi_opp.match_info, arbi_opp.occur_at_utc, arbi_opp.strat_id, raw_opp)