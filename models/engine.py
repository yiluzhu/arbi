import logging
import datetime
from threading import RLock
from arbi.models.match import Match
from arbi.models.record import MatchInfoRecord


log = logging.getLogger(__name__)
log.setLevel(logging.WARN)
log.addHandler(logging.StreamHandler())


class DataEngine(object):
    def __init__(self):
        # this overall dict can not have sub categories like "football", "basketball"
        # because the update records do not have sport type information.
        self.match_dict = {}
        self.last_clear_time = datetime.datetime.utcnow()
        self.match_dict_lock = RLock()

    def get_inspector_table(self):
        return sorted([[match.id, match.info['is_in_running'],
                        match.info['running_time'], match.info['league_name'], match.info['league_name_trad'],
                        match.info['home_team_name'], match.info['home_team_name_trad'], match.info['home_team_score'],
                        match.info['away_team_score'], match.info['away_team_name'], match.info['away_team_name_trad'],
                        ] for match_id, match in self.match_dict.iteritems() if match.info and match.odds],
                      key=lambda x: x[0])

    def clear_data(self):
        with self.match_dict_lock:
            self.match_dict.clear()

    def is_it_time_to_clear(self):
        return datetime.datetime.utcnow() - self.last_clear_time > datetime.timedelta(minutes=5)

    def init_match_dict(self, init_dict):
        self.match_dict.update(init_dict)

    def update_match_dict(self, record_list):
        """Update match dict.

        :param record_list: a list of record objects
        """
        if isinstance(record_list, dict):
            # When switch vip server, vip feed thread will send init dict again. We ignore it.
            return
        if record_list is None:
            # We've seen this error before but it shouldn't happen in theory
            return
        for record in record_list:
            match_id = record.record_dict['match_id']
            if match_id in self.match_dict:
                old_match = self.match_dict[match_id]
                old_match.update_with_record(record)
            elif isinstance(record, MatchInfoRecord):
                self.match_dict[match_id] = Match(record)

    def should_match_be_cleared(self, match):
        if match.info:
            running_time = match.info['running_time'].split()
            return (running_time and running_time[0] == '2h' and running_time[1] >= '45' and
                    datetime.datetime.utcnow() - match.match_info_last_updated > datetime.timedelta(minutes=10))
        else:
            return True

    def clear_unneeded_matches(self):
        """Remove finished matches.
        """
        if self.is_it_time_to_clear():
            to_be_cleared = []
            for match_id, match in self.match_dict.iteritems():
                if self.should_match_be_cleared(match):
                    to_be_cleared.append((match_id, match))

            for match_id, match in to_be_cleared:
                self.match_dict.pop(match_id)
                if match.info:
                    log.info('Remove finished match: {} - {} vs {}'.format(
                        match.info['league_name'], match.info['home_team_name'], match.info['away_team_name']
                    ))

            self.last_clear_time = datetime.datetime.utcnow()

    def clear_in_running_matches(self):
        """Sometimes we only want to do dead balls, e.g. in tc tool
        """
        for match_id, match in self.match_dict.items():
            if match.is_in_running:
                self.match_dict.pop(match_id)
