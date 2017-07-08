from datetime import datetime, timedelta
import calendar

from functools import lru_cache

from util import *

class HV:
    def __init__(self, data_handler, ticker):
        self.data_handler = data_handler
        self.ticker = ticker


    @lru_cache(maxsize=None)
    def period_hv_list(self, back_days = 365):
        max_date = self.data_handler.get_max_stored_date("HV", self.ticker)

        hv_list = []
        for i in range(back_days):
            older_date = max_date - timedelta(days = i)
            hv = self.data_handler.find_in_data("HV", self.ticker, older_date.strftime("%Y%m%d"), True)
            if hv is not None:
                hv_list.append(hv * 100)
        return hv_list


    @lru_cache(maxsize=None)
    def average_period_hv(self, back_days = 365):
        return sum(self.period_hv_list(back_days)) / len(self.period_hv_list(back_days))
    

    def min(self):
        return min(self.period_hv_list())

    
    def max(self):
        return max(self.period_hv_list())


    def range(self):
        return self.max() - self.min()