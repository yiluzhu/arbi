from arbi import constants

from arbi.models.calculations import calculate_stakes
from arbi.strats.strat import BaseArbiStrategy


class DirectArbiCombinedStrategy(BaseArbiStrategy):
    # todo rewrite this strategy in pythonic way
    # todo support lay prices
    def get_top_price(self, price_dict, bookie_availability_dict, bet_period):
        best_home_bookie_id = None
        best_home_bookie_odds = 0
        best_away_bookie_id = None
        best_away_bookie_odds = 0
        best_home_receipt = ''
        best_away_receipt = ''
        for bookie_id, bookie_odds_info in price_dict.iteritems():
            if not bookie_availability_dict[bookie_id][bet_period] or bookie_id.endswith(' lay'):
                continue
            prices, receipt, last_updated = bookie_odds_info
            if prices[0] > best_home_bookie_odds:
                best_home_bookie_id = bookie_id
                best_home_bookie_odds = prices[0]
                best_home_receipt = receipt
            if prices[1] > best_away_bookie_odds:
                best_away_bookie_id = bookie_id
                best_away_bookie_odds = prices[1]
                best_away_receipt = receipt

        if best_home_bookie_id and best_away_bookie_id:
            return best_home_bookie_id, best_home_bookie_odds, best_home_receipt, best_away_bookie_id, best_away_bookie_odds, best_away_receipt

    def hcp_checker(self, line, hcp_dict, bookie_availability_dict, bet_period):
        plus_line = line + 0.25
        minus_line = line - 0.25
        if line in hcp_dict and plus_line in hcp_dict and minus_line in hcp_dict:
            plus_line_info = self.get_top_price(hcp_dict[plus_line], bookie_availability_dict, bet_period)
            minus_line_info = self.get_top_price(hcp_dict[minus_line], bookie_availability_dict, bet_period)
            if plus_line_info is None or minus_line_info is None:
                return

            plus_line_home_bookie_id, plus_line_home_price, plus_line_home_receipt, plus_line_away_bookie_id, plus_line_away_price, plus_line_away_receipt = plus_line_info
            minus_line_home_bookie_id, minus_line_home_price, minus_line_home_receipt, minus_line_away_bookie_id, minus_line_away_price, minus_line_away_receipt = minus_line_info

            if plus_line_home_price + minus_line_home_price == 0 or plus_line_away_price + minus_line_away_price == 0:
                return

            plus_line_home_split_pcent = minus_line_home_price / (plus_line_home_price + minus_line_home_price)
            minus_line_home_split_pcent = plus_line_home_price / (plus_line_home_price + minus_line_home_price)
            home_eodds = plus_line_home_split_pcent * plus_line_home_price * 2
            plus_line_away_split_pcent = minus_line_away_price / (plus_line_away_price + minus_line_away_price)
            minus_line_away_split_pcent = plus_line_away_price / (plus_line_away_price + minus_line_away_price)
            away_eodds = plus_line_away_split_pcent * plus_line_away_price * 2
            return (line,
                    [plus_line_home_bookie_id, plus_line_home_split_pcent, plus_line_home_receipt, minus_line_home_bookie_id, minus_line_home_split_pcent, minus_line_home_receipt],
                    [home_eodds, plus_line_home_price, minus_line_home_price],
                    [plus_line_away_bookie_id, plus_line_away_split_pcent, plus_line_away_receipt, minus_line_away_bookie_id, minus_line_away_split_pcent, minus_line_away_receipt],
                    [away_eodds, plus_line_away_price, minus_line_away_price]
                    )

    def hcp_filter(self, event_type, odds_type, odds_dict, bookie_availability_dict, bet_period):
        available_whole_lines = []
        hcp_dict = odds_dict.get((event_type, odds_type))
        if hcp_dict and len(hcp_dict.keys()) > 2:
            for i in range(-4, 5):
                res = self.hcp_checker(i, hcp_dict, bookie_availability_dict, bet_period)
                if res:
                    available_whole_lines.append(res)
        return available_whole_lines

    def split_stakes(self, event_type, odds_type, p_arb, side, stake):
        handicap, h_pcent_info, h_odds_info, a_pcent_info, a_odds_info = p_arb

        if side == 'H':
            m_type = odds_type + (' Home' if odds_type == 'AH' else ' Over')
            selection1 = m_type, handicap + 0.25, event_type, h_pcent_info[0], round(stake[0] * h_pcent_info[1], 2), h_odds_info[1], h_pcent_info[2], False
            selection2 = m_type, handicap - 0.25, event_type, h_pcent_info[3], round(stake[0] * h_pcent_info[4], 2), h_odds_info[2], h_pcent_info[5], False
            return selection1, selection2
        elif side == 'A':
            m_type = odds_type + (' Away' if odds_type == 'AH' else ' Under')
            selection1 = m_type, handicap + 0.25, event_type, a_pcent_info[0], round(stake[1] * a_pcent_info[1], 2), a_odds_info[1], a_pcent_info[2], False
            selection2 = m_type, handicap - 0.25, event_type, a_pcent_info[3], round(stake[1] * a_pcent_info[4], 2), a_odds_info[2], a_pcent_info[5], False
            return selection1, selection2
        else:
            m_type1 = odds_type + (' Home' if odds_type == 'AH' else ' Over')
            m_type2 = odds_type + (' Away' if odds_type == 'AH' else ' Under')
            selection1 = m_type1, handicap + 0.25, event_type, h_pcent_info[0], round(stake[0] * h_pcent_info[1], 2), h_odds_info[1], h_pcent_info[2], False
            selection2 = m_type1, handicap - 0.25, event_type, h_pcent_info[3], round(stake[0] * h_pcent_info[4], 2), h_odds_info[2], h_pcent_info[5], False
            selection3 = m_type2, handicap + 0.25, event_type, a_pcent_info[0], round(stake[1] * a_pcent_info[1], 2), a_odds_info[1], a_pcent_info[2], False
            selection4 = m_type2, handicap - 0.25, event_type, a_pcent_info[3], round(stake[1] * a_pcent_info[4], 2), a_odds_info[2], a_pcent_info[5], False
            return selection1, selection2, selection3, selection4

    def spot_arbi(self, match, bookie_availability_dict):
        odds_dict = match.odds.odds_dict
        arbi_opps = []
        bet_period = 'running ball' if match.is_in_running else 'dead ball'

        for event_type in ['FT', 'HT']:
            for odds_type in ['AH', 'OU']:
                available_whole_lines = self.hcp_filter(event_type, odds_type, odds_dict, bookie_availability_dict, bet_period)
                for p_arb in available_whole_lines:
                    handicap, h_pcent_info, h_odds_info, a_pcent_info, a_odds_info = p_arb
                    home_prices = [(-999, h_odds_info[0], '')]
                    away_prices = [(-999, a_odds_info[0], '')]
                    for bookie_id, bookie_odds_info in odds_dict[(event_type, odds_type)][handicap].iteritems():
                        prices, receipt, last_updated = bookie_odds_info
                        home_price, away_price = prices
                        if bookie_availability_dict[bookie_id][bet_period] and not bookie_id.endswith(' lay') and home_price and away_price:
                            home_prices.append((bookie_id, home_price, receipt))
                            away_prices.append((bookie_id, away_price, receipt))

                    home_prices.sort(key=lambda x: x[1], reverse=True)
                    away_prices.sort(key=lambda x: x[1], reverse=True)

                    for h_data, a_data in zip(home_prices, away_prices):
                        home_bookie_id, h_price, h_receipt = h_data
                        away_bookie_id, a_price, a_receipt = a_data

                        if home_bookie_id != -999:
                            h_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[home_bookie_id], 0)
                        else:
                            hb1_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[h_pcent_info[0]], 0)
                            hb2_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[h_pcent_info[3]], 0)
                            h_commission = hb1_commission if hb1_commission > hb2_commission else hb2_commission
                        if away_bookie_id != -999:
                            a_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[away_bookie_id], 0)
                        else:
                            ab1_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[a_pcent_info[0]], 0)
                            ab2_commission = constants.BOOKIE_COMMISSION_MAP.get(constants.BOOKIE_ID_MAP[a_pcent_info[3]], 0)
                            a_commission = ab1_commission if ab1_commission > ab2_commission else ab2_commission

                        result = calculate_stakes(h_price, a_price, h_commission, a_commission, self.profit_threshold)
                        if result and (home_bookie_id == -999 or away_bookie_id == -999):
                            stake1, stake2, profit = result
                            if home_bookie_id == -999 and away_bookie_id == -999:
                                selection1, selection2, selection3, selection4 = self.split_stakes(event_type, odds_type, p_arb, 'B', [stake1, stake2])
                                arbi_opps.append((profit, (selection1, selection2, selection3, selection4)))
                            elif home_bookie_id == -999:
                                selection1, selection2 = self.split_stakes(event_type, odds_type, p_arb, 'H', [stake1, stake2])
                                m_type = odds_type + (' Away' if odds_type == 'AH' else ' Under')
                                m_handicap = -1 * handicap if odds_type == 'AH' else handicap
                                selection3 = m_type, m_handicap, event_type, away_bookie_id, stake2, a_price, a_receipt, False
                                arbi_opps.append((profit, (selection1, selection2, selection3)))
                            elif away_bookie_id == -999:
                                m_type = odds_type + (' Home' if odds_type == 'AH' else ' Over')
                                selection1 = m_type, handicap, event_type, home_bookie_id, stake1, h_price, h_receipt, False
                                selection2, selection3 = self.split_stakes(event_type, odds_type, p_arb, 'A', [stake1, stake2])
                                arbi_opps.append((profit, (selection1, selection2, selection3)))
                            else:
                                break
                        else:
                            break

        return arbi_opps
