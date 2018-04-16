import math


startLine = 0.5
totalIntGoals = 11
totalTGLines = int((totalIntGoals - 1) * 4 - 2)  # (2 + (startLine - 0.5)/0.25))


def calc_ou_price(ou_prob):
    over_working_array = [0.0] * totalTGLines
    under_working_array = [0.0] * totalTGLines

    over_prices = [0.0] * totalTGLines
    under_prices = [0.0] * totalTGLines

    j = 0
    cnt = 0
    while j < totalTGLines:
        cnt += 1
        for i in range(0, cnt):
            under_working_array[j] = under_working_array[j] + ou_prob[i]
        over_working_array[j] = 1.0 - under_working_array[j]
        j += 4

    j = 2
    cnt = 1
    while j < totalTGLines:
        under_working_array[j] = under_working_array[j-2] / (1.0 - ou_prob[cnt])
        over_working_array[j] = 1.0 - under_working_array[j]
        j += 4
        cnt += 1

    j = 1
    cnt = 1
    while j < totalTGLines:
        under_working_array[j] = under_working_array[j-1] / (1.0 - ou_prob[cnt]/2.0)
        over_working_array[j] = 1.0 - under_working_array[j]
        if j + 2 < totalTGLines:
            under_working_array[j+2] = (under_working_array[j-1] + ou_prob[cnt]/2.0) / (1.0 - ou_prob[cnt]/2.0)
            over_working_array[j+2] = 1.0 - under_working_array[j+2]
        j += 4
        cnt += 1

    for i in range(0, totalTGLines):
        over_prices[i] = 1.0 / over_working_array[i]
        under_prices[i] = 1.0 / under_working_array[i]

    return over_prices, under_prices


def poisson_value(a, e_goal):
    return math.pow(e_goal, a) * math.exp(-e_goal) / math.factorial(a)


def get_prices(hedge_OU, hedge_odds, sides, to_bet_bool, to_hedge_bool):
    tmp_sum = 0.0
    ou_working_array = [0.0] * totalIntGoals

    index = int(math.fabs(hedge_OU / 0.25) - 2)

    e = abs(hedge_OU) - 1.0
    cnt = 0
    iterations = 10000

    for i in range(0, totalIntGoals):
        if i == (totalIntGoals - 1):
            ou_working_array[i] = 1.0 - tmp_sum
        else:
            ou_working_array[i] = poisson_value(i,e)
            tmp_sum += ou_working_array[i]
    over_array, under_array = calc_ou_price(ou_working_array)
    cnt += 1

    if hedge_OU <= 0:
        while index < len(over_array) and over_array[index] > hedge_odds and cnt <= iterations:
            tmp_sum = 0.0
            for i in range(0, totalIntGoals):
                if i == (totalIntGoals - 1):
                    ou_working_array[i] = 1.0 - tmp_sum
                else:
                    ou_working_array[i] = poisson_value(i,e)
                    tmp_sum += ou_working_array[i]
            over_array, under_array = calc_ou_price(ou_working_array)
            e += 0.001
            cnt += 1
    else:
        while under_array[index] < hedge_odds and cnt <= iterations:
            tmp_sum = 0.0
            for i in range(0, totalIntGoals):
                if i == totalIntGoals - 1:
                    ou_working_array[i] = 1.0 - tmp_sum
                else:
                    ou_working_array[i] = poisson_value(i,e)
                    tmp_sum += ou_working_array[i]
            over_array, under_array = calc_ou_price(ou_working_array)
            e += 0.001
            cnt += 1

    return_dict = {}
    if cnt < iterations:
        if sides != 0:
            startIndex = max(0, index - sides)
            endIndex = min(totalTGLines, index + (sides + 1))
            if hedge_OU <= 0:
                if to_bet_bool:
                    for i in range(startIndex, endIndex):
                        if over_array[i] != 0.0:
                            return_dict[i * 0.25 + startLine] = over_array[i]
                if to_hedge_bool:
                    for i in range(startIndex, endIndex):
                        if under_array[i] != 0.0:
                            return_dict[i * 0.25 + startLine] = under_array[i]
            else:
                if to_bet_bool:
                    for i in range(startIndex, endIndex):
                        if under_array[i] != 0.0:
                            return_dict[i * 0.25 + startLine] = under_array[i]
                if to_hedge_bool:
                    for i in range(startIndex, endIndex):
                        if over_array[i] != 0.0:
                            return_dict[i * 0.25 + startLine] = over_array[i]
        else:
            if hedge_OU <= 0:
                if to_bet_bool:
                    for i in range(0, totalTGLines):
                        if over_array[i] != 0.0:
                            return_dict[i * 0.25 + startLine] = over_array[i]
                if to_hedge_bool:
                    for i in range(0, totalTGLines):
                        if under_array[i] != 0.0:
                            return_dict[i * 0.25 + startLine] = under_array[i]
            else:
                if to_bet_bool:
                    for i in range(0, totalTGLines):
                        if under_array[i] != 0.0:
                            return_dict[i * 0.25 + startLine] = under_array[i]
                if to_hedge_bool:
                    for i in range(0, totalTGLines):
                        if over_array[i] != 0.0:
                            return_dict[i * 0.25 + startLine] = over_array[i]
    return return_dict
