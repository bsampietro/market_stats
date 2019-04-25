from datetime import datetime, timedelta

from functools import lru_cache
import statistics
import math

import gcnv

from lib import util

class Stock:
    def __init__(self, data_handler, ticker):
        self.data_handler = data_handler
        self.ticker = ticker


    @lru_cache(maxsize=None)
    def ma(self, back_days):
        if len(self.closes(back_days)) == 0:
            return None
        return statistics.mean(self.closes(back_days))


    def current_to_ma_percentage(self, date, back_days):
        return (float(self.get_close_at(date)) / self.ma(back_days) - 1.0) * 100


    def get_close_at(self, date):
        return self.data_handler.find_in_data("STOCK", self.ticker, date)


    def get_last_percentage_change(self):
        return self.percentage_changes(gcnv.back_days)[-1]


    def min(self, back_days):
        return min(self.closes(back_days))


    def max(self, back_days):
        return max(self.closes(back_days))


    def min_max_rank(self, date, back_days):
        return (self.get_close_at(date) - self.min(back_days)) / (self.max(back_days) - self.min(back_days)) * 100


    def closes_nr(self, back_days, up):
        if up:
            return self.up_down_closes(back_days).count(1)
        else:
            return self.up_down_closes(back_days).count(-1)


    def consecutive_nr(self, back_days, up):
        assert up in (1,-1)
        consecutive = 0
        max_consecutive = 0
        for i in self.up_down_closes(back_days):
            if i * up == 1:
                consecutive += 1
            else:
                if consecutive > max_consecutive:
                    max_consecutive = consecutive
                consecutive = 0
        return max_consecutive

    
    def stdev(self, back_days):
        return statistics.stdev(self.accumulative_percentage_changes(back_days))

    
    # Gets the daily standard deviation of backdays and multiplies by sqrt of 
    # year days to get the aggregated value
    def hv(self, back_days):
        return statistics.stdev(self.percentage_changes(back_days)) * math.sqrt(252)


    @lru_cache(maxsize=None)
    def hv_to_10_ratio(self, back_days):
        return self.hv(back_days) / 10


    # private

    # Last list element is the most recent value, achieved by closes.reverse() statement
    @lru_cache(maxsize=None)
    def closes(self, back_days):
        max_date = self.data_handler.get_max_stored_date("STOCK", self.ticker)
        if max_date is None:
            return []

        closes = []
        for i in range(back_days):
            older_date = max_date - timedelta(days = i)
            close = self.data_handler.find_in_data("STOCK", self.ticker, older_date.strftime("%Y%m%d"), True)
            if close is not None:
                closes.append(close)
        closes.reverse()
        return closes


    @lru_cache(maxsize=None)
    def percentage_changes(self, back_days):
        closes = self.closes(back_days)
        percentage_changes = []
        percentage_change = 0
        for i in range(1, len(closes)):
            percentage_change = (closes[i] / closes[i-1] - 1) * 100 # non accumulative
            percentage_changes.append(percentage_change)
        return percentage_changes


    @lru_cache(maxsize=None)
    def accumulative_percentage_changes(self, back_days):
        closes = self.closes(back_days)
        percentage_changes = [0]
        base = closes[0]
        for i in range(1, len(closes)):
            percentage_changes.append((closes[i] / base - 1) * 100)
        return percentage_changes


    # @lru_cache(maxsize=None)
    # def accumulative_percentage_changes(self, back_days):
    #     accumulative_percentage_changes = []
    #     suma = 0
    #     for change in self.percentage_changes(back_days):
    #         suma += change
    #         accumulative_percentage_changes.append(suma)
    #     return accumulative_percentage_changes


    @lru_cache(maxsize=None)
    def up_down_closes(self, back_days):
        up_down_closes = []
        for change in self.percentage_changes(back_days):
            if change >= 0.15:
                up_down_closes.append(1)
            elif change <= -0.15:
                up_down_closes.append(-1)
            else:
                up_down_closes.append(0)
        return up_down_closes