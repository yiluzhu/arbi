"""
Connect to VIP feed and save stream to a local file
"""
import socket
from arbi.feeds.vip.constants import HOSTS, PORTS, ACCOUNT_MAP
from arbi.utils import get_body_size

TOTAL_PACKETS = 1000
FILE_NAME = '../mock_data/stream{0}.txt'.format(TOTAL_PACKETS)


def main():
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.connect((HOSTS[0], PORTS[0]))
    rfile = skt.makefile('rb', -1)
    wfile = skt.makefile('wb', 0)

    wfile.write('V021{0},{1}\n'.format(*ACCOUNT_MAP[0]))
    count = 0
    with open(FILE_NAME, 'w') as f:
        while count < TOTAL_PACKETS:
            f.write(get_raw_data(rfile))
            count += 1

            if count % 20 == 0:
                print '--count--', count


def get_raw_data(f):
    head = f.read(4)
    data = head
    size = get_body_size(head)
    if size > 0:
        data += f.read(size)

    return data


if __name__ == '__main__':
    main()