import time
import logging
from threading import Thread, Event

from arbi.utils import get_memory_usage
from arbi.tools.tc.web.scraper import SportteryScraper
from arbi.tools.tc.constants import SCRAPER_RUNNING_INTERVAL, SPORTTERY_DATA_FORCE_SEND_INTERVAL, LOG_MEMORY_INTERVAL


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class SportteryScraperThreadObj(object):

    def __init__(self, queue, account_model):
        self.queue = queue
        self.account_model = account_model
        self.thread = None
        self.stop_event = Event()
        self.last_scrapped_data = None
        self.ts_last_sent = 0
        self.ts_last_mem_log = 0

    def start(self):
        """To create the thread here rather than sub class Thread allows us to restart thread without create new instance"""
        self.stop_event.clear()
        self.thread = Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        scraper = SportteryScraper()
        log.info('{} scraper (thread id {}) starts.'.format('Sporttery', self.thread.ident))

        while not self.queue.has_put_init_dict_in:
            time.sleep(1)

        if self.account_model.use_sporttery_mock_data:
            data = scraper.scrape_football_mock_data()
            self.queue.put({'football': data, 'sporttery': True})
        else:
            while not self.stop_event.is_set():
                data = scraper.scrape_football()
                if data:
                    t = time.time()
                    if data == self.last_scrapped_data:
                        log.info('Sporttery data has not changed since last scraping.')
                        if t - self.ts_last_sent > SPORTTERY_DATA_FORCE_SEND_INTERVAL:
                            self.queue.put({'football': data, 'sporttery': True})
                            self.ts_last_sent = t
                            log.info('Sporttery data has not been sent for {} seconds. Force sending.'.format(SPORTTERY_DATA_FORCE_SEND_INTERVAL))
                    else:
                        self.queue.put({'football': data, 'sporttery': True})
                        self.last_scrapped_data = data
                        self.ts_last_sent = t
                        log.info('Sporttery data has changed since last scraping.')

                    if t - self.ts_last_mem_log > LOG_MEMORY_INTERVAL:
                        pid = scraper.get_driver_pid()
                        log.info('Chrome driver memory usage: {} MB'.format(get_memory_usage(pid)))
                        self.ts_last_mem_log = t

                time.sleep(SCRAPER_RUNNING_INTERVAL)
            else:
                log.info('Sporttery scraper (thread id {}) is finished.'.format(self.thread.ident))
                scraper.quit()
