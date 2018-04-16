from mock import patch, Mock, ANY
from unittest import TestCase
from arbi.feeds.base_feed import BaseFeedThreadObj, BaseFeed


class BaseFeedThreadObjTest(TestCase):
    def setUp(self):
        self.feed_thread_obj = BaseFeedThreadObj(None, None, None, ('', 1234), None, None)
        self.feed_thread_obj.FEED_NAME = 'XXX'

    def test_start_with_delay(self):
        self.feed_thread_obj.FEED_CLASS = BaseFeed
        self.feed_thread_obj.start(delay=0.5, thread_daemon=False)

    def test_prepare_history_file(self):
        mock_open = Mock(return_value='foo')
        with patch('__builtin__.open', mock_open):
            self.feed_thread_obj.prepare_history_file()

        self.assertEqual(self.feed_thread_obj.history_file, 'foo')

    def test_save_history(self):
        self.feed_thread_obj.history_file = Mock()
        self.feed_thread_obj.save_history('')
        self.feed_thread_obj.history_file.write.assert_called_once_with(ANY)

    def test_not_implemented_method_run_loop(self):
        with self.assertRaises(NotImplementedError):
            self.feed_thread_obj.run_loop()

    def test_not_implemented_method_get_records(self):
        with self.assertRaises(NotImplementedError):
            self.feed_thread_obj.get_records([])


class BaseFeedTest(TestCase):
    def setUp(self):
        with patch('socket.socket'):
            self.feed = BaseFeed('', 1234)

    def test_not_implemented_method_get_login_string(self):
        with self.assertRaises(NotImplementedError):
            self.feed.get_login_string('', '')

    def test_not_implemented_method_login_succeeded(self):
        with self.assertRaises(NotImplementedError):
            self.feed.login_succeeded(None)
