# from iv import *
# from hv import *

from datetime import datetime, timedelta
from functools import lru_cache

class MixedVs:
    BACK_DAYS = 365
    COMPARATION_PERIOD = BACK_DAYS - 30

    def __init__(self, data_handler, iv, hv):
        self.iv = iv
        self.hv = hv
        self.data_handler = data_handler
        self.ticker = self.iv.ticker
        assert self.iv.ticker == self.hv.ticker


    def iv_current_to_hv_average(self, date):
        return self.iv.get_at(date) / self.hv.period_average()


    def iv_average_to_hv_average(self):
        return self.iv.period_average() / self.hv.period_average()


    @lru_cache(maxsize=None)
    def iv_hv_difference(self):
        back_day = datetime.today() - timedelta(days = MixedVs.BACK_DAYS)
        differences = []
        for i in range(MixedVs.COMPARATION_PERIOD):
            iv = self.data_handler.find_in_data("IV", self.ticker, back_day, silent = True)
            hv = self.data_handler.find_in_data("HV", self.ticker, back_day + timedelta(days = 28), silent = True)
            if iv is not None and hv is not None:
                differences.append(iv * 100 - hv * 100)
            back_day = back_day + timedelta(days = 1)
        return differences


    def difference_average(self):
        return sum(self.iv_hv_difference()) / len(self.iv_hv_difference())


    # returns percentage of success of daily one month volatility trading
    def negative_difference_ratio(self):
        negative_count = 0
        for diff in self.iv_hv_difference():
            if diff < 0:
                negative_count += 1
        return (float(MixedVs.COMPARATION_PERIOD - negative_count) / (MixedVs.COMPARATION_PERIOD)) * 100