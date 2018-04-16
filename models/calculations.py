"""
A collection of functions to do various math.
"""

from arbi.constants import MINI_PROFIT

def calculate_stakes(odds1, odds2, commission1=0, commission2=0, profit_threshold=MINI_PROFIT):
    """Given two odds p1, p2 and commissions c1, c2,
    calculate if they can be used for arbitrage. If so, how to distribute stake.

    If the stakes for p1, p2 are s1, s2 then it is arbitrage when:
        side1 win:
            side1 winning(include base): p1 * s1
            side1 commission: c1 * s1
            side2 commission: c2 * s2
        side2 win
            side2 winning(include base): p2 * s2
            side2 commission: c2 * s2
            side1 commission: c1 * s1

        therefore:
            p1 * s1 + c1 * s1 + c2 * s2 = p2 * s2 + c2 * s2 + c1 * s1 > x + y

    Algorithm: assume total stake is 100, then
        s1 + s2 = 100
        s1/s2 = p2/p1
    => x = 100 * p2 / (p1 + p2)
    if p1 * s1 + c1 * s1 + c2 * s2 > 100, it is arbitrage

    About commission:
    Assume it's c then when the betting stake s, we guarantee to get s * c back regardless win or lose.
    e.g. if odds is 2.02, commission 0.25%, when bet 100, we could win 102.25 or lose 99.75
    """
    stake1 = 100 * odds2 / (odds1 + odds2)
    stake2 = 100 - stake1

    winning_with_base = (odds1 + commission1) * stake1 + commission2 * stake2
    if winning_with_base >= 100 * (1 + profit_threshold):
        profit = round((winning_with_base - 100) / 100, 5)
        return round(stake1, 1), round(stake2, 1), profit


def calculate_stakes_new(k1, k2, k3, c1=0, c2=0, c3=0, profit_threshold=MINI_PROFIT):
    """Given price1, price2, price3 and their related commissions, can we create arbitrage opportunities?
    """
    k1 *= 1 + c1
    k2 *= 1 + c2
    k3 *= 1 + c3

    arb_condition = 1.0/k1 + 1.0/k2 + 1.0/k3
    if arb_condition < 1 - profit_threshold:
        stake1 = round(100 / (arb_condition * k1), 1)
        stake2 = round(100 / (arb_condition * k2), 1)
        stake3 = round(100 / (arb_condition * k3), 1)
        profit = round(1/arb_condition - 1, 5)
        return stake1, stake2, stake3, profit


def convert_back_lay_prices(price, round_up=True):
    """This function does both back -> lay and lay -> back convertion.
    """
    return round(1 / (price - 1) + 1, 2) if round_up else 1 / (price - 1) + 1


def get_better_price_from_back_lay_prices(back_lay_prices_dict):
    """back_lay_prices_dict look like this:
    {'7':
        {'7': ([1.95, 2.0], 'a!1),
         '7 lay': ([1.94, 2.02], 'b!2'),
        }
    }

    Return a dict of pairs, with each pair only contains the better price for home-away from back-lay prices, like this:
    {'7':
        [('7', 1.95, 'a!1'), ('7 lay', 2.02, 'b!2')]
    }

    Please note that the lay prices are converted prices, not original ones.
    """
    only_back_or_lay_prices_dict = {}
    for bookie_id, bookie_prices_dict in back_lay_prices_dict.iteritems():
        if bookie_id in bookie_prices_dict and bookie_id + ' lay' in bookie_prices_dict:
            [home_back_price, away_back_price], back_receipt = bookie_prices_dict[bookie_id]
            [home_lay_price, away_lay_price], lay_receipt = bookie_prices_dict[bookie_id + ' lay']
            home_info = (bookie_id, home_back_price, back_receipt) if home_back_price > home_lay_price else (bookie_id + ' lay', home_lay_price, lay_receipt)
            away_info = (bookie_id, away_back_price, back_receipt) if away_back_price > away_lay_price else (bookie_id + ' lay', away_lay_price, lay_receipt)
            only_back_or_lay_prices_dict[bookie_id] = [home_info, away_info]
        else:  # either back or lay is in, but not both
            assert len(bookie_prices_dict) == 1
            the_bookie_id = bookie_prices_dict.keys()[0]
            [home_price, away_price], receipt = bookie_prices_dict[the_bookie_id]
            only_back_or_lay_prices_dict[bookie_id] = [(the_bookie_id, home_price, receipt), (the_bookie_id, away_price, receipt)]

    return only_back_or_lay_prices_dict

