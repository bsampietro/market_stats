import statistics
from functools import lru_cache

class IV:
    def __init__(self, data_handler, ticker):
        self.data_handler = data_handler
        self.ticker = ticker

    @lru_cache(maxsize=None)
    def period_list(self, back_days):
        ivs = self.data_handler.list_data([["IV", self.ticker]], back_days)[0]
        ivs = [iv * 100 for iv in ivs]
        ivs.reverse() # Reverse so first element of the array will be the last iv
        return ivs
    
    @lru_cache(maxsize=None)
    def min(self, back_days):
        return min(self.period_list(back_days))
    
    @lru_cache(maxsize=None)
    def max(self, back_days):
        return max(self.period_list(back_days))

    def get_at(self, date):
        return self.data_handler.find_in_data("IV", self.ticker, date, False) * 100

    @lru_cache(maxsize=None)
    def period_iv_ranks(self, back_days, max_results):
        period_iv_ranks = []
        for iv in self.period_list(back_days):
            period_iv_ranks.append(self.calculate_mm_iv_rank(iv, back_days))
            if len(period_iv_ranks) == max_results:
                break
        return period_iv_ranks

    @lru_cache(maxsize=None)
    def period_average(self, back_days):
        return statistics.mean(self.period_list(back_days))

    def current_to_average_ratio(self, date, back_days):
        return self.get_at(date) / self.period_average(back_days)

    def current_mm_iv_rank(self, back_days):
        return self.calculate_mm_iv_rank(
                self.period_list(back_days)[0], back_days)

    def current_percentile_iv_rank(self, back_days):
        return self.calculate_percentile_iv_rank(
                self.period_list(back_days)[0], back_days)

    # weighted (or not) average between min-max rank and percentile rank
    @lru_cache(maxsize=None)
    def current_weighted_iv_rank(self, back_days):
        return round(
                (2 * self.current_mm_iv_rank(back_days)
                + self.current_percentile_iv_rank(back_days)
                ) / 3.0
            )

    # Private
    
    # IV rank based on percentiles
    def calculate_percentile_iv_rank(self, iv, back_days):
        count = 0
        for close in self.period_list(back_days):
            if iv >= close:
                count += 1
        return round(count / len(self.period_list(back_days)) * 100)

    # IV rank based on min-max levels
    def calculate_mm_iv_rank(self, iv, back_days):
        return round((iv - self.min(back_days)) / 
                    (self.max(back_days) - self.min(back_days))
                    * 100)