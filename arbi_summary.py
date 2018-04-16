import os
import time
import codecs
import logging
import datetime
import operator
from PySide.QtCore import QAbstractTableModel, Qt, SIGNAL, QModelIndex
from PySide.QtGui import QBrush

from arbi.constants import ROOT_PATH, ARBI_SUMMARY_HEADER, NO_REPEAT_OPPS_IN_HISTORIC_VIEW_TIME_FRAME


ARBI_STORE_PATH = os.path.join(ROOT_PATH, 'stored_data', 'arbi_opps')

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

HISTORIC_ARBI_OPP_FILTER_DICT_CLEANUP_INTERVAL = 60 * 60 * 8


class ArbiSummaryTableModel(QAbstractTableModel):
    def __init__(self, table, header):
        super(ArbiSummaryTableModel, self).__init__()
        self.table = table
        self.header = header

    def clear_data(self):
        self.update([])

    def rowCount(self, parent):
        return len(self.table)

    def columnCount(self, parent):
        return len(self.header)

    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                try:
                    return self.table[index.row()][index.column()]
                except IndexError:
                    pass
            elif role == Qt.BackgroundColorRole:
                try:
                    note = self.table[index.row()][0]
                except IndexError:
                    pass
                else:
                    if note == 'Sporttery No Rebate':
                        return QBrush(Qt.green)

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]

    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.table = sorted(self.table, key=operator.itemgetter(col))
        if order == Qt.DescendingOrder:
            self.table.reverse()
        self.emit(SIGNAL("layoutChanged()"))

    # def removeRows(self, row, count):
    #     self.beginRemoveRows(QModelIndex(), row, row + count - 1)
    #     del self.table[row: row + count]
    #     self.endRemoveRows()

    def update(self, new_table):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        del self.table[:]
        self.table.extend(new_table)
        self.emit(SIGNAL("layoutChanged()"))

    def append(self, new_table):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.table = new_table + self.table
        self.emit(SIGNAL("layoutChanged()"))


class ArbiSummaryLogger(object):
    """For one arbitrage opportunity, we only show one row with final elapsed time. This means we write the opportunity
    when it disappears rather than when it first occurs.
    """
    chinese_columns = ['League CN', 'Home CN', 'Away CN', 'Bookie CN1', 'Bookie CN2', 'Bookie CN3']

    def __init__(self, path=ARBI_STORE_PATH, file_obj=None):
        self.occurred_time_index = ARBI_SUMMARY_HEADER.index('Occurred (HK Time)')
        self.chinese_column_indices = [ARBI_SUMMARY_HEADER.index(col) for col in self.chinese_columns]
        self.cached_arbi_opps_dict = {}
        self.historic_arbi_opp_filter_dict = {'last cleaned': 0}
        self.create_storage_file(path, file_obj)

    def create_storage_file(self, path, file_obj):
        date = datetime.datetime.utcnow().strftime('%Y%m%d')
        filename = os.path.join(path, 'arbi_opps_{0}.csv'.format(date))
        new_file = False if os.path.exists(filename) else True
        if not os.path.exists(path):
            os.makedirs(path)
        self.file = file_obj or open(filename, 'w' if new_file else 'a')
        if new_file:
            self.file.write(codecs.BOM_UTF8)  # write byte order mark tell Excel to open the file with utf-8 coding
            self.file.write(','.join(ARBI_SUMMARY_HEADER) + '\n')

    def clear_data(self):
        self.cached_arbi_opps_dict.clear()

    def filter_out_saved_opps(self, disappeared_opps_pairs):
        """For opps we have saved in the past one minute, we do not save them again.
        """
        disappeared_opps = []
        t = time.time()
        if t - self.historic_arbi_opp_filter_dict['last cleaned'] > HISTORIC_ARBI_OPP_FILTER_DICT_CLEANUP_INTERVAL:
            for part_opp, ts in self.historic_arbi_opp_filter_dict.items():
                if t - ts > NO_REPEAT_OPPS_IN_HISTORIC_VIEW_TIME_FRAME:
                    self.historic_arbi_opp_filter_dict.pop(part_opp)
            self.historic_arbi_opp_filter_dict['last cleaned'] = t

        for part_opp, full_opp in disappeared_opps_pairs:
            if part_opp not in self.historic_arbi_opp_filter_dict or t - self.historic_arbi_opp_filter_dict[part_opp] > NO_REPEAT_OPPS_IN_HISTORIC_VIEW_TIME_FRAME:
                disappeared_opps.append(full_opp)
                self.historic_arbi_opp_filter_dict[part_opp] = t

        return disappeared_opps

    def save(self, arbi_summary):
        disappeared_opps_pairs = self.process_arbi_summary(arbi_summary)
        disappeared_opps = self.filter_out_saved_opps(disappeared_opps_pairs)
        if not disappeared_opps:
            return

        log.info('Found {} new opportunities in tc tool.'.format(len(disappeared_opps)))

        for opp in disappeared_opps:
            content = ','.join(self.convert_arbi_opp(opp))
            self.file.write(content + '\n')
            log.info('Found arb: {}'.format(content))

        return disappeared_opps

    def process_arbi_summary(self, arbi_summary):
        """Update cached arbi opp dict with new dict, and return arb opps that was in old cached dict but not in new cached dict
        e.g. if cached_dict = {a, b, c}, new_dict = {a, b, d} => cached_dict = {a, b, d} return c
        """
        disappeared_opps_pairs = []
        new_arbi_opps_dict = self.get_arbi_opps_dict(arbi_summary)
        for opp, full_opp in self.cached_arbi_opps_dict.iteritems():
            if opp not in new_arbi_opps_dict:
                disappeared_opps_pairs.append((opp, full_opp))
        self.cached_arbi_opps_dict = new_arbi_opps_dict

        return disappeared_opps_pairs

    def get_arbi_opps_dict(self, arbi_summary):
        return {self.get_comparable_part(arbi_opp): arbi_opp for arbi_opp in arbi_summary}

    def get_comparable_part(self, arbi_opp):
        """For a given arbitrage opportunity, return the part that is used to identify it
        """
        return tuple(arbi_opp[:self.occurred_time_index] + arbi_opp[self.occurred_time_index + 1:])

    def convert_arbi_opp(self, arbi_opp):
        return [item.encode('utf8') if i in self.chinese_column_indices else str(item) for i, item in enumerate(arbi_opp)]

    def finish(self):
        for opp in self.cached_arbi_opps_dict.values():
            content = ','.join(self.convert_arbi_opp(opp))
            self.file.write(content + '\n')

        self.file.flush()
        self.clear_data()

    def __del__(self):
        if hasattr(self, 'file'):
            self.finish()
            self.file.close()
