from PySide.QtGui import QLabel
from arbi.constants import SCREEN_SIZE
from arbi.ui.menu_bar_ui import MenuBarUI
from arbi.ui.arbi_pro_ui import BaseView
from arbi.tools.tc.ui.tc_menu_bar_ui import TCAccountPanelUI
from arbi.constants import HIDDEN_COLUMNS


class TCView(BaseView):

    def initialize_view(self, table_model, table_model_for_history, version):
        table_view, table_view_for_history = self.initialize_table_views(table_model, table_model_for_history)
        self.set_menu_bar(table_view, table_view_for_history)

        historic_opps_layout = self.create_historic_opps_panel()
        button_layout = self.create_buttons()

        layout = self.create_layout(historic_opps_layout, table_view_for_history,
                                    QLabel('Real time Opportunities:'), table_view, button_layout)
        self.set_layout(layout, 'TC Tool {0}'.format(version), SCREEN_SIZE)

    def set_menu_bar(self, table_view, table_view_for_history):
        menu_bar = MenuBarUI(self.model, table_view, table_view_for_history, account_panel_ui_class=TCAccountPanelUI)
        menu_bar.hide_columns(HIDDEN_COLUMNS)
        self.setMenuBar(menu_bar)
