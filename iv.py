from datetime import datetime, timedelta
import calendar

from functools import lru_cache

from util import *

class IV:
    def __init__(self, data_handler, ticker):
        self.data_handler = data_handler
        self.ticker = ticker

    
    @lru_cache(maxsize=None)
    def period_list(self, back_days):
        max_date = self.data_handler.get_max_stored_date("IV", self.ticker)
        if max_date is None:
            return None

        iv_list = []
        for i in range(back_days):
            older_date = max_date - timedelta(days = i)
            iv = self.data_handler.find_in_data("IV", self.ticker, older_date.strftime("%Y%m%d"), True)
            if iv is not None:
                iv_list.append(iv * 100)
        return iv_list

    
    @lru_cache(maxsize=None)
    def min(self, back_days):
        return min(self.period_list(back_days))

    
    @lru_cache(maxsize=None)
    def max(self, back_days):
        return max(self.period_list(back_days))


    def get_at(self, date):
        return self.data_handler.find_in_data("IV", self.ticker, date) * 100


    def period_iv_ranks(self, back_days, max_results):
        period_iv_ranks = []
        for iv in self.period_list(back_days):
            period_iv_ranks.append(self.calculate_iv_rank(iv, back_days))
            if len(period_iv_ranks) == max_results:
                break
        return period_iv_ranks
        

    @lru_cache(maxsize=None)
    def period_average(self, back_days):
        return sum(self.period_list(back_days)) / len(self.period_list(back_days))


    def current_to_average_ratio(self, date, back_days):
        return self.get_at(date) / self.period_average(back_days)
    

    # private

    def calculate_iv_rank(self, iv, back_days):
        return (iv - self.min(back_days)) / (self.max(back_days) - self.min(back_days)) * 100