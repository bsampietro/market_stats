from datetime import datetime, timedelta
import calendar

from util import *

class HV:
    def __init__(self, data_handler, ticker):
        self.data_handler = data_handler
        self.ticker = ticker

    
    def period_hv_list(self, back_days = 365):
        max_date = self.data_handler.get_max_stored_date("HV", self.ticker)

        hv_list = []
        for i in range(back_days):
            older_date = max_date - timedelta(days = i)
            hv = self.data_handler.find_in_data("HV", self.ticker, older_date.strftime("%Y%m%d"), True)
            if hv is not None:
                hv_list.append(hv * 100)
        return hv_list


    def average_period_hv(self, back_days = 365):
        period_hv_list = self.period_hv_list(back_days)
        return sum(period_hv_list) / len(period_hv_list)
    

    # def min_iv(self):
    #     return min(self.period_iv_list())

    
    # def max_iv(self):
    #     return max(self.period_iv_list())