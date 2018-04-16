"""
Connect to VIP feed and save packets to a local file in tests/tests_data
"""
import time
from arbi.feeds.vip.networking import VIPFeed
from arbi.feeds.vip.constants import HOSTS, PORTS, ACCOUNT_MAP


TOTAL_PACKETS = 5000
FILE_NAME = '../mock_data/vip/packets{0}.txt'.format(TOTAL_PACKETS)


def main():
    vip_feed = VIPFeed(HOSTS[0], PORTS[0])

    if not vip_feed.login(*ACCOUNT_MAP[0]):
        print 'Login failed'
        return

    with open(FILE_NAME, 'w') as f:
        packet = vip_feed.get_one_packet()
        f.write(str(packet) + '\n')
        pkg_counter = 0
        t0 = time.time()
        while True:
            packet = vip_feed.get_one_packet()
            if not packet:
                print 'no packet'
                return
            elif len(packet) == 1 and packet[0] == 'LOGOUT\x00':
                print 'logout'
                return

            pkg_counter += 1
            f.write(str(packet) + '\n')
            if pkg_counter >= TOTAL_PACKETS:
                break

    print 'Processed {0} packets, average time for processing each packet: {1}'.format(
            TOTAL_PACKETS, (time.time() - t0) / TOTAL_PACKETS)


if __name__ == '__main__':
    main()