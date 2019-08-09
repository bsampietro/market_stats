from functools import lru_cache
import statistics
import math

import gcnv

class Stock:
    def __init__(self, ticker):
        self.ticker = ticker

    @lru_cache(maxsize=None)
    def ma(self, back_days):
        if len(self.closes(back_days)) == 0:
            return None
        return statistics.mean(self.closes(back_days))

    def current_to_ma_percentage(self, date, back_days):
        return (float(self.get_close_at(date)) / self.ma(back_days) - 1.0) * 100

    def get_close_at(self, date):
        return gcnv.data_handler.find_in_data("STOCK", self.ticker, date, False)

    def get_last_percentage_change(self):
        # Using 10 as an arbitrary big number to have at least
        # 1 percentage change. (Weekends and holidays don't add numbers)
        return self.percentage_changes(10)[-1]

    def min(self, back_days):
        return min(self.closes(back_days))

    def max(self, back_days):
        return max(self.closes(back_days))

    def min_max_rank(self, date, back_days):
        return ((self.get_close_at(date) - self.min(back_days))
                / (self.max(back_days) - self.min(back_days))
                * 100)

    def closes_nr(self, back_days, up):
        assert up in (1,-1)
        return self.up_down_closes(back_days).count(up)

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

    @lru_cache(maxsize=None)
    def up_down_closes(self, back_days):
        result = []
        for change in self.percentage_changes(back_days):
            if change >= 0:
                result.append(1)
            else:
                result.append(-1)
        return result

    # Gets the daily standard deviation of backdays and multiplies by sqrt of 
    # year days to get the aggregated value
    def hv(self, back_days):
        # changes_metric = self.percentage_changes(back_days) # simple percentage change
        changes_metric = self.log_changes(back_days) # log changes
        return statistics.stdev(changes_metric) * 15.8745 # = math.sqrt(252)

    @lru_cache(maxsize=None)
    def hv_to_10_ratio(self, back_days):
        return self.hv(back_days) / 10

    def range(self, back_days):
        return (self.max(back_days) / self.min(back_days) - 1) * 100

    # Private

    @lru_cache(maxsize=None)
    def closes(self, back_days):
        return gcnv.data_handler.list_data([["STOCK", self.ticker]], back_days)[0]

    @lru_cache(maxsize=None)
    def percentage_changes(self, back_days):
        closes = self.closes(back_days)
        return [(closes[i] / closes[i-1] - 1) * 100 for i in range(1, len(closes))]

    @lru_cache(maxsize=None)
    def log_changes(self, back_days):
        closes = self.closes(back_days)
        return [math.log(closes[i] / closes[i-1]) * 100 for i in range(1, len(closes))]