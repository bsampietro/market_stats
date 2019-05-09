from datetime import datetime, timedelta
from functools import lru_cache
import statistics
import math

import pygal

from lib import util
from lib.errors import *
import gcnv

class Pair:
    def __init__(self, data_handler, ticker1, ticker2, fixed_stdev_ratio = None):
        self.data_handler = data_handler
        self.ticker1 = ticker1
        self.ticker2 = ticker2
        self.fixed_stdev_ratio = fixed_stdev_ratio


    # -------- Correlation part -------

    @lru_cache(maxsize=None)
    def correlation(self, back_days):
        changes = self.parallel_percentage_changes(back_days)
        return util.covariance(changes[0], changes[1]) / (statistics.stdev(changes[0]) * statistics.stdev(changes[1]))


    @lru_cache(maxsize=None)
    def beta(self, back_days):
        return self.correlation(back_days) * self.stdev_ratio(back_days)


    @lru_cache(maxsize=None)
    def stdev_ratio(self, back_days):
        if self.fixed_stdev_ratio != None:
            return self.fixed_stdev_ratio
        changes = self.parallel_percentage_changes(back_days)
        return (statistics.stdev(changes[0]) / statistics.stdev(changes[1]))


    # Gets the daily standard deviation of backdays and multiplies by sqrt of 
    # year days to get the aggregated value
    def hv(self, back_days):
        changes_metric = self.percentage_changes(back_days) # simple percentage change
        return statistics.stdev(changes_metric) * math.sqrt(252)


    @lru_cache(maxsize=None)
    def hv_to_10_ratio(self, back_days):
        return self.hv(back_days) / 10


    # -------- Pairs part ----------

    # Could also be called accumulative_percentage_changes
    # Sum of percentage changes of the pair as a whole
    @lru_cache(maxsize=None)
    def closes(self, back_days):
        closes = []
        suma = 0
        # for change in self.log_changes(back_days):
        for change in self.percentage_changes(back_days):
            suma += change
            closes.append(suma)
        return closes


    # Percentage changes of the pair as a whole
    @lru_cache(maxsize=None)
    def percentage_changes(self, back_days):
        percentage_changes1 = self.parallel_percentage_changes(back_days)[0]
        percentage_changes2 = self.parallel_percentage_changes(back_days)[1]
        percentage_changes = []
        positively_correlated = self.correlation(back_days) >= 0
        for i in range(len(percentage_changes1)):
            if positively_correlated:
                change = percentage_changes1[i] - percentage_changes2[i] * self.stdev_ratio(back_days)
            else:
                change = percentage_changes1[i] + percentage_changes2[i] * self.stdev_ratio(back_days)
            percentage_changes.append(change)
        return percentage_changes


    @lru_cache(maxsize=None)
    def log_changes(self, back_days):
        return [math.log((change / 100) + 1) for change in self.percentage_changes(back_days)]


    def get_last_close(self, back_days):
        return self.closes(back_days)[-1]


    @lru_cache(maxsize=None)
    def ma(self, back_days):
        closes = self.closes(back_days)
        if len(closes) == 0:
            return None
        return statistics.mean(closes)


    @lru_cache(maxsize=None)
    def current_to_ma_diff(self, back_days):
        return self.get_last_close(back_days) - self.ma(back_days)


    @lru_cache(maxsize=None)
    def min(self, back_days):
        return min(self.closes(back_days))


    @lru_cache(maxsize=None)
    def max(self, back_days):
        return max(self.closes(back_days))


    def current_rank(self, back_days):
        midpoint = (self.max(back_days) + self.min(back_days)) / 2
        min_max_midpoint_distance = self.max(back_days) - midpoint
        return ((self.get_last_close(back_days) - midpoint) / min_max_midpoint_distance) * 100


    def output_chart(self, back_days):
        line_chart = pygal.Line(truncate_label=-1)
        line_chart.title = f"{self.ticker1}-{self.ticker2}"
        line_chart.x_title = f"Ratio: {format(self.stdev_ratio(back_days), '.2f')} - Corr: {format(self.correlation(back_days), '.2f')}"
        x_labels = []
        for i in range(len(self.parallel_accumulative_percentage_changes(back_days)[0])):
            if i % 20 == 0:
                x_labels.append(i)
            else:
                x_labels.append('')
        x_labels.reverse()
        line_chart.x_labels = x_labels
        line_chart.add(str(back_days), self.closes(back_days))
        line_chart.add(self.ticker1, self.parallel_accumulative_percentage_changes(back_days)[0])
        line_chart.add(self.ticker2, self.parallel_accumulative_percentage_changes(back_days)[1])
        # line_chart.show_dots = False
        line_chart.render_to_file(f"/media/ramd/{self.ticker1}-{self.ticker2}.svg")


    # PRIVATE

    @lru_cache(maxsize=None)
    def parallel_closes(self, back_days):
        max_date_ticker1 = self.data_handler.get_max_stored_date("STOCK", self.ticker1)
        max_date_ticker2 = self.data_handler.get_max_stored_date("STOCK", self.ticker2)
        if max_date_ticker1 is None or max_date_ticker2 is None or max_date_ticker1 != max_date_ticker2:
            raise GettingInfoError(f"{self.ticker1}-{self.ticker2}: Not available data for pairs percentage change calculation")

        closes_ticker1 = []
        closes_ticker2 = []
        for i in range(back_days):
            older_date = max_date_ticker1 - timedelta(days = i)
            close_ticker1 = self.data_handler.find_in_data("STOCK", self.ticker1, older_date.strftime("%Y%m%d"), True)
            close_ticker2 = self.data_handler.find_in_data("STOCK", self.ticker2, older_date.strftime("%Y%m%d"), True)
            if close_ticker1 is not None and close_ticker2 is not None:
                closes_ticker1.append(close_ticker1)
                closes_ticker2.append(close_ticker2)
        closes_ticker1.reverse()
        closes_ticker2.reverse()

        return (closes_ticker1, closes_ticker2)


    @lru_cache(maxsize=None)
    def parallel_percentage_changes(self, back_days):
        closes_ticker1 = self.parallel_closes(back_days)[0]
        closes_ticker2 = self.parallel_closes(back_days)[1]

        percentage_changes_ticker1 = []
        percentage_changes_ticker2 = []
        for i in range(1, len(closes_ticker1)):
            percentage_changes_ticker1.append((closes_ticker1[i] / closes_ticker1[i-1] - 1) * 100)
            percentage_changes_ticker2.append((closes_ticker2[i] / closes_ticker2[i-1] - 1) * 100)

        return (percentage_changes_ticker1, percentage_changes_ticker2)

    @lru_cache(maxsize=None)
    def parallel_accumulative_percentage_changes(self, back_days):
        closes_ticker1 = self.parallel_closes(back_days)[0]
        closes_ticker2 = self.parallel_closes(back_days)[1]

        closes_ticker1_base = closes_ticker1[0]
        closes_ticker2_base = closes_ticker2[0]

        percentage_changes_ticker1 = [0] # starts with 0 change
        percentage_changes_ticker2 = [0] # starts with 0 change
        for i in range(1, len(closes_ticker1)):
            percentage_changes_ticker1.append((closes_ticker1[i] / closes_ticker1_base - 1) * 100)
            percentage_changes_ticker2.append((closes_ticker2[i] / closes_ticker2_base - 1) * 100)

        return (percentage_changes_ticker1, percentage_changes_ticker2)