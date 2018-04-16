import math
from operator import itemgetter
from arbi import constants

from arbi.models.calculations import calculate_stakes
from arbi.strats import cross_handicap_hcp_prices
from arbi.strats import cross_handicap_tg_prices
from arbi.strats.strat import BaseArbiStrategy


class CrossHandicapArbiStrategy(BaseArbiStrategy):

    def get_top_price(self, price_dict):
        best_x_bookie_id = -999
        best_x_bookie_odds = 0.0
        best_y_bookie_id = -999
        best_y_bookie_odds = 0.0
        best_x_receipt = ''
        best_y_receipt = ''
        for bookie_id, bookie_odds_info in price_dict.iteritems():
            prices, receipt, last_updated = bookie_odds_info
            if prices[0] > best_x_bookie_odds:
                best_x_bookie_id = bookie_id
                best_x_bookie_odds = prices[0]
                best_x_receipt = receipt
            if prices[1] > best_y_bookie_odds:
                best_y_bookie_id = bookie_id
                best_y_bookie_odds = prices[1]
                best_y_receipt = receipt

        return best_x_bookie_id, best_x_bookie_odds, best_x_receipt, best_y_bookie_id, best_y_bookie_odds, best_y_receipt

    def hcp_checker(self, line, dict, return_list, ou_line, ou_odds):
        swap_jolly_bool = 0
        if line > 0: swap_jolly_bool = 1
        tmp_return_list = []
        best_hedge_line, best_hedge_odds = -999, -999
        if dict.keys() > 1:
            best_home_bookie_id, best_home_bookie_odds, best_home_receipt, best_away_bookie_id, best_away_bookie_odds, best_away_receipt = self.get_top_price(dict[line])
            if swap_jolly_bool:
                hedge_dict = cross_handicap_hcp_prices.get_prices(-1 * line, best_away_bookie_odds, ou_line, ou_odds, 0, 0, 1)
                for i in dict.keys():
                    current_line = i
                    if current_line != line:
                        home_bookie_id, home_bookie_odds, home_receipt, away_bookie_id, away_bookie_odds, away_receipt = self.get_top_price(dict[current_line])
                        if hedge_dict[current_line] < home_bookie_odds:
                            home_equivalent_line_price = -999
                            ret = cross_handicap_hcp_prices.get_prices(-current_line, 1.0 / (home_bookie_odds - 1.0) + 1.0, ou_line, ou_odds, 0, 0, 1)
                            best_hedge_line, best_hedge_odds, best_value = current_line, home_bookie_odds, ret[line]
                            if best_value > 0:
                                return_tuple = (current_line, 'AH', -line, best_value, [home_bookie_id, home_bookie_odds, home_receipt],
                                                [best_away_bookie_id, best_away_bookie_odds, best_away_receipt])
                                tmp_return_list.append(return_tuple)
            else:
                hedge_dict = cross_handicap_hcp_prices.get_prices(line, best_home_bookie_odds, ou_line, ou_odds, 0, 0, 1)
                for i in dict.keys():
                    current_line = i
                    if current_line != line:
                        home_bookie_id, home_bookie_odds, home_receipt, away_bookie_id, away_bookie_odds, away_receipt = self.get_top_price(dict[current_line])
                        if -current_line in hedge_dict and hedge_dict[-current_line] < away_bookie_odds:
                            ret = cross_handicap_hcp_prices.get_prices(current_line, 1.0 / (away_bookie_odds - 1.0) + 1.0, ou_line, ou_odds, 0, 0, 1)
                            best_hedge_line, best_hedge_odds, best_value = current_line, away_bookie_odds, ret[-line]
                            if best_value > 0:
                                return_tuple = (line, 'AH', -current_line, best_value, [best_home_bookie_id, best_home_bookie_odds, best_home_receipt],
                                                [away_bookie_id, away_bookie_odds, away_receipt])
                                tmp_return_list.append(return_tuple)
            if len(tmp_return_list) > 1:
                best_return = max(tmp_return_list, key=itemgetter(3))
                return best_return
            elif len(tmp_return_list) == 1:
                return tmp_return_list[0]
            else:
                return []

    def ou_checker(self, line, ou_dict, return_list):
        if ou_dict.keys() > 1:
            best_over_bookie_id, best_over_bookie_odds, best_over_receipt, best_under_bookie_id, best_under_bookie_odds, best_under_receipt = self.get_top_price(ou_dict[line])
            best_odds = best_over_bookie_odds
            hedge_dict = cross_handicap_tg_prices.get_prices(-line, best_over_bookie_odds, 0, 0, 1)
            tmp_return_list = []
            best_hedge_line, best_hedge_odds = -999, -999
            for i in ou_dict.keys():
                current_line = i
                if current_line != line:
                    over_bookie_id, over_bookie_odds, over_receipt, under_bookie_id, under_bookie_odds, under_receipt = self.get_top_price(ou_dict[current_line])
                    if hedge_dict[current_line] < under_bookie_odds:
                        ret = cross_handicap_tg_prices.get_prices(-current_line, 1.0 / (under_bookie_odds - 1.0) + 1.0, 0, 0, 1)
                        if line not in ret:
                            continue
                        best_hedge_line, best_hedge_odds, best_value = current_line, under_bookie_odds, ret[line]
                        if best_value > 0:
                            return_tuple = (line, 'OU', current_line, best_value, [best_over_bookie_id, best_over_bookie_odds, best_over_receipt],
                                            [under_bookie_id, under_bookie_odds, under_receipt])
                            tmp_return_list.append(return_tuple)
            if len(tmp_return_list) > 1:
                best_return = max(tmp_return_list, key=itemgetter(3))
                return best_return, best_odds
            elif len(tmp_return_list) == 1:
                return tmp_return_list[0], best_odds
            else:
                return [], -999

    def hcp_filter(self, event_type, odds_dict):
        available_arbs = []
        hcp_dict = odds_dict.get((event_type, 'AH'))
        ou_dict = odds_dict.get((event_type, 'OU'))
        best_ou_odds = -999
        if ou_dict:
            ou_index = int(math.floor(len(ou_dict.keys()) / 2.0))
            ou_key_list = sorted(ou_dict.keys())
            ou_line = ou_key_list[ou_index]
            ret, best_ou_odds = self.ou_checker(ou_line, ou_dict, available_arbs)
            if best_ou_odds != -999:
                available_arbs.append(ret)
            if hcp_dict and best_ou_odds > 0 and len(hcp_dict.keys()) > 1:
                hcp_index = int(math.floor(len(hcp_dict.keys()) / 2.0))
                hcp_key_list = sorted(hcp_dict.keys())
                ret = self.hcp_checker(hcp_key_list[hcp_index], hcp_dict, available_arbs, ou_line, best_ou_odds)
                available_arbs.append(ret)
        return available_arbs

    def spot_arbi(self, match, bookie_availability_dict):
        arbi_opps = []
        if not match.is_in_running and match.odds:
            arbi_opps = self.spot_arbi_both(match.odds.odds_dict, bookie_availability_dict, 'dead ball')
        return arbi_opps

    def spot_arbi_both(self, odds_dict, bookie_availability_dict, bet_period):
        arbi_opps = []
        if bet_period == 'dead ball':
            for event_type in ['FT', 'HT']:
                possible_arbs = self.hcp_filter(event_type, odds_dict)
                if possible_arbs != []:
                    for p_arb in possible_arbs:
                        if not p_arb:
                            continue
                        line, market_type, hedge_line, hedge_equivalent_line_price, x_info, y_info = p_arb
                        if market_type == 'AH':
                            if line < 0:
                                bet_bookie_id, bet_bookie_odds, bet_receipt = x_info
                                hedge_bookie_id, hedge_bookie_odds, hedge_receipt = y_info
                                bet_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[bet_bookie_id], 0)
                                hedge_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[hedge_bookie_id], 0)
                                result = calculate_stakes(bet_bookie_odds, hedge_equivalent_line_price, bet_commission, hedge_commission, 0.005)
                                if result:
                                    stake1, stake2, profit = result
                                    selection1 = (market_type + ' Home', line, event_type, bet_bookie_id, stake1, bet_bookie_odds, bet_receipt, False)
                                    selection2 = (market_type + ' Away', hedge_line, event_type, hedge_bookie_id, stake2, hedge_bookie_odds, hedge_receipt, False)
                                    arbi_opps.append((profit, (selection1, selection2)))
                                else:
                                    break
                            else:
                                bet_bookie_id, bet_bookie_odds, bet_receipt = y_info
                                hedge_bookie_id, hedge_bookie_odds, hedge_receipt = x_info
                                bet_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[bet_bookie_id], 0)
                                hedge_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[hedge_bookie_id], 0)
                                result = calculate_stakes(bet_bookie_odds, hedge_equivalent_line_price, bet_commission, hedge_commission, 0.005)
                                if result:
                                    stake1, stake2, profit = result
                                    selection1 = market_type + ' Home', line, event_type, hedge_bookie_id, stake2, hedge_bookie_odds, hedge_receipt, False
                                    selection2 = market_type + ' Away', hedge_line, event_type, bet_bookie_id, stake1, bet_bookie_odds, bet_receipt, False
                                    arbi_opps.append((profit, (selection1, selection2)))
                                else:
                                    break
                        elif market_type == 'OU':
                            bet_bookie_id, bet_bookie_odds, bet_receipt = x_info
                            hedge_bookie_id, hedge_bookie_odds, hedge_receipt = y_info
                            bet_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[bet_bookie_id], 0)
                            hedge_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[hedge_bookie_id], 0)
                            result = calculate_stakes(bet_bookie_odds, hedge_equivalent_line_price, bet_commission, hedge_commission, 0.005)
                            if result:
                                stake1, stake2, profit = result
                                selection1 = market_type + ' Over', line, event_type, bet_bookie_id, stake1, bet_bookie_odds, bet_receipt, False
                                selection2 = market_type + ' Under', hedge_line, event_type, hedge_bookie_id, stake2, hedge_bookie_odds, hedge_receipt, False
                                arbi_opps.append((profit, (selection1, selection2)))
                            else:
                                break
                        else:
                            break
                return arbi_opps
