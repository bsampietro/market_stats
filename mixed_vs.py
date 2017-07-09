# from iv import *
# from hv import *

class MixedVs:
    def __init__(self, iv, hv):
        self.iv = iv
        self.hv = hv

    def iv_current_to_hv_average(self, date):
        return self.iv.get_at(date) / self.hv.period_average()


    def iv_average_to_hv_average(self):
        return self.iv.period_average() / self.hv.period_average()