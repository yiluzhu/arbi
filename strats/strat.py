from arbi import constants


STRAT_ID_MAP = {
    'DirectArbiStrategy': '1',
    'TCDirectArbiStrategy': '1',
    'DirectArbiCombinedStrategy': '2',
    'AHvs2Strategy': '3',
    'AHvsXvs2Strategy': '4',
    'EHvsEHXvsAHStrategy': '5',
    'CrossHandicapArbiStrategy': '6',
}


class BaseArbiStrategy(object):

    def __init__(self, profit_threshold=constants.MINI_PROFIT):
        self.profit_threshold = profit_threshold
        self.id = STRAT_ID_MAP[self.__class__.__name__]

    def spot_arbi(self, match, bookie_availability_dict):
        raise NotImplementedError
