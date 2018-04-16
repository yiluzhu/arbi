from arbi import constants

from arbi.models.calculations import convert_back_lay_prices
from arbi.models.calculations import calculate_stakes, calculate_stakes_new
from arbi.strats.strat import BaseArbiStrategy


class AHvs2Strategy(BaseArbiStrategy):
    """
        match.odds.odds_dict = {
            ('FT', 'AH'): {
                                0.5: {'b1': ([2.35, 1.60], 'a!A1', 123.45),
                                      'b2': ([2.30, 1.65], 'b!A2', 456.78),
                                      'b3': ([2.25, 1.70], 'c!A3', 789.12),
                                     }
                           },
            ('FT', '1x2'): {
                                None: {'b4': ([2.00, 3.50, 3.50], 'd!A4', 741.85),
                                       'b5': ([2.00, 3.40, 3.60], 'e!A5', 963.25),
                                      },
                           },
            ...
        }
    """
    # TODO add support for non-traditional AH bookies
    arbi_args_for_both_map = {
        False: {
            'AH':  0,  # Home
            '1x2': 2,  # Away
            'selection1': 'AH Home',
            'handicap sign': 1,
            'selection2': 'Away',
        },
        True:  {
            'AH':  1,  # Away
            '1x2': 0,  # Home
            'selection1': 'AH Away',
            'handicap sign': -1,
            'selection2': 'Home',
        }
    }

    def spot_arbi(self, match, bookie_availability_dict):
        """Strategy 006/005
        Normal:   AH Home +0.5, 1x2 Away.
        Reversed: AH Away +0.5, 1x2 Home.
            Note: AH Away + 0.5 == AH Home -0.5

        """
        home_score = match.info['home_team_score']  # -1 for dead ball
        away_score = match.info['away_team_score']  # -1 for dead ball
        bet_period = 'running ball' if match.is_in_running else 'dead ball'

        if home_score == away_score:
            handicap = 0.5
            arbi_opps = self.spot_arbi_both(match.odds.odds_dict, handicap,
                                            bookie_availability_dict, bet_period, is_arbi_reversed=False) + \
                        self.spot_arbi_both(match.odds.odds_dict, handicap * -1,
                                            bookie_availability_dict, bet_period, is_arbi_reversed=True)
        elif home_score > away_score:
            handicap = home_score - away_score + 0.5
            arbi_opps = self.spot_arbi_both(match.odds.odds_dict, handicap,
                                            bookie_availability_dict, bet_period, is_arbi_reversed=False)
        else:  # home_score < away_score
            handicap = home_score - away_score - 0.5
            arbi_opps = self.spot_arbi_both(match.odds.odds_dict, handicap,
                                            bookie_availability_dict, bet_period, is_arbi_reversed=True)

        return arbi_opps

    def spot_arbi_both(self, odds_dict, handicap, bookie_availability_dict, bet_period, is_arbi_reversed):
        arbi_args = self.arbi_args_for_both_map[is_arbi_reversed]
        arbi_opps = []
        for event_type in ['FT', 'HT']:
            if (event_type, 'AH') in odds_dict and (event_type, '1x2') in odds_dict:
                if handicap in odds_dict[(event_type, 'AH')] and None in odds_dict[(event_type, '1x2')]:
                    ah_prices = []
                    for bookie_id, bookie_odds_info in odds_dict[(event_type, 'AH')][handicap].iteritems():
                        prices, receipt, last_updated = bookie_odds_info
                        if bookie_availability_dict[bookie_id][bet_period] and not bookie_id.endswith(' lay') and \
                                bookie_id not in constants.NON_TRADITIONAL_AH_BOOKIE_IDS:
                            ah_price = prices[arbi_args['AH']]
                            if ah_price:  # cannot be 0
                                ah_prices.append((bookie_id, ah_price, receipt))
                    ah_prices.sort(key=lambda x: x[1], reverse=True)

                    x_prices = []
                    for bookie_id, bookie_odds_info in odds_dict[(event_type, '1x2')][None].iteritems():
                        prices, receipt, last_updated = bookie_odds_info
                        if bookie_availability_dict[bookie_id][bet_period] and not bookie_id.endswith(' lay') and \
                                bookie_id not in constants.NON_TRADITIONAL_AH_BOOKIE_IDS:
                            x_price = prices[arbi_args['1x2']]
                            if x_price:
                                x_prices.append((bookie_id, x_price, receipt))
                    x_prices.sort(key=lambda x: x[1], reverse=True)

                    for ah_data, x_data in zip(ah_prices, x_prices):
                        ah_bookie_id, home_price, ah_receipt = ah_data
                        x_bookie_id, x_price, x_receipt = x_data
                        if ah_bookie_id != x_bookie_id:
                            result = calculate_stakes(home_price, x_price, profit_threshold=self.profit_threshold)
                            if result:
                                stake1, stake2, profit = result
                                selection1 = (arbi_args['selection1'], handicap * arbi_args['handicap sign'],
                                              event_type, ah_bookie_id, stake1, home_price, ah_receipt, False)
                                selection2 = ('1x2', arbi_args['selection2'],
                                              event_type, x_bookie_id, stake2, x_price, x_receipt, False)
                                arbi_opps.append((profit, (selection1, selection2)))
                            else:
                                break

        return arbi_opps


