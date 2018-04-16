# -*- coding: utf-8 -*-

import os
import time
import logging
import datetime
from importlib import import_module

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from arbi.constants import ROOT_PATH, SPORTTERY_REBATE
from arbi.tools.tc.constants import SCRAPER_TIMEOUT

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class Scraper(object):
    def __init__(self):
        path = os.path.join(ROOT_PATH, 'tools/tc/web/drivers/chromedriver.exe')
        self.driver = self.get_driver(path)
        self.driver.set_window_size(200, 200)

    @staticmethod
    def get_driver(path):
        return webdriver.Chrome(path)

    def get_driver_pid(self):
        return self.driver.service.process.pid

    def quit(self):
        self.driver.quit()


class SportteryScraper(Scraper):

    url_dict = {
        # football
        'eh_1x2_and_1x2': 'http://info.sporttery.cn/football/hhad_list.php',
        # right scores: http://info.sporttery.cn/football/cal_crs.htm
        # total goals: http://info.sporttery.cn/football/cal_ttg.htm
        # ft and ht combination: http://info.sporttery.cn/football/cal_hafu.htm

        # basketball
        '1or2': 'http://info.sporttery.cn/basketball/mnl_list.php',
        'AH': 'http://info.sporttery.cn/basketball/hdc_list.php',
        #pt_diff = 'http://info.sporttery.cn/basketball/wnm_list.php'
        'OU': 'http://info.sporttery.cn/basketball/hilo_list.php',
    }

    def scrape_football(self):
        return self.scrape(self.url_dict['eh_1x2_and_1x2'])

    def scrape_football_mock_data(self):
        log.info('Use Sporttery mock data.')
        odds_module_path = 'arbi.mock_data.sporttery.sporttery_odds'
        football_data = import_module(odds_module_path).sporttery_football_data
        return football_data

    def scrape(self, url):
        t0 = time.time()
        self.driver.get(url)
        try:
            elem_present = expected_conditions.visibility_of_element_located((By.ID, 'mainTbl'))
            WebDriverWait(self.driver, SCRAPER_TIMEOUT).until(elem_present)
        except exceptions.TimeoutException:
            log.warning('Timeout after %s seconds when scrape %s', time.time() - t0, url)
            return []

        loading_time = time.time() - t0
        try:
            elem = self.driver.find_element_by_id('mainTbl')
        except exceptions.NoSuchElementException:
            log.warning('NoSuchElementException when find element "mainTbl"')
            return []

        html = elem.get_attribute("innerHTML")
        soup = BeautifulSoup(html, 'html.parser')
        rows = soup.findChildren(['th', 'tr'])
        log.info('Found %s rows of match data from Sporttery website in %s seconds', len(rows), loading_time)
        match_list = self.get_match_data(rows)
        log.info('Scraped %s matches from Sporttery website', len(match_list))
        return match_list

    @staticmethod
    def get_effective_price(price, ret_pct=SPORTTERY_REBATE):
        """Apply discount to the price"""
        price = float(price)
        return round(((price - 1.0) / (1.0 - ret_pct)) + 1.0, 5) if price else 0

    def get_match_data(self, rows):
        match_list = []
        now = datetime.datetime.now()
        now_year = now.year
        now_month = now.month
        for row in rows:
            data_list = row.findAll(text=True)
            data_list_len = len(data_list)
            if data_list_len < 20:
                log.debug('Ignore non-match data row.')
                continue

            if data_list_len not in (30, 31, 32, 33, 34):  # normally 30 or 32, but can have u"未知" and/or notice
                log.warning('Found unknown data row format: %s', data_list)
                continue

            log.debug('Data list is: %s', data_list)

            if data_list_len in (31, 33, 34) and data_list[5] == u'未知':
                del data_list[5]

            league = data_list[2]
            year = now_year + 1 if (now_month == 12 and int(data_list[3].split('-')[0]) == 1) else now_year
            match_hk_time = '{}-{} {}'.format(year, data_list[3], data_list[4])
            if data_list_len in (30, 31):
                data_list.insert(6, '[]')
                data_list.insert(10, '[]')

            home = data_list[7]
            away = data_list[9]

            odds_dict = {}
            if data_list[11] == '0':
                no_hcp_prices = [self.get_effective_price(x) for x in data_list[13:16]]
                odds_dict[('FT', '1x2')] = {None: {'99': (no_hcp_prices, 'sporttery', 0)}}
            try:
                hcp = float(data_list[12])
            except UnicodeEncodeError:
                pass  # The second line of odds for this match is not available
            else:
                hcp_prices = [self.get_effective_price(x) for x in data_list[16:19]]
                odds_dict[('FT', 'EH')] = {hcp: {'99': (hcp_prices, 'sporttery', 0)}}

            if odds_dict:
                log.debug('Match data row is good')
                match_list.append((match_hk_time, league, home, away, odds_dict))

        return match_list


if __name__ == '__main__':
    t0 = time.time()
    scraper = SportteryScraper()
    data = scraper.scrape_football()
    print 'time elapsed in seconds:', time.time() - t0
    print '--data--', data
