import re
import random
filename = '../mock_data/vip/packets2000with_timestamp_100ms.txt'
new_file = filename.replace('vip', 'betfair')

with open(filename) as f:
    with open(new_file, 'w') as new_f:
        for line in f:
            lst = []
            first, second = line.rstrip().split('  ')
            second = eval(second)
            for s in second:
                if s.startswith(('M', 'O', 'p')):
                    continue
                if s.startswith('o') and s.count('|') != 8:
                    continue
                flag = 0 if random.random() > 0.5 else 1
                new = re.sub(r"(o\d+\|.*\|.*\|.*)\|.*\|(.*\|.*\|.*\|.*[0-9])", r'\1|7|\2|{}'.format(flag), s)
                lst.append(new)
            if lst:
                new_f.write(first + '  ' + str(lst) + '\n')