class AHvsXvs2Strategy(BaseArbiStrategy):
    """
        match.odds.odds_dict = {
            ('FT', 'AH'): {
                                -0.5: {'b1': ([2.35, 1.60], 'a!A1'),
                                       'b2': ([2.30, 1.65], 'b!A2'),
                                       'b3': ([2.25, 1.70], 'c!A3'),
                                     },
                           },
            ('FT', '1x2'): {
                                None: {'b4': ([2.00, 3.50, 3.50], 'd!A4'),
                                       'b5': ([2.00, 3.40, 3.60], 'e!A5'),
                                      },
                            },
            ...
        }
    """

    # TODO add support for non-traditional AH bookies
    arbi_args_for_both_map = {
        False: {
            'AH':  0,  # Home
            '1x2': 2,  # Away
            '1x2 lay': 0,  # Home
            'selection1': 'AH Home',
            'selection2 lay': 'Home',
            'handicap sign': 1,
            'selection3 1x2': 'Away',
        },
        True:  {
            'AH':  1,  # Away
            '1x2': 0,  # Home
            '1x2 lay': 2,  # Away
            'selection1': 'AH Away',
            'selection2 lay': 'Away',
            'handicap sign': -1,
            'selection3 1x2': 'Home',
        },
    }

    def spot_arbi(self, match, bookie_availability_dict):
        """
        Normal:   AH Home -0.5, 1x2 Draw, 1x2 Away or AH Home -0.5, 1x2 Home lay
            It's not applicable to home winning state.
        Reversed: AH Away -0.5, 1x2 Draw, 1x2 Home or AH Away -0.5, 1x2 Away lay
            It's not applicable to away winning state.
            Note: AH Away -0.5 means AH Home +0.5.  All our handicaps in AH are based on home teams.
        """
        home_score = match.info['home_team_score']  # -1 for dead ball
        away_score = match.info['away_team_score']  # -1 for dead ball
        bet_period = 'running ball' if match.is_in_running else 'dead ball'

        if home_score == away_score:
            handicap = -0.5
            arbi_opps = self.spot_arbi_both(match.odds.odds_dict, handicap,
                                            bookie_availability_dict, bet_period, is_arbi_reversed=False) + \
                        self.spot_arbi_both(match.odds.odds_dict, handicap * -1,
                                            bookie_availability_dict, bet_period, is_arbi_reversed=True)
        elif home_score < away_score:
            handicap = home_score - away_score - 0.5
            arbi_opps = self.spot_arbi_both(match.odds.odds_dict, handicap,
                                            bookie_availability_dict, bet_period, is_arbi_reversed=False, even_score=False)
        else:  # home_score > away_score
            handicap = home_score - away_score + 0.5
            arbi_opps = self.spot_arbi_both(match.odds.odds_dict, handicap,
                                            bookie_availability_dict, bet_period, is_arbi_reversed=True, even_score=False)

        return arbi_opps

    def find_opps_for_ah_and_x_lay_prices(self, ah_prices, x_lay_prices, arbi_args, event_type, handicap):
        """For each price in ah_prices and x_lay_prices:
         1. find if they can make arb;
         2. if so, mark them so they can't be used again
         3. continue until both lists are exhausted
         4. the ah prices used can't be used again in later calculation
        """
        arbi_opps = []
        used_ah_price_index_list = []
        used_x_lay_price_index_list = []
        for x_lay_index, x_lay_data in enumerate(x_lay_prices):
            x_lay_bookie_id, x_lay_price_converted, x_lay_receipt = x_lay_data
            for ah_index, ah_data in enumerate(ah_prices):
                ah_bookie_id, ah_price, ah_receipt = ah_data
                if ah_index not in used_ah_price_index_list and x_lay_index not in used_x_lay_price_index_list and \
                        ah_bookie_id not in [x_lay_bookie_id, x_lay_bookie_id.replace(' lay', '')]:
                    comm1 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[ah_bookie_id], 0)
                    comm2 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[x_lay_bookie_id], 0)
                    result = calculate_stakes(ah_price, x_lay_price_converted, comm1, comm2, self.profit_threshold)

                    if result:
                        stake1, stake2, profit = result
                        selection1 = (arbi_args['selection1'], handicap * arbi_args['handicap sign'],
                                      event_type, ah_bookie_id, stake1, ah_price, ah_receipt, False)
                        selection2 = ('1x2', arbi_args['selection2 lay'],
                                      event_type, x_lay_bookie_id[:-4], stake2, convert_back_lay_prices(x_lay_price_converted), x_lay_receipt, True)
                        arbi_opps.append((profit, (selection1, selection2)))
                        used_ah_price_index_list.append(ah_index)
                        used_x_lay_price_index_list.append(x_lay_index)
                    else:
                        break

        # exclude ah prices that have been used
        ah_prices = [price for i, price in enumerate(ah_prices) if i not in used_ah_price_index_list]

        return ah_prices, arbi_opps

    def find_opps_for_ah_draw_and_x_prices(self, ah_prices, draw_prices, x_prices, arbi_args, event_type, handicap):
        arbi_opps = []
        for ah_data, draw_data, x_data in zip(ah_prices, draw_prices, x_prices):
            ah_bookie_id, ah_price, ah_receipt = ah_data
            draw_bookie_id, draw_price, draw_receipt = draw_data
            x_bookie_id, x_price, x_receipt = x_data
            if {ah_bookie_id, draw_bookie_id, x_bookie_id} != {ah_bookie_id}:
                commission1 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[ah_bookie_id], 0)
                commission2 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[draw_bookie_id], 0)
                commission3 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[x_bookie_id], 0)
                result = calculate_stakes_new(ah_price, draw_price, x_price,
                                              commission1, commission2, commission3, self.profit_threshold)

                if result:
                    stake1, stake2, stake3, profit = result
                    selection1 = (arbi_args['selection1'], handicap * arbi_args['handicap sign'],
                                  event_type, ah_bookie_id, stake1, ah_price, ah_receipt, False)
                    selection2 = ('1x2', 'Draw',
                                  event_type, draw_bookie_id, stake2, draw_price, draw_receipt, False)
                    selection3 = ('1x2', arbi_args['selection3 1x2'],
                                  event_type, x_bookie_id, stake3, x_price, x_receipt, False)
                    arbi_opps.append((profit, (selection1, selection2, selection3)))
                else:
                    break

        return arbi_opps

    def get_prices_by_position(self, odds_dict, bookie_availability_dict, bet_period, arbi_args, event_type, handicap):
        ah_prices = []
        for bookie_id, bookie_odds_info in odds_dict[(event_type, 'AH')][handicap].iteritems():
            prices, receipt, last_updated = bookie_odds_info
            # because betfair AH has rules different from traditional AH, we don't include them in AH prices
            if bookie_availability_dict[bookie_id][bet_period] and not bookie_id.endswith(' lay') and \
                    bookie_id not in constants.NON_TRADITIONAL_AH_BOOKIE_IDS:
                ah_price = prices[arbi_args['AH']]
                if ah_price:  # cannot be 0
                    ah_prices.append((bookie_id, ah_price, receipt))

        draw_prices = []
        x_prices = []
        x_lay_prices = []
        for bookie_id, bookie_odds_info in odds_dict[(event_type, '1x2')][None].iteritems():
            prices, receipt, last_updated = bookie_odds_info
            if bookie_availability_dict[bookie_id][bet_period]:
                if bookie_id.endswith(' lay'):
                    x_lay_price = prices[arbi_args['1x2 lay']]
                    if x_lay_price:
                        x_lay_prices.append((bookie_id, convert_back_lay_prices(x_lay_price, round_up=False), receipt))
                else:
                    draw_price = prices[1]
                    if draw_price:
                        draw_prices.append((bookie_id, draw_price, receipt))
                    x_price = prices[arbi_args['1x2']]
                    if x_price:
                        x_prices.append((bookie_id, x_price, receipt))

        for seq in [ah_prices, draw_prices, x_prices, x_lay_prices]:
            seq.sort(key=lambda x: x[1], reverse=True)

        return ah_prices, draw_prices, x_prices, x_lay_prices

    def spot_arbi_both(self, odds_dict, handicap, bookie_availability_dict, bet_period, is_arbi_reversed, even_score=True):
        arbi_args = self.arbi_args_for_both_map[is_arbi_reversed]
        arbi_opps = []
        for event_type in ['FT', 'HT']:
            if (event_type, 'AH') in odds_dict and (event_type, '1x2') in odds_dict and \
                    handicap in odds_dict[(event_type, 'AH')] and None in odds_dict[(event_type, '1x2')]:
                ah_prices, draw_prices, x_prices, x_lay_prices = self.get_prices_by_position(odds_dict,
                                                 bookie_availability_dict, bet_period, arbi_args, event_type, handicap)
                found_2_selection_opps = False
                if even_score:
                    ah_prices, opps = self.find_opps_for_ah_and_x_lay_prices(ah_prices, x_lay_prices,
                                                                             arbi_args, event_type, handicap)
                    if opps:
                        arbi_opps += opps
                        found_2_selection_opps = True

                if found_2_selection_opps:
                    # we don't bother to calculate 3 selection arbs if we've got 2 selection ones.
                    # This is an optimization to limit the number of opportunities.
                    continue

                opps = self.find_opps_for_ah_draw_and_x_prices(ah_prices, draw_prices, x_prices,
                                                               arbi_args, event_type, handicap)
                arbi_opps += opps

        return arbi_opps
