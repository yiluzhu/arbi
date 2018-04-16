import math
from arbi.strats.static_data.cross_handicap_strat_data import jolly_win_generics, jolly_win_wb12, non_poisson_adjustment

global_matrixSize = 11  # need to add 1
global_HcpSize = 11


def calc_SJD(stats):
    return (stats[0] + stats[1])/2.0, (stats[0] - stats[1])/2.0, (stats[0] + stats[1] + 0.01)/2.0, (stats[0] - stats[1] - 0.01)/2.0


def config(setting):
    home_adv = setting[0]
    home_rating = setting[1]
    away_adv = setting[2]
    true_goals = setting[3]
    suprem = home_adv + home_rating - away_adv
    jollyHG, dogHG, jollyHG_delta, dogHG_delta = calc_SJD([true_goals, suprem])
    return home_adv, home_rating, away_adv, suprem, jollyHG, dogHG, jollyHG_delta, dogHG_delta


def poisson_value(a, lam):
    return math.pow(lam, a) * math.exp(-lam) / math.factorial(a)


def db_poisson(nrow , ncol, deltaFlag, hg_info):
    jollyHG, dogHG, jollyHG_delta, dogHG_delta = hg_info
    db = [[0 for _ in range(ncol)] for _ in range(nrow)]
    for i in range(0, nrow):
        for j in range(0, ncol):
            if deltaFlag == 0:
                db[i][j] = poisson_value(i, jollyHG) * poisson_value(j, dogHG)
            else:
                db[i][j] = poisson_value(i, jollyHG_delta) * poisson_value(j, dogHG_delta)
    return db


def map_non_poisson_adjustments(value, index):
    if index == 1 or index == 2:
        nrow = 21

        i = 0
        while i < nrow:
            if value - non_poisson_adjustment[i][0] < 0:
                tmp_value = non_poisson_adjustment[i-1][index]
                return (tmp_value / 0.05 - int(tmp_value/0.05)) * (non_poisson_adjustment[i][index] - non_poisson_adjustment[i-1][index]) + non_poisson_adjustment[i-1][index]
            i += 1

        return -100.0
    else:
        return -100.0


def map_jolly_win_generics(value, index):
    if index == 1 or index == 2:
        nrow = 251
        i = 0
        while i < nrow:
            if value - jolly_win_generics[i][0] < 0:
                if i == 0:
                    return jolly_win_generics[0][index]
                else:
                    return jolly_win_generics[i-1][index]
            i += 1
        return -100.0
    else:
        return -100.0


def map_jolly_win_wb12(value, index):
    if index == 1 or index == 2:
        nrow = 261
        i = 0
        while i < nrow:
            if value - jolly_win_wb12[i][0] < 0:
                if i == 0:
                    return jolly_win_wb12[0][index]
                else:
                    return jolly_win_wb12[i-1][index]
            i += 1
        return -100.0
    else:
        return -100.0


def calc_hcp_price(index, j_mid, x_mid, d_mid, jwb1, jwb2):
    switcher = {
        0: d_mid / j_mid + 1.0,
        1: (j_mid + x_mid/2.0 + d_mid)/j_mid,
        2: 1.0 / j_mid,
        3: ((1 - j_mid) + (j_mid - jwb1 / 2.0)) / (j_mid - jwb1 / 2.0),
        4: (1.0 - j_mid)/(j_mid - jwb1) + 1.0,
        5: (jwb1 / 2.0 + (1.0 - jwb1)) / (j_mid - jwb1),
        6: 1.0 / (j_mid - jwb1),
        7: (1.0 - jwb2 / 2.0) / (j_mid - jwb1 - jwb2/2.0),
        8: (1.0 - jwb2) / (j_mid - jwb1 - jwb2),
        9: (1.0 - jwb2 / 2.0) / (j_mid - jwb1 - jwb2),
        10: 1.0 / (j_mid - jwb1 - jwb2)
    }
    return switcher.get(index, "HCP out of range.")


def calc_ou_price(ou_prob):
    total_slots = 11
    over_working_array = [0.0] * total_slots
    under_working_array = [0.0] * total_slots
    over_prices = [0.0] * total_slots
    under_prices = [0.0] * total_slots

    j = 0
    cnt = 0
    while j < total_slots:
        cnt += 1
        for i in range(0, cnt + 1):
            under_working_array[j] = under_working_array[j] + ou_prob[i]
        over_working_array[j] = 1.0 - under_working_array[j]
        j += 4

    j = 2
    cnt = 2
    while j < total_slots:
        under_working_array[j] = under_working_array[j-2] / (1.0 - ou_prob[cnt])
        over_working_array[j] = 1.0 - under_working_array[j]
        j += 4
        cnt += 1

    j = 1
    cnt = 2
    while j < total_slots:
        under_working_array[j] = under_working_array[j-1] / (1.0 - ou_prob[cnt]/2.0)
        over_working_array[j] = 1.0 - under_working_array[j]
        if j+2 < 11:
            under_working_array[j+2] = (under_working_array[j-1] + ou_prob[cnt]/2.0) / (1.0 - ou_prob[cnt]/2.0)
            over_working_array[j+2] = 1.0 - under_working_array[j+2]
        j += 4
        cnt += 1

    for i in range(0, total_slots):
        over_prices[i] = 1.0 / over_working_array[i]
        under_prices[i] = 1.0 / under_working_array[i]

    return over_prices, under_prices


