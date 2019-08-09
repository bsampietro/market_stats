import statistics
from functools import lru_cache

import gcnv

class HV:
    def __init__(self, ticker):
        self.ticker = ticker

    @lru_cache(maxsize=None)
    def period_list(self, back_days):
        hvs = gcnv.data_handler.list_data([["HV", self.ticker]], back_days)[0]
        return [hv * 100 for hv in hvs]

    @lru_cache(maxsize=None)
    def period_average(self, back_days):
        return statistics.mean(self.period_list(back_days))