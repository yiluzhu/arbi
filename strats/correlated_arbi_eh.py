from arbi import constants

from arbi.models.calculations import convert_back_lay_prices
from arbi.models.calculations import calculate_stakes_new, calculate_stakes
from arbi.strats.strat import BaseArbiStrategy


class EHvsEHXvsAHStrategy(BaseArbiStrategy):
    """
        Note: AH2(+0.5) means Away team +0.5 so AH dish should be -0.5

        Normal:
            Strategy 019: home in favour
                EH1(-1) - X1(-1) - AH2(+0.5) or EH2(+1) lay - AH2(+0.5)
            Strategy 022: home in favour
                EH1(-2) - X1(-2) - AH2(+1.5) or EH2(+2) lay - AH2(+1.5)
            Strategy 025: home in favour
                EH1(-3) - X1(-3) - AH2(+2.5) or EH2(+3) lay - AH2(+2.5)

        Reversed:
            Strategy 027: away in favour
                AH1(+0.5) - X1(+1) - EH2(-1) or AH1(+0.5) - EH1(+1) lay
            Strategy 030: away in favour
                AH1(+1.5) - X1(+2) - EH2(-2) or AH1(+1.5) - EH1(+2) lay
            Strategy 033: away in favour
                AH1(+2.5) - X1(+3) - EH2(-3) or AH1(+2.5) - EH1(+3) lay
    """
    arbi_args_for_both_map = {
        False: {'EH': 0,  # Home
                'EH_lay': 2,  # Away
                'AH': 1,  # Away
               },
        True:  {'EH': 2,  # Away
                'EH_lay': 0,  # Home
                'AH': 0,  # Home
               }
    }

    def spot_arbi(self, match, bookie_availability_dict):
        home_score = match.info['home_team_score']  # -1 for dead ball
        away_score = match.info['away_team_score']  # -1 for dead ball
        bet_period = 'running ball' if match.is_in_running else 'dead ball'

        if home_score == away_score:
            arbi_opps = self.spot_arbi_normal(match.odds.odds_dict, bookie_availability_dict, bet_period) + \
                        self.spot_arbi_reversed(match.odds.odds_dict, bookie_availability_dict, bet_period)
        else:
            arbi_opps = []  # todo complete this

        return arbi_opps

    def get_prices_by_position(self, odds_dict, bookie_availability_dict, bet_period, ah_hcp, eh_hcp, is_reversed):
        arbi_args = self.arbi_args_for_both_map[is_reversed]

        ah_prices = []
        for bookie_id, bookie_odds_info in odds_dict[('FT', 'AH')][ah_hcp].iteritems():
            prices, receipt, last_updated = bookie_odds_info
            if bookie_availability_dict[bookie_id][bet_period] and bookie_id not in ['7', '7 lay']:
                ah_price = prices[arbi_args['AH']]
                if ah_price:  # cannot be 0
                    ah_prices.append((bookie_id, ah_price, receipt))

        draw_prices = []
        eh_prices = []
        eh_lay_prices = []
        for bookie_id, bookie_odds_info in odds_dict[('FT', 'EH')][eh_hcp].iteritems():
            prices, receipt, last_updated = bookie_odds_info
            if bookie_availability_dict[bookie_id][bet_period]:
                if bookie_id.endswith(' lay'):  # only betfair offers this market at the moment
                    eh_lay_price = prices[arbi_args['EH_lay']]
                    if eh_lay_price:
                        eh_lay_prices.append((bookie_id, convert_back_lay_prices(eh_lay_price, round_up=False), receipt))
                else:
                    draw_price = prices[1]
                    eh_price = prices[arbi_args['EH']]
                    if draw_price and eh_price:
                        draw_prices.append((bookie_id, draw_price, receipt))
                        eh_prices.append((bookie_id, eh_price, receipt))

        for seq in [ah_prices, draw_prices, eh_prices, eh_lay_prices]:
            seq.sort(key=lambda x: x[1], reverse=True)

        return ah_prices, draw_prices, eh_prices, eh_lay_prices

    def spot_arbi_normal(self, odds_dict, bookie_availability_dict, bet_period):
        arbi_opps = []
        if ('FT', 'AH') in odds_dict and ('FT', 'EH') in odds_dict:
            for eh_hcp, ah_hcp in [(-1, -0.5), (-2, -1.5), (-3, -2.5)]:
                if eh_hcp in odds_dict[('FT', 'EH')] and ah_hcp in odds_dict[('FT', 'AH')]:
                    ah_prices, draw_prices, eh_prices, eh_lay_prices = self.get_prices_by_position(odds_dict,
                                                        bookie_availability_dict, bet_period, ah_hcp, eh_hcp, False)

                    found_2_selection_opps = False
                    # Calculate opportunities with EH Lay first
                    for eh_lay_data, ah_data in zip(eh_lay_prices, ah_prices):
                        eh_lay_bookie_id, eh_lay_price_converted, eh_lay_receipt = eh_lay_data
                        ah_bookie_id, ah_price, ah_receipt = ah_data
                        if eh_lay_bookie_id != ah_bookie_id:
                            eh_lay_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[eh_lay_bookie_id], 0)
                            ah_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[ah_bookie_id], 0)

                            result = calculate_stakes(eh_lay_price_converted, ah_price, eh_lay_comm, ah_comm, self.profit_threshold)
                            if result:
                                stake1, stake2, profit = result
                                selection1 = ('EH Away', eh_hcp * -1,
                                              'FT', eh_lay_bookie_id[:-4], stake1, convert_back_lay_prices(eh_lay_price_converted), eh_lay_receipt, True)
                                selection2 = ('AH Away', ah_hcp * -1,
                                              'FT', ah_bookie_id, stake2, ah_price, ah_receipt, False)
                                arbi_opps.append((profit, (selection1, selection2)))
                                found_2_selection_opps = True
                            else:
                                break

                    if found_2_selection_opps:
                        # we don't bother to calculate 3 selection arbs if we've got 2 selection ones
                        continue

                    ah_prices = ah_prices[len(eh_lay_prices):]  # exclude ah prices that has been used
                    for eh_data, draw_data, ah_data in zip(eh_prices, draw_prices, ah_prices):
                        eh_bookie_id, eh_price, eh_receipt = eh_data
                        draw_bookie_id, draw_price, draw_receipt = draw_data
                        ah_bookie_id, ah_price, ah_receipt = ah_data
                        if {eh_bookie_id, draw_bookie_id, ah_bookie_id} != {ah_bookie_id}:
                            eh_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[eh_bookie_id], 0)
                            draw_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[draw_bookie_id], 0)
                            ah_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[ah_bookie_id], 0)

                            result = calculate_stakes_new(eh_price, draw_price, ah_price,
                                                          eh_comm, draw_comm, ah_comm, self.profit_threshold)
                            if result:
                                stake1, stake2, stake3, profit = result
                                selection1 = ('EH Home', eh_hcp,
                                              'FT', eh_bookie_id, stake1, eh_price, eh_receipt, False)
                                selection2 = ('EH Draw', eh_hcp,
                                              'FT', draw_bookie_id, stake2, draw_price, draw_receipt, False)
                                selection3 = ('AH Away', ah_hcp * -1,
                                              'FT', ah_bookie_id, stake3, ah_price, ah_receipt, False)
                                arbi_opps.append((profit, (selection1, selection2, selection3)))
                            else:
                                break

        return arbi_opps

    def spot_arbi_reversed(self, odds_dict, bookie_availability_dict, bet_period):
        arbi_opps = []
        if ('FT', 'AH') in odds_dict and ('FT', 'EH') in odds_dict:
            for eh_hcp, ah_hcp in [(1, 0.5), (2, 1.5), (3, 2.5)]:
                if eh_hcp in odds_dict[('FT', 'EH')] and ah_hcp in odds_dict[('FT', 'AH')]:
                    ah_prices, draw_prices, eh_prices, eh_lay_prices = self.get_prices_by_position(odds_dict,
                                                            bookie_availability_dict, bet_period, ah_hcp, eh_hcp, True)

                    found_2_selection_opps = False
                    for eh_lay_data, ah_data in zip(eh_lay_prices, ah_prices):
                        eh_lay_bookie_id, eh_lay_price_converted, eh_lay_receipt = eh_lay_data
                        ah_bookie_id, ah_price, ah_receipt = ah_data
                        if eh_lay_bookie_id != ah_bookie_id:
                            eh_lay_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[eh_lay_bookie_id], 0)
                            ah_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[ah_bookie_id], 0)

                            result = calculate_stakes(ah_price, eh_lay_price_converted, ah_comm, eh_lay_comm, self.profit_threshold)
                            if result:
                                stake1, stake2, profit = result
                                selection1 = ('AH Home', ah_hcp,
                                              'FT', ah_bookie_id, stake1, ah_price, ah_receipt, False)
                                selection2 = ('EH Home', eh_hcp,
                                              'FT', eh_lay_bookie_id[:-4], stake2, convert_back_lay_prices(eh_lay_price_converted), eh_lay_receipt, True)
                                arbi_opps.append((profit, (selection1, selection2)))
                                found_2_selection_opps = True
                            else:
                                break

                    if found_2_selection_opps:
                        # we don't bother to calculate 3 selection arbs if we've got 2 selection ones
                        continue

                    ah_prices = ah_prices[len(eh_lay_prices):]  # exclude ah prices that has been used
                    for eh_data, draw_data, ah_data in zip(eh_prices, draw_prices, ah_prices):
                        eh_bookie_id, eh_price, eh_receipt = eh_data
                        draw_bookie_id, draw_price, draw_receipt = draw_data
                        ah_bookie_id, ah_price, ah_receipt = ah_data
                        if {eh_bookie_id, draw_bookie_id, ah_bookie_id} != {ah_bookie_id}:
                            eh_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[eh_bookie_id], 0)
                            draw_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[draw_bookie_id], 0)
                            ah_comm = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[ah_bookie_id], 0)

                            result = calculate_stakes_new(ah_price, draw_price, eh_price,
                                                          ah_comm, draw_comm, eh_comm, self.profit_threshold)
                            if result:
                                stake1, stake2, stake3, profit = result
                                selection1 = ('AH Home', ah_hcp,
                                              'FT', ah_bookie_id, stake1, ah_price, ah_receipt, False)
                                selection2 = ('EH Draw', eh_hcp,
                                              'FT', draw_bookie_id, stake2, draw_price, draw_receipt, False)
                                selection3 = ('EH Away', eh_hcp * -1,
                                              'FT', eh_bookie_id, stake3, eh_price, eh_receipt, False)
                                arbi_opps.append((profit, (selection1, selection2, selection3)))
                            else:
                                break

        return arbi_opps
