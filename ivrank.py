from datetime import datetime, timedelta
import calendar

from functools import lru_cache

from util import *

class IVRank:
    def __init__(self, data_handler, ticker):
        self.data_handler = data_handler
        self.ticker = ticker

    
    @lru_cache(maxsize=None)
    def period_iv_list(self, back_days = 365):
        max_date = self.get_max_stored_date()

        iv_list = []
        for i in range(back_days):
            older_date = max_date - timedelta(days = i)
            iv = self.data_handler.find_in_data(self.ticker, older_date.strftime("%Y%m%d"), True)
            if iv is not None:
                iv_list.append(iv * 100)
        return iv_list

    
    @lru_cache(maxsize=None)
    def min_iv(self):
        return min(self.period_iv_list())

    
    @lru_cache(maxsize=None)
    def max_iv(self):
        return max(self.period_iv_list())

    
    def get_iv_rank_today(self):
        return self.calculate_iv_rank(self.get_iv_today())

    
    @lru_cache(maxsize=None)
    def get_iv_today(self):
        return self.data_handler.find_in_data(self.ticker, today_in_string()) * 100
    
    
    @lru_cache(maxsize=None)
    def get_period_iv_ranks(self, back_days = 365):
        period_iv_ranks = []
        today = datetime.today()
        for iv in self.period_iv_list(back_days):
            period_iv_ranks.append(self.calculate_iv_rank(iv))
        return period_iv_ranks
        

    @lru_cache(maxsize=None)
    def average_period_iv(self, back_days = 365):
        return sum(self.period_iv_list(back_days)) / len(self.period_iv_list(back_days))


    @lru_cache(maxsize=None)
    def get_max_stored_date(self):
        max_date = max(self.data_handler.find_in_data(self.ticker).keys())
        return datetime.strptime(max_date, "%Y%m%d")
    

    # private

    def calculate_iv_rank(self, iv):
        return (iv - self.min_iv()) / (self.max_iv() - self.min_iv()) * 100