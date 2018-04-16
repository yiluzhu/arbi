from unittest2 import TestCase

from arbi.ui_models.menu_bar_model import StratsPanelModel
from arbi.strats.correlated_arbi import AHvsXvs2Strategy, AHvs2Strategy
from arbi.strats.direct_arbi import DirectArbiStrategy


class StratsPanelModelTest(TestCase):
    def test_get_enabled_strats(self):
        model = StratsPanelModel()
        model.use_direct_arb = True
        model.use_direct_arb_combined = False
        model.use_correlated_arb_AHvs2 = True
        model.use_correlated_arb_AHvsXvs2 = True
        model.use_correlated_arb_EHvsEHXvsAH = False

        expected = [DirectArbiStrategy, AHvsXvs2Strategy, AHvs2Strategy]
        result = model.get_enabled_strats()
        self.assertEqual(result, expected)

    def test_get_enabled_strats_all_false(self):
        model = StratsPanelModel()
        model.use_direct_arb = False
        model.use_direct_arb_combined = False
        model.use_correlated_arb_AHvs2 = False
        model.use_correlated_arb_AHvsXvs2 = False
        model.use_correlated_arb_EHvsEHXvsAH = False

        result = model.get_enabled_strats()
        self.assertEqual(result, [])
