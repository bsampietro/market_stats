# from iv import *
# from hv import *

from datetime import datetime, timedelta
from functools import lru_cache

class MixedVs:

    def __init__(self, data_handler, iv, hv):
        self.iv = iv
        self.hv = hv
        self.data_handler = data_handler
        self.ticker = self.iv.ticker
        assert self.iv.ticker == self.hv.ticker


    def iv_current_to_hv_average(self, date, back_days):
        return self.iv.get_at(date) / self.hv.period_average(back_days)


    def iv_average_to_hv_average(self, back_days):
        return self.iv.period_average(back_days) / self.hv.period_average(back_days)


    @lru_cache(maxsize=None)
    def iv_hv_difference(self, back_days):
        back_day = datetime.today() - timedelta(days = back_days)
        differences = []
        for i in range(back_days - 30):
            iv = self.data_handler.find_in_data("IV", self.ticker, back_day, silent = True)
            hv = self.data_handler.find_in_data("HV", self.ticker, back_day + timedelta(days = 28), silent = True)
            if iv is not None and hv is not None:
                differences.append(iv * 100 - hv * 100)
            back_day = back_day + timedelta(days = 1)
        return differences


    def difference_average(self, back_days):
        return sum(self.iv_hv_difference(back_days)) / len(self.iv_hv_difference(back_days))


    # returns percentage of success of daily one month volatility trading
    def negative_difference_ratio(self, back_days):
        negative_count = 0
        for diff in self.iv_hv_difference(back_days):
            if diff < 0:
                negative_count += 1
        return (float(back_days - 30 - negative_count) / (back_days - 30)) * 100