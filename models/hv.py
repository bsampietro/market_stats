import statistics
from functools import lru_cache

class HV:
    def __init__(self, data_handler, ticker):
        self.data_handler = data_handler
        self.ticker = ticker


    @lru_cache(maxsize=None)
    def period_list(self, back_days):
        hvs = self.data_handler.list_data([["HV", self.ticker]], back_days)[0]
        return [hv * 100 for hv in hvs]


    @lru_cache(maxsize=None)
    def period_average(self, back_days):
        return statistics.mean(self.period_list(back_days))