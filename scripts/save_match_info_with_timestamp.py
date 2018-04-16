"""
Connect to VIP feed and save packets to a local file with timestamp for back testing
"""
import datetime
from arbi.feeds.vip.networking import VIPFeed
from arbi.feeds.vip.constants import HOSTS, PORTS, ACCOUNT_MAP


DURATION_IN_MINS = 60 * 24
STARTING_TIME = str(datetime.datetime.utcnow()).replace(':', '').split('.')[0]
FEED_NAME = 'VIP'
FILE_NAME = '../mock_data/{}/{}_match_only_{}minutes.txt'.format(FEED_NAME.lower(), STARTING_TIME, DURATION_IN_MINS)


def get_match_record(packet):
    """Given a packet return a sub packet which only contains match record"""
    return [record for record in packet if record.startswith('M')]


def main():
    vip_feed = VIPFeed(HOSTS[0], PORTS[0])

    if not vip_feed.login(*ACCOUNT_MAP[2]):
        print 'Login failed'
        return

    with open(FILE_NAME, 'w') as f:
        t0 = datetime.datetime.utcnow()
        duration = datetime.timedelta(minutes=DURATION_IN_MINS)

        f.write('Starts at {}\n'.format(t0))
        packet = vip_feed.get_one_packet()
        m_packet = get_match_record(packet)
        if m_packet:
            f.write(str(datetime.datetime.utcnow()) + ' ' + str(m_packet) + '\n')
        pkt_count = 1
        while True:
            packet = vip_feed.get_one_packet()
            if not packet:
                print 'no packet'
                return
            elif len(packet) == 1 and packet[0] == 'LOGOUT\x00':
                print 'logout'
                return

            t = datetime.datetime.utcnow()
            m_packet = get_match_record(packet)
            if m_packet:
                f.write(str(t) + ' ' + str(m_packet) + '\n')
                pkt_count += 1
            if t - t0 > duration:
                break

        f.write('Total packets that contain match record: ' + str(pkt_count))


if __name__ == '__main__':
    main()