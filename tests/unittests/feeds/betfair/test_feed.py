from mock import patch
from unittest import TestCase
from arbi.feeds.betfair.feed import BetfairFeed


class BetfairFeedTest(TestCase):
    def test(self):
        with patch('socket.socket'):
            feed = BetfairFeed('', 1234)