import time
import datetime
from multiprocessing import Pool
from arbi import constants
from arbi.constants import BOOKIE_ID_MAP
from arbi.ui_models.menu_bar_model import StratsPanelModel
from arbi.models.opportunity import ArbiOpportunity


class ArbiSpotter(object):
    def __init__(self, match_dict, menu_bar_model=None, profit_threshold=constants.MINI_PROFIT):
        self.match_dict = match_dict
        # some bookie's website could be unusable temporarily, in which case we put them in this dict.
        # bookie_availability_dict looks like this:
        #     {
        #         '2': {'dead ball': True, 'running ball': False},
        #         '1': {'dead ball': True, 'running ball': False},
        #     }
        self.bookie_availability_dict = {bookie_id: {'dead ball': True, 'running ball': True}
                                         for bookie_id in BOOKIE_ID_MAP.keys()}

        self.profit_threshold = profit_threshold  # this can be overwritten when we start discovering
        self.menu_bar_model = menu_bar_model

        self.use_parallel_computing = False
        self.use_async_for_cross_handicap_arb = True
        self.strats_pool = {}
        self.cross_handicap_strat_pool = None
        self.selected_strats = []
        self.selected_strats_str = []
        self.selected_strats_name_map = {}
        self.cross_handicap_strat_result = None

        self.last_rb_prices_expiry_checked = time.time()

    def initialize_strats(self, strats_model_class=StratsPanelModel):
        if self.menu_bar_model is None:
            strats_model = strats_model_class()
            self.use_parallel_computing = False
        else:
            strats_model = self.menu_bar_model.strats_panel_model
            self.use_parallel_computing = self.menu_bar_model.account_model.use_parallel_computing

        self.use_async_for_cross_handicap_arb = strats_model.use_async_for_cross_handicap_arb

        selected_strat_classes = strats_model.get_enabled_strats()
        self.selected_strats = [klass(self.profit_threshold) for klass in selected_strat_classes]
        self.selected_strats_str = {klass.__name__ for klass in selected_strat_classes}

        self.strats_pool = {}
        for name in self.selected_strats_str:
            if name == 'CrossHandicapArbiStrategy':
                self.cross_handicap_strat_pool = Pool(1)
            else:
                self.strats_pool[name] = Pool(1)

        self.selected_strats_name_map = {klass.__name__: klass(self.profit_threshold)
                                         for klass in selected_strat_classes}

    def spot_arbi(self):
        matches = self.match_dict.values()
        for match in matches:
            if match.odds and match.info:
                if match.is_in_running and self.it_is_time_to_check_rb_prices_expiry():
                    self.check_running_ball_prices_expiry(match.odds.odds_dict)

        occur_at_utc = datetime.datetime.utcnow()
        raw_opps_by_id = self.apply_strats_in_parallel(matches) if self.use_parallel_computing else self.apply_strats(matches)

        arbi_opps = self.convert_to_arb_opp_objects(raw_opps_by_id, occur_at_utc)

        return arbi_opps

    def convert_to_arb_opp_objects(self, raw_opps_by_id, occur_at_utc):
        """
        :param raw_opps_by_id: a dict with match_id being key and strat_opps_dict being value,
            where strat_opps_dict is a dict of strat_id being key and a list of raw opps being value.
            e.g.
                {
                    '001':
                        {
                            '1': [opp1, opp2],
                            '3': [opp3, opp4]
                        }
                    '002':
                        {
                            '1': [opp5],
                            '3': []
                        }
                }
        """
        arbi_opps = []
        for match_id, strat_opps_dict in raw_opps_by_id.iteritems():
            for strat_id, raw_opps in strat_opps_dict.iteritems():
                match = self.match_dict[match_id]
                info = {key: match.info[key] for key in ArbiOpportunity.match_info_keys}
                arbi_opps += [ArbiOpportunity(info, occur_at_utc, strat_id, raw_opp) for raw_opp in raw_opps]

        return sorted(arbi_opps, key=lambda x: x.profit, reverse=True)

    def it_is_time_to_check_rb_prices_expiry(self):
        t = time.time()
        if t - self.last_rb_prices_expiry_checked > constants.RB_PRICE_EXPIRY_CHECK_INTERVAL:
            self.last_rb_prices_expiry_checked = t
            return True

    def check_running_ball_prices_expiry(self, odds_dict):
        """If some bookie's prices are expired, remove them
        """
        t = time.time()
        for event_and_odds_type, odds_by_category in odds_dict.iteritems():
            for handicap, bookie_odds_id_and_info in odds_by_category.iteritems():
                for bookie_id, bookie_odds_info in bookie_odds_id_and_info.items():
                    # bookie_odds_info[2] is last_updated
                    if t - bookie_odds_info[2] > constants.RB_PRICE_EXPIRY_TIME:
                        bookie_odds_id_and_info.pop(bookie_id)

    def run_cross_handicap_strat(self, matches, raw_opps_dict):
        if self.use_async_for_cross_handicap_arb:
            if self.cross_handicap_strat_result is None:
                strat = self.selected_strats_name_map['CrossHandicapArbiStrategy']
                self.cross_handicap_strat_result = self.cross_handicap_strat_pool.apply_async(
                    run_one_strat, (matches, strat, self.bookie_availability_dict))
            elif self.cross_handicap_strat_result.ready():  # do not wait for the result
                cross_handicap_opps = self.cross_handicap_strat_result.get()
                raw_opps_dict = self.update_raw_opps_dict(raw_opps_dict, cross_handicap_opps)
                self.cross_handicap_strat_result = None
        else:
            strat = self.selected_strats_name_map['CrossHandicapArbiStrategy']
            cross_handicap_opps = run_one_strat(matches, strat, self.bookie_availability_dict)
            raw_opps_dict = self.update_raw_opps_dict(raw_opps_dict, cross_handicap_opps)

        return raw_opps_dict

    def apply_strats(self, matches):
        raw_opps_dict = {}
        for name, strat in self.selected_strats_name_map.items():
            if name != 'CrossHandicapArbiStrategy':
                new_raw_opps_dict = run_one_strat(matches, strat, self.bookie_availability_dict)
                raw_opps_dict = self.update_raw_opps_dict(raw_opps_dict, new_raw_opps_dict)  # raw_opps_dict should not contain strat_id 6

        if 'CrossHandicapArbiStrategy' in self.selected_strats_str:
            raw_opps_dict = self.run_cross_handicap_strat(matches, raw_opps_dict)

        return raw_opps_dict

    def apply_strats_in_parallel(self, matches):
        strats_results = {}
        for name, pool in self.strats_pool.items():
            strat = self.selected_strats_name_map[name]
            strats_results[name] = pool.apply_async(run_one_strat, (matches, strat, self.bookie_availability_dict))

        raw_opps_dict = {}
        while strats_results:  # wait until all strats finish
            for name, result in strats_results.items():
                if result.ready():
                    raw_opps_dict = self.update_raw_opps_dict(raw_opps_dict, result.get())
                    strats_results.pop(name)

        if 'CrossHandicapArbiStrategy' in self.selected_strats_str:
            raw_opps_dict = self.run_cross_handicap_strat(matches, raw_opps_dict)

        return raw_opps_dict

    @staticmethod
    def update_raw_opps_dict(raw_opps_dict, new_opps_dict, do_assert=True):
        """Merge opps generated from different strats by match_id.
        Note:
            1. raw_opps_dict and new_opps_dict should have the same match_ids as keys.
            2. new_opps_dict should only have one strat_id, for which raw_opps_dict should not contain.

        Assume we  have three strategies with ID '1', '2' and '3'. Given input
            raw_opps_dict = {
                001: {'1': [a, b], '2': [],},
                002: {'1': [d],   '2': [e, f]}
            }
        and
            new_opps_dict = {
                001: {'3': [h, i]},
                002: {'3': [k]}
            }

        The return should be:
            {
                '001': {'1': ['a', 'b'], '2': [], '3': [h, i]},
                '002': {'1': ['d'], '2': ['e', 'f'], '3': [k]},
            }
        """
        if raw_opps_dict == {}:
            return new_opps_dict
        elif new_opps_dict == {}:
            return raw_opps_dict

        if do_assert:
            assert raw_opps_dict.keys() == new_opps_dict.keys()

        for match_id, strat_opps_dict in new_opps_dict.iteritems():
            assert len(strat_opps_dict) == 1
            raw_opps_dict[match_id].update(new_opps_dict[match_id])

        return raw_opps_dict

    def terminate_all_pools(self):
        for pool in self.strats_pool.values():
            pool.terminate()
        if self.cross_handicap_strat_pool:
            self.cross_handicap_strat_pool.terminate()


def run_one_strat(matches, strat, bookie_availability_dict):
    return {match.id: {strat.id: strat.spot_arbi(match, bookie_availability_dict)}
            for match in matches if match.odds and match.info}
