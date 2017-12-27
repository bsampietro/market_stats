MIN_IVR = 25
MIN_MONEY = 25 # minimum money (25 thousand) to put starting on 25 IVR
# MULTIPLIER has to be so that with ivr of 85 or more,
# the money is the triple of MIN_MONEY
# check notional_quantity method
MULTIPLIER = 2 * MIN_MONEY / 60.0 # 60 because: 85 ivr - 25 ivr

def notional_quantity(ivr, spy_vol_ratio):
    ratio = 0
    if ivr >= MIN_IVR:
        plus = (ivr - MIN_IVR) * MULTIPLIER
        if plus < 2 * MIN_MONEY:
            ratio = (MIN_MONEY + plus) / spy_vol_ratio
        else:
            ratio = (MIN_MONEY + 2 * MIN_MONEY) / spy_vol_ratio
    return round(ratio)