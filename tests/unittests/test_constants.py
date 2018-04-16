from unittest2 import TestCase, main
from arbi.constants import get_selection_header, ARBI_SUMMARY_HEADER


class ConstantsTest(TestCase):
    def test_get_selection_header(self):
        expected = ['Type7', 'Subtype7', 'F/HT7', 'Bookie7', 'Bookie CN7', 'Stake7', 'Raw Odds7', 'Effective Odds7', 'Commission7', 'Lay Flag7']
        self.assertEqual(get_selection_header(7), expected)

    def test_ARBI_SUMMARY_HEADER(self):
        expected = 42
        self.assertEqual(len(ARBI_SUMMARY_HEADER), expected)


# if __name__ == '__main__':
#     main()
