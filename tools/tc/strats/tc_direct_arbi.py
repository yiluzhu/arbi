from arbi import constants
from arbi.strats.strat import STRAT_ID_MAP
from arbi.models.calculations import calculate_stakes, convert_back_lay_prices, get_better_price_from_back_lay_prices


class TCDirectArbiStrategy(object):

    def __init__(self, profit_threshold=constants.MINI_PROFIT):
        self.profit_threshold = profit_threshold
        self.id = STRAT_ID_MAP[self.__class__.__name__]

    def spot_arbi(self, match):
        odds_dict = match.odds.odds_dict
        arbi_opps = []
        for (event_type, odds_type), odds_by_category in odds_dict.iteritems():
            if odds_type in ('AH', 'OU'):
                arbi_opps += self.spot_direct_arb_for_AH_and_OU(event_type, odds_type, odds_by_category, self.profit_threshold)
            if odds_type == '1x2':
                arbi_opps += self.spot_direct_arb_for_1x2(event_type, odds_by_category, self.profit_threshold)

        return arbi_opps

    @staticmethod
    def spot_direct_arb_for_1x2(event_type, odds_by_category, profit_threshold):
        """This can only happens between back and lay prices from different bookies,

        e.g. Home back (sbo) vs Home lay (betfair)
        """
        arbi_opps = []
        home_sporttery_price = None
        draw_sporttery_price = None
        away_sporttery_price = None
        home_lay_prices_converted = []
        draw_lay_prices_converted = []
        away_lay_prices_converted = []
        bookie_odds_id_and_info = odds_by_category.get(None)
        if not bookie_odds_id_and_info:
            return []

        for bookie_id, bookie_odds_info in bookie_odds_id_and_info.iteritems():
            prices, receipt, last_updated = bookie_odds_info
            home_price, draw_price, away_price = prices
            if home_price and draw_price and away_price:
                if bookie_id.endswith(' lay'):
                    home_lay_price_converted = convert_back_lay_prices(home_price, round_up=False)
                    draw_lay_price_converted = convert_back_lay_prices(draw_price, round_up=False)
                    away_lay_price_converted = convert_back_lay_prices(away_price, round_up=False)
                    home_lay_prices_converted.append((bookie_id, home_lay_price_converted))
                    draw_lay_prices_converted.append((bookie_id, draw_lay_price_converted))
                    away_lay_prices_converted.append((bookie_id, away_lay_price_converted))
                elif bookie_id in constants.BOOKIE_IDS_WITH_LAY_PRICES:
                    pass  # we don't use it if the bookie_id could appear on lay side
                elif bookie_id == '99':
                    home_sporttery_price = home_price
                    draw_sporttery_price = draw_price
                    away_sporttery_price = away_price

        if not home_lay_prices_converted or not draw_lay_prices_converted or not away_lay_prices_converted:
            return []

        for seq in [home_lay_prices_converted, draw_lay_prices_converted, away_lay_prices_converted]:
            seq.sort(key=lambda x: x[1], reverse=True)

        for sporttery_price, lay_prices, sub_type_flag in [(home_sporttery_price, home_lay_prices_converted, 'Home'),
                                                            (draw_sporttery_price, draw_lay_prices_converted, 'Draw'),
                                                            (away_sporttery_price, away_lay_prices_converted, 'Away')]:
            if sporttery_price is None:
                continue

            for lay_bookie_id, lay_price in lay_prices:
                commission1 = 0
                commission2 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[lay_bookie_id], 0)
                result = calculate_stakes(sporttery_price, lay_price, commission1, commission2, profit_threshold)
                if result:
                    stake1, stake2, profit = result
                    selection1 = ('1x2', sub_type_flag, event_type, '99', stake1, sporttery_price, '', False)
                    selection2 = ('1x2', sub_type_flag, event_type, lay_bookie_id[:-4], stake2, convert_back_lay_prices(lay_price), '', True)
                    arbi_opps.append((profit, (selection1, selection2)))

        return arbi_opps

    @staticmethod
    def spot_direct_arb_for_AH_and_OU(event_type, odds_type, odds_by_category, profit_threshold):
        arbi_opps = []
        odds_type1 = '{} {}'.format(odds_type, {'AH': 'Home', 'OU': 'Over'}[odds_type])
        odds_type2 = '{} {}'.format(odds_type, {'AH': 'Away', 'OU': 'Under'}[odds_type])
        for handicap, bookie_odds_id_and_info in odds_by_category.iteritems():
            home_prices, away_prices, home_sporttery_price, away_sporttery_price = TCDirectArbiStrategy.get_prices_by_position(bookie_odds_id_and_info)
            if home_sporttery_price is None or away_sporttery_price is None:
                continue

            away_handicap = handicap * -1 if odds_type == 'AH' else handicap

            # Find opportunities with away_sporttery_price
            for bookie_id1, odds1, receipt1 in home_prices:
                commission1 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[bookie_id1], 0)
                commission2 = 0
                result = calculate_stakes(odds1, away_sporttery_price, commission1, commission2, profit_threshold)
                if result:
                    stake1, stake2, profit = result
                    handicap_dict = {}
                    for _id, idx in [(bookie_id1, '1'), ('99', '2')]:
                        if _id in ['7', '7 lay'] and odds_type == 'AH':
                            handicap_dict[idx + '_home'] = handicap
                            handicap_dict[idx + '_away'] = handicap * -1
                        else:
                            handicap_dict[idx + '_home'] = handicap
                            handicap_dict[idx + '_away'] = away_handicap

                    if bookie_id1.endswith(' lay'):
                        selection1 = (odds_type2, handicap_dict['1_away'], event_type, bookie_id1.split()[0], stake1,
                                      convert_back_lay_prices(odds1), '', True)
                    else:
                        selection1 = (odds_type1, handicap_dict['1_home'], event_type, bookie_id1, stake1,
                                      odds1, '', False)

                    selection2 = (odds_type2, handicap_dict['2_away'], event_type, '99', stake2,
                                  away_sporttery_price, '', False)

                    arbi_opps.append((profit, (selection1, selection2)))
                else:
                    break

            # Find opportunities with home_sporttery_price
            for bookie_id2, odds2, receipt2 in away_prices:
                commission1 = 0
                commission2 = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[bookie_id2], 0)
                result = calculate_stakes(home_sporttery_price, odds2, commission1, commission2, profit_threshold)
                if result:
                    stake1, stake2, profit = result
                    handicap_dict = {}
                    for _id, idx in [('99', '1'), (bookie_id2, '2')]:
                        if _id in ['7', '7 lay'] and odds_type == 'AH':
                            handicap_dict[idx + '_home'] = handicap
                            handicap_dict[idx + '_away'] = handicap * -1
                        else:
                            handicap_dict[idx + '_home'] = handicap
                            handicap_dict[idx + '_away'] = away_handicap

                    selection1 = (odds_type1, handicap_dict['1_home'], event_type, '99', stake1,
                                  home_sporttery_price, '', False)

                    if bookie_id2.endswith(' lay'):
                        selection2 = (odds_type1, handicap_dict['2_home'], event_type, bookie_id2.split()[0], stake2,
                                      convert_back_lay_prices(odds2), '', True)
                    else:
                        selection2 = (odds_type2, handicap_dict['2_away'], event_type, bookie_id2, stake2,
                                      odds2, '', False)
                    arbi_opps.append((profit, (selection1, selection2)))
                else:
                    break

        return arbi_opps

    @staticmethod
    def get_prices_by_position(bookie_odds_id_and_info):
        home_prices = []  # [(bookie1, 2.1, receipt1), (bookie2, 2.0, receipt2), ...]
        away_prices = []
        home_sporttery_price = None
        away_sporttery_price = None
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
            if price1 and price2:
                if bookie_id.endswith(' lay'):
                    price1_tmp = convert_back_lay_prices(price1, round_up=False)
                    price2_tmp = convert_back_lay_prices(price2, round_up=False)
                    price1, price2 = price2_tmp, price1_tmp

                if bookie_id.split()[0] in constants.BOOKIE_IDS_WITH_LAY_PRICES:
                    lay_bookie_prices_dict_dict = lay_bookie_prices_dict.get(bookie_id.split()[0], {})
                    lay_bookie_prices_dict_dict[bookie_id] = ([price1, price2], receipt)
                    lay_bookie_prices_dict[bookie_id.split()[0]] = lay_bookie_prices_dict_dict
                elif bookie_id == '99':
                    home_sporttery_price = price1
                    away_sporttery_price = price2
                else:
                    home_prices.append((bookie_id, price1, receipt))
                    away_prices.append((bookie_id, price2, receipt))

        only_back_or_lay_prices_dict = get_better_price_from_back_lay_prices(lay_bookie_prices_dict)
        for home_info, away_info in only_back_or_lay_prices_dict.itervalues():
            home_prices.append(home_info)
            away_prices.append(away_info)
        home_prices.sort(key=lambda x: x[1], reverse=True)
        away_prices.sort(key=lambda x: x[1], reverse=True)

        return home_prices, away_prices, home_sporttery_price, away_sporttery_price
