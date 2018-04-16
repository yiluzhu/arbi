"""
Test how the system would perform if it didn't have UI
"""
# import time
# import pprint
# from unittest2 import TestCase, main
# from arbi.feeds.vip.data import DataEngine
# from arbi.feeds.vip.networking import MockVIPFeed
# from arbi.models.arbi_spotter import ArbiSpotter
#
#
# PACKET_SIZE = 2000
# TOTAL_TIME_BENCHMARK = 60
# TIME_PER_LOOP_BENCHMARK = 0.03
# TIME_FOR_INIT_PACKET_BENCHMARK = 0.8
#
# class TestPerf(TestCase):
#     def test(self):
#         start_time = time.time()
#
#         vip_feed = MockVIPFeed(PACKET_SIZE)
#         engine = DataEngine()
#         arbi_spotter = ArbiSpotter(engine.match_dict)
#
#         packet = vip_feed.get_one_packet()
#         before_init_match_dict_time = time.time()
#         for record in engine.get_records(packet):
#             engine.initialize_match_dict(record)
#
#         before_loop_time = time.time()
#         while True:
#             try:
#                 packet = vip_feed.get_one_packet()
#             except StopIteration:
#                 break
#
#             for record in engine.get_records(packet):
#                 engine.update_match_dict(record)
#                 arbis = arbi_spotter.spot_arbi()
#
#         finish_time = time.time()
#         total_time = finish_time - start_time
#         init_match_dict_time = before_loop_time - before_init_match_dict_time
#         time_per_loop = (finish_time - before_loop_time) / PACKET_SIZE
#
#         pprint.pprint('Total running time: {}'.format(total_time))
#         pprint.pprint('Time to process init packet: {}'.format(init_match_dict_time))
#         pprint.pprint('Time to process each packet: {}'.format(time_per_loop))
#         self.assertLess(time_per_loop, TIME_PER_LOOP_BENCHMARK)
#         self.assertLess(init_match_dict_time, TIME_FOR_INIT_PACKET_BENCHMARK)
#         self.assertLess(total_time, TOTAL_TIME_BENCHMARK)
#
#
# if __name__ == '__main__':
#     main()