from arbi import constants

from arbi.models.calculations import calculate_stakes, convert_back_lay_prices, get_better_price_from_back_lay_prices
from arbi.strats.strat import BaseArbiStrategy


class DirectArbiStrategy(BaseArbiStrategy):

    def spot_arbi(self, match, bookie_availability_dict):
        """This contains all the odds for one specific match, e.g.

        odds_dict = {
            ('FT', 'AH'): {
                                '0.5': {'1': ([2.05, 1.90], 'a!A1', 22345.678),
                                        '2': ([2.00, 1.95], 'b!A2', 38545.123),
                                        '7': ([1.95, 2.00], 'c!A3', 17896.254),
                                        '7 lay': ([1.97, 2.02], 'c!A4', 17896.255),
                                       },
                                '0.75':{'4': ([1.75, 2.20], 'd!A4', 45862.482),
                                       },
                          },
            ('HT', 'OU'): {
                                '1.5': {'5': ([2.00, 1.95], 'e!A5', 78564.396),
                                       },
                          },
            ('FT', '1x2'): {
                                None: {'1': ([3.0, 4.0, 4.5], 'f!A1', 22345.678),
                                       '2': ([3.1, 4.2, 4.3], 'g!A2', 38545.123),
                                       '7': ([3.2, 4.3, 4.4], 'h!A3', 17896.254),
                                       '7 lay': ([3.3, 4.4, 4.5], 'j!A4', 17896.255),
                                       },
            ...
        }

        Lay price can be better than back price for both home and away, e.g.:
            {'7': [1.95, 2.0],
             '7 lay': [1.97, 2.02]
            }
        Lay price can be worse than back price for both home and away, e.g.:
            {'7': [1.7, 2.25],
             '7 lay': [1.82, 2.45]
            }
        Lay price can be better than back price only for home, e.g.:
            {'7': [1.95, 2.0],
             '7 lay': [2.01, 2.02]
            }
        Lay price can be better than back price only for away, e.g.:
            {'7': [1.95, 2.0],
             '7 lay': [1.97, 2.06]
            }

        """
        odds_dict = match.odds.odds_dict
        goal_diff = match.info['home_team_score'] - match.info['away_team_score']
        bet_period = 'running ball' if match.is_in_running else 'dead ball'
        arbi_opps = []
        for (event_type, odds_type), odds_by_category in odds_dict.iteritems():
            if odds_type in ('AH', 'OU'):
                arbi_opps += self.spot_direct_arb_for_AH_and_OU(event_type, odds_type, goal_diff, odds_by_category,
                                                                bookie_availability_dict, bet_period, self.profit_threshold)
            if odds_type == '1x2':
                arbi_opps += self.spot_direct_arb_for_1x2(event_type, odds_by_category,
                                                          bookie_availability_dict, bet_period, self.profit_threshold)

        return arbi_opps

    @staticmethod
    def spot_direct_arb_for_1or2(event_type, odds_by_category, bookie_availability_dict, bet_period, profit_threshold):
        """This is for matches with only win or lose results, e.g. basketball
        """
        # TODO handle lay prices
        arbi_opps = []
        home_back_prices = []
        away_back_prices = []
        bookie_odds_id_and_info = odds_by_category.get(None)
        if not bookie_odds_id_and_info:
            return []

        for bookie_id, bookie_odds_info in bookie_odds_id_and_info.iteritems():
            prices, receipt, last_updated = bookie_odds_info
            home_price, away_price = prices
            if bookie_availability_dict[bookie_id][bet_period] and not bookie_id.endswith(' lay') and home_price and away_price:
                home_back_prices.append((bookie_id, home_price, receipt))
                away_back_prices.append((bookie_id, away_price, receipt))

        for seq in [home_back_prices, away_back_prices]:
            seq.sort(key=lambda x: x[1], reverse=True)

        for home_price_info, away_price_info in zip(home_back_prices, away_back_prices):
            home_bookie_id, home_price, home_receipt = home_price_info
            away_bookie_id, away_price, away_receipt = away_price_info
            commission1 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[home_bookie_id], 0)
            commission2 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[away_bookie_id], 0)
            result = calculate_stakes(home_price, away_price, commission1, commission2, profit_threshold)
            if result:
                stake1, stake2, profit = result
                selection1 = ('1or2', 'Home', event_type, home_bookie_id, stake1,
                              home_price, home_receipt, False)
                selection2 = ('1or2', 'Away', event_type, away_bookie_id, stake2,
                              away_price, away_receipt, False)
                arbi_opps.append((profit, (selection1, selection2)))
            else:
                break

        return arbi_opps

    @staticmethod
    def spot_direct_arb_for_1x2(event_type, odds_by_category, bookie_availability_dict, bet_period, profit_threshold):
        """This can only happens between back and lay prices from different bookies,

        e.g. Home back (sbo) vs Home lay (betfair)
        """
        arbi_opps = []
        home_back_prices = []
        draw_back_prices = []
        away_back_prices = []
        home_lay_prices_converted = []
        draw_lay_prices_converted = []
        away_lay_prices_converted = []
        bookie_odds_id_and_info = odds_by_category.get(None)
        if not bookie_odds_id_and_info:
            return []

        for bookie_id, bookie_odds_info in bookie_odds_id_and_info.iteritems():
            prices, receipt, last_updated = bookie_odds_info
            home_price, draw_price, away_price = prices
            if bookie_id in bookie_availability_dict and bookie_availability_dict[bookie_id][bet_period] and \
                    home_price and draw_price and away_price:
                if bookie_id.endswith(' lay'):
                    home_lay_price_converted = convert_back_lay_prices(home_price, round_up=False)
                    draw_lay_price_converted = convert_back_lay_prices(draw_price, round_up=False)
                    away_lay_price_converted = convert_back_lay_prices(away_price, round_up=False)
                    home_lay_prices_converted.append((bookie_id, home_lay_price_converted, receipt))
                    draw_lay_prices_converted.append((bookie_id, draw_lay_price_converted, receipt))
                    away_lay_prices_converted.append((bookie_id, away_lay_price_converted, receipt))
                elif bookie_id in constants.BOOKIE_IDS_WITH_LAY_PRICES:
                    pass  # we don't use it if the bookie_id could appear on lay side
                else:
                    home_back_prices.append((bookie_id, home_price, receipt))
                    draw_back_prices.append((bookie_id, draw_price, receipt))
                    away_back_prices.append((bookie_id, away_price, receipt))

        if not home_lay_prices_converted or not draw_lay_prices_converted or not away_lay_prices_converted:
            return []

        for seq in [home_lay_prices_converted, draw_lay_prices_converted, away_lay_prices_converted,
                    home_back_prices, draw_back_prices, away_back_prices]:
            seq.sort(key=lambda x: x[1], reverse=True)

        for back_prices, lay_prices, sub_type_flag in [(home_back_prices, home_lay_prices_converted, 'Home'),
                                                        (draw_back_prices, draw_lay_prices_converted, 'Draw'),
                                                        (away_back_prices, away_lay_prices_converted, 'Away')]:
            for (back_bookie_id, back_price, back_receipt), (lay_bookie_id, lay_price, lay_receipt) in zip(back_prices, lay_prices):
                commission1 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[back_bookie_id], 0)
                commission2 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[lay_bookie_id], 0)
                result = calculate_stakes(back_price, lay_price, commission1, commission2, profit_threshold)
                if result:
                    stake1, stake2, profit = result
                    selection1 = ('1x2', sub_type_flag, event_type, back_bookie_id, stake1,
                                  back_price, back_receipt, False)
                    selection2 = ('1x2', sub_type_flag, event_type, lay_bookie_id[:-4], stake2,
                                  convert_back_lay_prices(lay_price), lay_receipt, True)
                    arbi_opps.append((profit, (selection1, selection2)))

        return arbi_opps

    @staticmethod
    def spot_direct_arb_for_AH_and_OU(event_type, odds_type, goal_diff, odds_by_category,
                                      bookie_availability_dict, bet_period, profit_threshold):
        arbi_opps = []
        odds_type1 = '{} {}'.format(odds_type, {'AH': 'Home', 'OU': 'Over'}[odds_type])
        odds_type2 = '{} {}'.format(odds_type, {'AH': 'Away', 'OU': 'Under'}[odds_type])
        for handicap, bookie_odds_id_and_info in odds_by_category.iteritems():
            home_prices, away_prices = DirectArbiStrategy.get_prices_by_position(bookie_odds_id_and_info,
                                                                          bookie_availability_dict, bet_period)

            away_handicap = handicap * -1 if odds_type == 'AH' else handicap
            for (bookie_id1, odds1, receipt1), (bookie_id2, odds2, receipt2) in zip(home_prices, away_prices):
                if DirectArbiStrategy.is_valid(bookie_id1, bookie_id2):
                    commission1 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[bookie_id1], 0)
                    commission2 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[bookie_id2], 0)
                    result = calculate_stakes(odds1, odds2, commission1, commission2, profit_threshold)
                    if result:
                        stake1, stake2, profit = result
                        handicap_dict = {}
                        for _id, idx in [(bookie_id1, '1'), (bookie_id2, '2')]:
                            if _id in ['7', '7 lay'] and odds_type == 'AH':
                                handicap_dict[idx + '_home'] = handicap - goal_diff
                                handicap_dict[idx + '_away'] = (handicap - goal_diff) * -1
                            else:
                                handicap_dict[idx + '_home'] = handicap
                                handicap_dict[idx + '_away'] = away_handicap

                        if bookie_id1.endswith(' lay'):
                            selection1 = (odds_type2, handicap_dict['1_away'], event_type, bookie_id1.split()[0], stake1,
                                          convert_back_lay_prices(odds1), receipt1, True)
                        else:
                            selection1 = (odds_type1, handicap_dict['1_home'], event_type, bookie_id1, stake1,
                                          odds1, receipt1, False)

                        if bookie_id2.endswith(' lay'):
                            selection2 = (odds_type1, handicap_dict['2_home'], event_type, bookie_id2.split()[0], stake2,
                                          convert_back_lay_prices(odds2), receipt2, True)
                        else:
                            selection2 = (odds_type2, handicap_dict['2_away'], event_type, bookie_id2, stake2,
                                          odds2, receipt2, False)
                        arbi_opps.append((profit, (selection1, selection2)))
                    else:
                        break

        return arbi_opps

    @staticmethod
    def get_prices_by_position(bookie_odds_id_and_info, bookie_availability_dict, bet_period):
        home_prices = []  # [(bookie1, 2.1, receipt1), (bookie2, 2.0, receipt2), ...]
        away_prices = []
        # lay_bookie_prices_dict is for bookies which can offer lay prices
        # It looks like:
        # {'7': {'7': ([1.95, 2.0], 'a!1'), '7 lay': ([1.97, 2.02], 'b!2')}}
        # Be aware that [1.97, 2.02] are converted prices, not original ones.
        # for each back-lay price pair, we only get the best one.
        # e.g. for back price [x, y] and lay price [a, b],
        # we only get [x, b] if x and b are better than a and y.
        lay_bookie_prices_dict = {}
        for bookie_id, bookie_odds_info in bookie_odds_id_and_info.iteritems():
            prices, receipt, last_updated = bookie_odds_info
            price1, price2 = prices
            if bookie_id in bookie_availability_dict and bookie_availability_dict[bookie_id][bet_period] and \
                    price1 and price2:
                if bookie_id.endswith(' lay'):
                    price1_tmp = convert_back_lay_prices(price1, round_up=False)
                    price2_tmp = convert_back_lay_prices(price2, round_up=False)
                    price1, price2 = price2_tmp, price1_tmp
                if bookie_id.split()[0] in constants.BOOKIE_IDS_WITH_LAY_PRICES:
                    lay_bookie_prices_dict_dict = lay_bookie_prices_dict.get(bookie_id.split()[0], {})
                    lay_bookie_prices_dict_dict[bookie_id] = ([price1, price2], receipt)
                    lay_bookie_prices_dict[bookie_id.split()[0]] = lay_bookie_prices_dict_dict
                else:
                    home_prices.append((bookie_id, price1, receipt))
                    away_prices.append((bookie_id, price2, receipt))

        only_back_or_lay_prices_dict = get_better_price_from_back_lay_prices(lay_bookie_prices_dict)
        for home_info, away_info in only_back_or_lay_prices_dict.itervalues():
            home_prices.append(home_info)
            away_prices.append(away_info)
        home_prices.sort(key=lambda x: x[1], reverse=True)
        away_prices.sort(key=lambda x: x[1], reverse=True)

        return home_prices, away_prices

    @staticmethod
    def is_valid(bookie_id1, bookie_id2):
        if bookie_id1.split()[0] == bookie_id2.split()[0]:
            # 7 == 7 lay
            return False

        return True