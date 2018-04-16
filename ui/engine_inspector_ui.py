from PySide.QtGui import QWidget, QTableView, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QComboBox
from arbi.ui_models.engine_inspector_model import DATA_ENGINE_TABLE_HEADER
from arbi.ui.constants import ENGINE_INSPECTOR_UI_REFRESH_INVERVAL


class EngineInspectorUI(QWidget):
    def __init__(self, engine_table_model):
        super(EngineInspectorUI, self).__init__()
        self.timer_id = None

        self.engine_table_model = engine_table_model
        self.table_view = QTableView()
        self.table_view.setModel(engine_table_model)

        # Filter
        label1 = QLabel('Filter (Chinese not supported yet) ')
        self.line_edit = QLineEdit()
        self.line_edit.setFixedWidth(300)
        self.line_edit.textChanged.connect(self.filter_displayed_matches)
        label2 = QLabel(' on Column ')
        self.column_combo_box = QComboBox()
        self.column_combo_box.addItems(DATA_ENGINE_TABLE_HEADER)
        label3 = QLabel('Refresh Every {} Seconds'.format(ENGINE_INSPECTOR_UI_REFRESH_INVERVAL))

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(label1)
        filter_layout.addWidget(self.line_edit)
        filter_layout.addWidget(label2)
        filter_layout.addWidget(self.column_combo_box)
        filter_layout.addStretch()
        filter_layout.addWidget(label3)

        # main layout
        layout = QVBoxLayout()
        layout.addLayout(filter_layout)
        layout.addWidget(self.table_view)
        self.setLayout(layout)

        self.setWindowTitle('Inspect All Matches in Real Time')
        self.resize(1000, 400)
        self.line_edit.setText('True')
        self.column_combo_box.setCurrentIndex(1)

    def filter_displayed_matches(self):
        index = self.column_combo_box.currentIndex()
        text = self.line_edit.text()
        for i, row in enumerate(self.engine_table_model.table):
            hidden_flag = text not in str(row[index])
            self.table_view.setRowHidden(i, hidden_flag)

    def set_timer_id(self, timer_id):
        self.timer_id = timer_id

    def timerEvent(self, event):
        self.engine_table_model.refresh()
        self.filter_displayed_matches()

    def closeEvent(self, event):
        if self.timer_id:
            self.killTimer(self.timer_id)
        event.accept()
