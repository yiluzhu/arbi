# -*- coding: GBK -*-

import logging
import datetime
from threading import RLock
from arbi.models.odds import Odds
from arbi.models.data_utils import get_sport_type
from arbi.models.record import MatchInfoRecord, InitOddsRecord


log = logging.getLogger(__name__)
log.setLevel(logging.WARN)
log.addHandler(logging.StreamHandler())


class Match(object):
    """This represents one match. It contains all the odds from all bookies for that match
    """
    def __init__(self, match_record):
        self.id = match_record.record_dict['match_id']
        self.info = match_record.record_dict
        self.odds = None
        self.sport_type = get_sport_type(self.info)

        self.update_match_info_last_updated()

    def clear_all_prices(self):
        if self.odds:
            self.odds.odds_dict.clear()

    @property
    def is_in_running(self):
        if self.info:
            return self.info['is_in_running']

    def update_match_info_last_updated(self):
        self.match_info_last_updated = datetime.datetime.utcnow()

    def init_update(self, record):
        """This function is only used when process initial packet
        """
        if isinstance(record, MatchInfoRecord):
            self.info = record.record_dict
            self.update_match_info_last_updated()
        elif isinstance(record, InitOddsRecord):
            goal_diff = self.info['home_team_score'] - self.info['away_team_score']
            if self.odds:
                self.odds.update_with_dict(record.record_dict, goal_diff)
            else:
                self.odds = Odds(record.record_dict, goal_diff)
        else:
            log.error(u'Should not have UpdateOddsRecord in an initial packet: {0}'.format(record.record_str))

    def update_with_record(self, record):
        """Apply latest record from feed"""
        if isinstance(record, InitOddsRecord):
            log.error(u'Should not have InitOddsRecord in a update packet: {0}'.format(record.record_str))
        elif isinstance(record, MatchInfoRecord):
            if self.info and self.in_running_match_scored(record):
                self.clear_all_prices()
            self.info = record.record_dict
            self.info_str = record.record_str
            self.update_match_info_last_updated()
        else:
            goal_diff = self.info['home_team_score'] - self.info['away_team_score'] if self.info else None
            if self.odds:
                self.odds.update_with_dict(record.record_dict, goal_diff)
            else:
                self.odds = Odds(record.record_dict, goal_diff)

    def in_running_match_scored(self, match_info_record):
        if self.is_in_running:
            current_home_score = self.info['home_team_score']
            current_away_score = self.info['away_team_score']
            new_home_score = match_info_record.record_dict['home_team_score']
            new_away_score = match_info_record.record_dict['away_team_score']
            home_team = self.info['home_team_name']
            away_team = self.info['away_team_name']

            if new_home_score - current_home_score > 1 or new_away_score - current_away_score > 1:
                try:
                    log.error('Wrong scores for match {} vs {}! Were {}:{}, now {}:{}'.format(
                        home_team, away_team, current_home_score, current_away_score, new_home_score, new_away_score
                    ))
                except UnicodeEncodeError:
                    pass

            if current_home_score == -1 or current_away_score == -1:
                try:
                    log.warning('In running match {} vs {} had scores {}:{}'.format(
                        home_team, away_team, current_home_score, current_away_score
                    ))
                except UnicodeEncodeError:
                    pass

            else:
                return new_home_score - current_home_score >= 1 or new_away_score - current_away_score >= 1
