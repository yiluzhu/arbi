from PySide.QtCore import QAbstractTableModel, Qt, SIGNAL, QModelIndex


DATA_ENGINE_TABLE_HEADER = [
    'Match ID', 'In Running', 'Running Time', 'League', 'League CN', 'Home', 'Home CN', 'Home Score', 'Away Score', 'Away', 'Away CN',
]


class DataEngineTableModel(QAbstractTableModel):
    """
    This table presents a summary of what matches are in the data engine
    """
    def __init__(self, data_engine, header):
        super(DataEngineTableModel, self).__init__()
        self.data_engine = data_engine
        self.table = []
        self.header = header

    def clear_data(self):
        self.update([])

    def rowCount(self, parent):
        return len(self.table)

    def columnCount(self, parent):
        return len(self.header)

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            try:
                return self.table[index.row()][index.column()]
            except IndexError:
                return

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]

    # def removeRows(self, row_index, count):
    #     self.beginRemoveRows(QModelIndex(), row_index, row_index + count - 1)
    #     del self.table[row_index: row_index + count]
    #     self.endRemoveRows()

    def refresh(self):
        # TODO: use delta to change table
        new_table = self.data_engine.get_inspector_table()
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        del self.table[:]
        self.table.extend(new_table)
        self.emit(SIGNAL("layoutChanged()"))
