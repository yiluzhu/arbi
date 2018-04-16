from unittest2 import TestCase
from arbi.models.match import Match
from arbi.models.record import MatchInfoRecord


class MatchTest(TestCase):
    def test_in_running_match_scored__true(self):
        record_str = 'M0|02|A Cup|A Cup|A Cup|03|Team A|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|1|0|ht|1|-1|-1'
        match = Match(MatchInfoRecord(record_str))
        new_str = 'M0|02|A Cup|A Cup|A Cup|03|Team A|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|1|1|2h 5|1|-1|-1'
        record_new = MatchInfoRecord(new_str)

        self.assertTrue(match.in_running_match_scored(record_new))

    def test_in_running_match_scored__more_than_one_goal(self):
        record_str = 'M0|02|A Cup|A Cup|A Cup|03|Team A|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|1|0|ht|1|-1|-1'
        match = Match(MatchInfoRecord(record_str))
        new_str = 'M0|02|A Cup|A Cup|A Cup|03|Team A|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|1|2|2h 5|1|-1|-1'
        record_new = MatchInfoRecord(new_str)

        self.assertTrue(match.in_running_match_scored(record_new))

    def test_in_running_match_scored__false(self):
        record_str = 'M0|02|A Cup|A Cup|A Cup|03|Team A|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|1|0|ht|1|-1|-1'
        match = Match(MatchInfoRecord(record_str))
        new_str = 'M0|02|A Cup|A Cup|A Cup|03|Team A|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|1|0|2h 5|1|-1|-1'
        record_new = MatchInfoRecord(new_str)

        self.assertFalse(match.in_running_match_scored(record_new))

    def test_in_running_match_scored__match_not_started(self):
        record_str = 'M0|02|A Cup|A Cup|A Cup|03|Team A|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|-1|-1||1|-1|-1'
        match = Match(MatchInfoRecord(record_str))
        new_str = 'M0|02|A Cup|A Cup|A Cup|03|Team A|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|-1|-1||1|-1|-1'
        record_new = MatchInfoRecord(new_str)

        self.assertFalse(match.in_running_match_scored(record_new))

    def test_in_running_match_scored__exception1(self):
        record_str = 'M0|02|A Cup|A Cup|A Cup|03|\xb5\xc2|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|1|0|ht|1|-1|-1'
        match = Match(MatchInfoRecord(record_str))
        new_str = 'M0|02|A Cup|A Cup|A Cup|03|\xb5\xc2|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|3|0|2h 5|1|-1|-1'
        record_new = MatchInfoRecord(new_str)

        self.assertTrue(match.in_running_match_scored(record_new))

    def test_in_running_match_scored__exception2(self):
        record_str = 'M0|02|A Cup|A Cup|A Cup|03|\xb5\xc2|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|-1|-1||1|-1|-1'
        match = Match(MatchInfoRecord(record_str))
        new_str = 'M0|02|A Cup|A Cup|A Cup|03|\xb5\xc2|Team A|Team A|04|Team B|Team B|Team B|2015-04-17 03:05:00|#6F00DD|1|-1|-1||1|-1|-1'
        record_new = MatchInfoRecord(new_str)

        self.assertFalse(match.in_running_match_scored(record_new))
