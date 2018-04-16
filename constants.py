# -*- coding: utf-8 -*-
import os
from itertools import product

####################################
# General constants
VERSION = '0.15.12'

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))  # E:/works/yan/code/arbi

SCREEN_SIZE = (1920, 950)
SCREEN_SIZE_SMALL = (1024, 768)

MAX_ODDS = 50.0
MAX_BOOKIES_FOR_EACH_CATEGORY = 5
SLEEP_BEFORE_RECONNECT = 15
MINI_PROFIT = 0.01
THREAD_ALIVE_CHECK_INTERVAL = 10
RB_PRICE_EXPIRY_TIME = 30  # seconds
RB_PRICE_EXPIRY_CHECK_INTERVAL = 5  # seconds
PROCESS_EXEC_MSG_MAX_TIME = 0.5  # seconds
EMPTY_SRC_Q_SLEEP_TIME = 0.02
SPORTTERY_REBATE = 0.08

NO_REPEAT_OPPS_IN_HISTORIC_VIEW_TIME_FRAME = 60 * 60 * 6
#####################################

#####################################
# Bookie constants
BOOKIE_ID_MAP = {
    '1': 'crown_c',
    '2': 'sbobet',
    '5': 'ibcbet',
    '7': 'betfair',
    '7 lay': 'betfair',
    '15': 'crown_d',
    '37': 'isn',
    '52': 'm8bet',
    '59': 'tl',
    '62': 'ga',
    '69': 'pinnacle',
    '99': 'sporttery',
}

VIP_ALL_BOOKIES_ID_MAP = {
    '10': 'macau',
    '11': 'bc080',
    '25': 'ssbet',
    '26': '188bet',
    '30': 'winningft',
    '31': 'cmdbt',
    '38': 'ibet',
    '43': 'foobet',
    '46': 'foobet2',
    '47': 'newbb',
    '49': 'sin88',
    '50': 'toutou',
    '53': 'sh2828',
}
VIP_ALL_BOOKIES_ID_MAP.update(BOOKIE_ID_MAP)  # used by oh tool

# traditional AH counts current scores (e.g. most asian bookies),
# while non traditional AH doesn't count current scores (e.g. betfair)
NON_TRADITIONAL_AH_BOOKIE_IDS = ['7']
BOOKIE_IDS_WITH_LAY_PRICES = ['7']

BOOKIE_COMMISSION_MAP = {
    'crown_c': 0.0075,
    'sbobet': 0.0025,
    'ibcbet': 0.0025,
    'pinnacle': 0.0025,
    'betfair': -0.02,
}

BOOKIE_NAME_CN_MAP = {
    'crown_c': u'皇冠_C',
    'sbobet': u'利记',
    'ibcbet': u'沙巴',
    'macau': u'澳门',
    'crown_d': u'皇冠_D',
    'pinnacle': u'平博',
    'winningft': u'微能',
    'isn': u'智博',
    'foobet': u'富博',
    'foobet2': u'富博2',
    'betfair': u'必发',
    'tl': u'天龙',
    'ga': u'星际',
    'sporttery': u'竞彩网',
}
#########################################

#########################################
# UI Column settings #
get_selection_header = lambda n: [header + str(n) for header in
                        ['Type', 'Subtype', 'F/HT', 'Bookie', 'Bookie CN', 'Stake', 'Raw Odds', 'Effective Odds', 'Commission', 'Lay Flag']]

ARBI_SUMMARY_HEADER = ['Single Market', 'Strategy', 'Profit', 'Occurred (HK Time)',
                       'League', 'League CN', 'Home', 'Home CN', 'Home Score', 'Away Score', 'Away', 'Away CN',
                       ] + sum([get_selection_header(n) for n in [1, 2, 3]], [])

KEPT_COLUMNS = ['Profit', 'Occurred (HK Time)', 'League', 'League CN', 'Home', 'Home CN', 'Away', 'Away CN'] + [
    header + str(n) for n, header in product([1, 2, 3], ['Type', 'Subtype', 'F/HT', 'Bookie CN', 'Stake', 'Raw Odds', 'Effective Odds', 'Lay Flag'])]

HIDDEN_COLUMNS = [column for column in ARBI_SUMMARY_HEADER if column not in KEPT_COLUMNS]

ARBI_SUMMARY_BOOKIE1_INDEX = ARBI_SUMMARY_HEADER.index('Bookie1')
ARBI_SUMMARY_BOOKIE2_INDEX = ARBI_SUMMARY_HEADER.index('Bookie2')
ARBI_SUMMARY_BOOKIE3_INDEX = ARBI_SUMMARY_HEADER.index('Bookie3')
ARBI_SUMMARY_LEAGUE_INDEX = ARBI_SUMMARY_HEADER.index('League')
ARBI_SUMMARY_HOME_TEAM_INDEX = ARBI_SUMMARY_HEADER.index('Home')
ARBI_SUMMARY_AWAY_TEAM_INDEX = ARBI_SUMMARY_HEADER.index('Away')

DEFAULT_COLUMN_WIDTH = 55

COLUMN_WIDTH_DICT = {
    'Occurred (HK Time)': 140,
    'League': 70,
    'League CN': 70,
    'Home': 80,
    'Home CN': 85,
    'Away': 80,
    'Away CN': 85,
    'Type': 70,
    'Subtype': 45,
    'F/HT': 30,
    'Raw Odds': 50,
    'Lay Flag': 40,
}
