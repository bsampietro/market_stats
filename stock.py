from datetime import datetime, timedelta

from functools import lru_cache
from util import *
import statistics
import math

class Stock:
    def __init__(self, data_handler, ticker):
        self.data_handler = data_handler
        self.ticker = ticker


    def hv(self, back_days):
        closes = self.closes(back_days)

        # nr_of_closes = len(closes)
        # percentage_changes = []
        # for i in range(nr_of_closes):
        #     if i == 0:
        #         continue
        #     percentage_changes.append((closes[i] / closes[i-1] - 1) * 100)
        # return statistics.stdev(percentage_changes) * math.sqrt(365/back_days)

        # return (statistics.stdev(closes) / self.ma(back_days)) * 100 * math.sqrt(365/back_days)

        return (statistics.stdev(closes) / closes[-1]) * 100 * math.sqrt(365/back_days)


    @lru_cache(maxsize=None)
    def hv_average(self):
        closes = self.closes(365)
        hvs = []
        for i in range(len(closes) - 30):
            monthly_closes = closes[i:i+30]
            hvs.append((statistics.stdev(monthly_closes) / monthly_closes[-1]) * 100 * math.sqrt(12))
        return statistics.mean(hvs)



    @lru_cache(maxsize=None)
    def ma(self, back_days):
        if len(self.closes(back_days)) == 0:
            return None
        return statistics.mean(self.closes(back_days))


    def get_close_at(self, date):
        return self.data_handler.find_in_data("STOCK", self.ticker, date)


    def current_to_ma_percentage(self, date, back_days):
        return (float(self.get_close_at(date)) / self.ma(back_days) - 1.0) * 100


    # private


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