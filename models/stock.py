from datetime import datetime, timedelta

from functools import lru_cache
import statistics
import math

from config import main_vars

def calculate_hv(closes):
    # return (statistics.stdev(closes) / closes[-1]) * 100 * math.sqrt(252/len(closes))
    return (statistics.stdev(closes) / statistics.mean(closes)) * 100 * math.sqrt(252/len(closes))

def calculate_percentage_hv(percentage_changes):
    return statistics.stdev(percentage_changes) * math.sqrt(252/len(percentage_changes))

class Stock:
    def __init__(self, data_handler, ticker):
        self.data_handler = data_handler
        self.ticker = ticker


    def hv(self, back_days):
        return calculate_hv(self.closes(back_days))


    @lru_cache(maxsize=None)
    def period_hvs(self):
        closes = self.closes(main_vars.back_days)
        hvs = []
        for i in range(len(closes) - 21):
            monthly_closes = closes[i:i+21]
            hvs.append(calculate_hv(monthly_closes))
        return hvs


    @lru_cache(maxsize=None)
    def hv_average(self):
        return statistics.mean(self.period_hvs())


    @lru_cache(maxsize=None)
    def ma(self, back_days):
        if len(self.closes(back_days)) == 0:
            return None
        return statistics.mean(self.closes(back_days))


    def current_to_ma_percentage(self, date, back_days):
        return (float(self.get_close_at(date)) / self.ma(back_days) - 1.0) * 100


    def get_close_at(self, date):
        return self.data_handler.find_in_data("STOCK", self.ticker, date)


    def min(self, back_days):
        return min(self.closes(back_days))


    def max(self, back_days):
        return max(self.closes(back_days))


    @lru_cache(maxsize=None)
    def percentage_hv(self, back_days):
        return calculate_percentage_hv(self.percentage_changes(back_days))


    @lru_cache(maxsize=None)
    def percentage_period_hvs(self):
        percentage_changes = self.percentage_changes(main_vars.back_days)
        hvs = []
        for i in range(len(percentage_changes) - 21):
            monthly_percentage_changes = percentage_changes[i:i+21]
            hvs.append(calculate_percentage_hv(monthly_percentage_changes))
        return hvs


    @lru_cache(maxsize=None)
    def percentage_hv_average(self):
        return statistics.mean(self.percentage_period_hvs())


    def closes_nr(self, back_days, up):
        if up:
            return self.up_down_closes(back_days).count(1)
        else:
            return self.up_down_closes(back_days).count(-1)


    def consecutive_nr(self, back_days, up):
        consecutive = 0
        max_consecutive = 0
        for i in self.up_down_closes(back_days):
            if up:
                if i == 1:
                    consecutive += 1
                else:
                    if consecutive > max_consecutive:
                        max_consecutive = consecutive
                    consecutive = 0
            else:
                if i == -1:
                    consecutive += 1
                else:
                    if consecutive > max_consecutive:
                        max_consecutive = consecutive
                    consecutive = 0
        return max_consecutive


    def stdev(self, back_days):
        return statistics.stdev(self.accumulative_percentage_changes(back_days))


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


    @lru_cache(maxsize=None)
    def percentage_changes(self, back_days):
        closes = self.closes(back_days)
        percentage_changes = []
        percentage_change = 0
        for i in range(len(closes)):
            if i == 0:
                continue
            # percentage_change += (closes[i] / closes[i-1] - 1) * 100 # accumulative
            percentage_change = (closes[i] / closes[i-1] - 1) * 100 # non accumulative
            percentage_changes.append(percentage_change)
        return percentage_changes


    @lru_cache(maxsize=None)
    def accumulative_percentage_changes(self, back_days):
        accumulative_percentage_changes = []
        suma = 0
        for change in self.percentage_changes(back_days):
            suma += change
            accumulative_percentage_changes.append(suma)
        return accumulative_percentage_changes


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