def calc_expG(hedge_OU, hedge_odds):
    tmp_sum = 0.0
    ou_working_array = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    index = int(math.fabs(hedge_OU / 0.25) - 6)

    e = 1.0
    cnt = 0
    iterations = 10000

    for i in range(0, 6):
        if i == 5:
            ou_working_array[i] = 1.0 - tmp_sum
        else:
            ou_working_array[i] = poisson_value(i,e)
            tmp_sum += ou_working_array[i]
    over_array, under_array = calc_ou_price(ou_working_array)
    cnt += 1

    if hedge_OU <= 0:
        while index < len(over_array) and over_array[index] > hedge_odds and cnt <= iterations:
            tmp_sum = 0.0
            for i in range(0, 6):
                if i == 5:
                    ou_working_array[i] = 1.0 - tmp_sum
                else:
                    ou_working_array[i] = poisson_value(i,e)
                    tmp_sum += ou_working_array[i]
            over_array, under_array = calc_ou_price(ou_working_array)
            e += 0.001
            cnt += 1
    else:
        while index < len(under_array) and under_array[index] < hedge_odds and cnt <= iterations:
            tmp_sum = 0.0
            for i in range(0,6):
                if i == 5:
                    ou_working_array[i] = 1.0 - tmp_sum
                else:
                    ou_working_array[i] = poisson_value(i,e)
                    tmp_sum += ou_working_array[i]
            over_array, under_array = calc_ou_price(ou_working_array)
            e += 0.001
            cnt += 1
    return e


def get_prices(hedge_HCP, hedge_odds, tgValue, tgOdds, non_poisson_flag, to_bet_bool, to_hedge_bool):
    true_goals = calc_expG(tgValue, tgOdds)
    (home_adv, home_rating, away_adv, supremacy, jollyHG, dogHG, jollyHG_delta, dogHG_delta) = config([abs(hedge_HCP + (hedge_HCP + 1.35)), 0.0, 0.0, true_goals, 0.0, 0.0])

    run = 1
    while run:
        jollyHG, dogHG, jollyHG_delta, dogHG_delta = calc_SJD([true_goals, supremacy])
        poisson_matrix = db_poisson(global_matrixSize, global_matrixSize, 0, [jollyHG, dogHG, jollyHG_delta, dogHG_delta])
        jolly_mid = 0.0
        jolly_mid_by_one = 0.0
        jolly_mid_by_two = 0.0
        draw_mid = 0.0

        for i in range(global_matrixSize):
            for j in range(global_matrixSize):
                if i > j:
                    jolly_mid += poisson_matrix[i][j]
                    if (i-j) == 1:
                        jolly_mid_by_one += poisson_matrix[i][j]
                    if (i-j) == 2:
                        jolly_mid_by_two += poisson_matrix[i][j]
                else:
                    if i == j:
                        draw_mid += poisson_matrix[i][j]
        dog_mid = 1.0 - jolly_mid - draw_mid

        poisson_matrix_delta = db_poisson(global_matrixSize, global_matrixSize, 1, [jollyHG, dogHG, jollyHG_delta, dogHG_delta])
        jolly_delta = 0.0
        draw_delta = 0.0

        for i in range(0, global_matrixSize):
            for j in range(0, global_matrixSize):
                if i > j:
                    jolly_delta += poisson_matrix_delta[i][j]
                elif i == j:
                    draw_delta += poisson_matrix_delta[i][j]

        dog_delta = 1.0 - jolly_delta - draw_delta
        jolly_delta -= jolly_mid
        draw_delta -= draw_mid
        dog_delta -= dog_mid

        jolly_non_poisson_adjust = jolly_mid - map_non_poisson_adjustments(jolly_mid, 1)

        if non_poisson_flag:
            jolly_mid = jolly_non_poisson_adjust

        draw_mid = map_jolly_win_generics(jolly_mid, 1)

        dog_mid = 1.0 - jolly_mid - draw_mid
        wb1 = map_jolly_win_wb12(jolly_mid, 1)
        wb2 = map_jolly_win_wb12(jolly_mid, 2)

        jolly_hcp_array = [calc_hcp_price(i, jolly_mid, draw_mid, dog_mid, wb1, wb2) for i in range(global_HcpSize)]
        dog_hcp_array = [1.0 / (jolly_hcp_array[i] - 1.0) + 1.0 for i in range(global_HcpSize)]

        index = int(-1 * hedge_HCP / 0.25)
        diff = jolly_hcp_array[index] - hedge_odds

        if math.fabs(diff) < 1e-4:
            run = 0
        else:
            if jolly_hcp_array[index] > hedge_odds:
                if math.fabs(diff) < 0.001:
                    supremacy += 0.0001
                else:
                    supremacy += math.fabs(diff)
            else:
                if math.fabs(diff) < 0.001:
                    supremacy -= 0.0001
                else:
                    supremacy -= math.fabs(diff)

    return_dict = {}
    for i in range(global_HcpSize):
        if i == 0:
            if to_bet_bool:
                return_dict[0.0] = jolly_hcp_array[i]
            if to_hedge_bool:
                return_dict[0.0] = dog_hcp_array[i]
        else:
            if to_bet_bool:
                return_dict[-i * 0.25] = jolly_hcp_array[i]
            if to_hedge_bool:
                return_dict[i * 0.25] = dog_hcp_array[i]
    return return_dict
