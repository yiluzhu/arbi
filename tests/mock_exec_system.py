"""Run Mock Execution System """

import time
import socket
import logging
import datetime
from arbi.utils import get_body_size, unzip_string
from arbi.execution.constants import EXEC_PORT, EXEC_READ_BLOCK_SIZE


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class ExecSystem(object):

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection_error_count = 0

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('127.0.0.1', EXEC_PORT))
        self.socket.listen(10)
        log.info('Mock execution system is now listening.')
        conn, addr = self.socket.accept()
        log.info('Connected with ' + addr[0] + ':' + str(addr[1]))
        self.conn = conn

        login = True
        while True:
            time.sleep(0.2)
            opps = self.receive_data()
            self.get_details_from_opps(opps)
            if self.connection_error_count >= 3:
                break
            # if login:
            #     self.wfile.write('True')
            #     login = False

        self.socket.close()

    def get_details_from_opps(self, opps):
        for opp in opps:
            if opp.startswith('NB^'):
                opp_list = opp.split('^')
                match_id = opp_list[2]
                score = ':'.join(opp_list[3:5])
                occurred_at_uk = datetime.datetime.strptime(opp_list[6], '%Y-%m-%d %H:%M:%S.%f')
                t = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
                print 'match id: {}, score: {}, delay: {}'.format(match_id, score, (t - occurred_at_uk).total_seconds())

    def __del__(self):
        try:
            self.socket.close()
        except:
            pass

    def receive_data(self):
        try:
            head = self.conn.recv(4)
        except socket.error as e:
            log.error('Error in receiving opp message header: {0}'.format(e))
            self.connection_error_count += 1
            return []
        try:
            size = get_body_size(head)
        except Exception as e:
            log.error('Error in decoding opp message header: {0}'.format(e))
            size = 0

        if size > 0:
            zdata = ''
            try:
                while size > EXEC_READ_BLOCK_SIZE:
                    zdata += self.conn.recv(EXEC_READ_BLOCK_SIZE)
                    size -= EXEC_READ_BLOCK_SIZE
                else:
                    zdata += self.conn.recv(size)
            except socket.error as e:
                udata = None
                log.error('Error in reading execution message body: {0}'.format(e))
            else:
                udata = unzip_string(zdata)

            if udata is None:
                log.error('Error when unzip exec system data.')
                data = []
            else:
                data = udata.strip().split("\n")
        else:
            data = []

        self.conn.recv(5)  # read useless '[END]'

        return data


def run_exec_system():
    exec_system = ExecSystem()
    exec_system.run()


if __name__ == '__main__':
    run_exec_system()