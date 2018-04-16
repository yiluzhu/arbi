from unittest2 import TestCase, main
from arbi.utils import gzip_string, unzip_string


class UtilTest(TestCase):
    def test_zip_and_uzip(self):
        data = 'abc'
        zipped_data = gzip_string(data)
        unzipped_data = unzip_string(zipped_data)
        self.assertEqual(unzipped_data, data)
