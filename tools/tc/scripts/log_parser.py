import os
import glob
import codecs

ARBI_SUMMARY_HEADER = [
    'Single Market', 'Strategy', 'Profit', 'Occurred (HK Time)',
    'League', 'League CN', 'Home', 'Home CN', 'Home Score', 'Away Score', 'Away', 'Away CN',
    'Type1', 'Subtype1', 'F/HT1', 'Bookie1', 'Bookie CN1', 'Stake1', 'Odds1', 'Commission1', 'Lay Flag1',
    'Type2', 'Subtype2', 'F/HT2', 'Bookie2', 'Bookie CN2', 'Stake2', 'Odds2', 'Commission2', 'Lay Flag2',
    'Type3', 'Subtype3', 'F/HT3', 'Bookie3', 'Bookie CN3', 'Stake3', 'Odds3', 'Commission3', 'Lay Flag3'
]
chinese_columns = ['League CN', 'Home CN', 'Away CN', 'Bookie CN1', 'Bookie CN2', 'Bookie CN3']
chinese_column_indices = [ARBI_SUMMARY_HEADER.index(col) for col in chinese_columns]

dir_path = os.path.dirname(os.path.realpath(__file__))
i = 0

with open(dir_path + '\opportunities.csv', 'w') as output:
    output.write(codecs.BOM_UTF8)  # write byte order mark tell Excel to open the file with utf-8 coding
    output.write(','.join(ARBI_SUMMARY_HEADER) + '\n')
    for filename in glob.glob(dir_path + '\*.log'):
        if 'tc_log_' in filename:
            print filename
            with open(filename) as f:
                for line in f:
                    if "{'Single Market': " in line:
                        dict_str = line.split(' ', 2)[2]
                        opp_dct = eval(dict_str.strip())
                        assert isinstance(opp_dct, dict)
                        opp_lst = []
                        for i, item in enumerate(ARBI_SUMMARY_HEADER):
                            v = opp_dct.get(item, '')
                            if i in chinese_column_indices:
                                try:
                                    v = v.encode('utf8')
                                except UnicodeDecodeError:
                                    print 'UnicodeDecodeError', v
                                    v = str(v)
                                opp_lst.append(v)
                            else:
                                opp_lst.append(str(v))

                        output.write(','.join(opp_lst) + '\n')
                        i += 1

print 'Opportunities found:', i
