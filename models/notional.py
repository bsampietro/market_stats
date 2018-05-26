MIN_IVR = 25
MAX_IVR = 85
MIN_MONEY = 15 # minimum money (in thousands) to put starting on 25 IVR
MAX_PLUS = 3 * MIN_MONEY # = 4 * MIN_MONEY - MIN_MONEY

# MULTIPLIER has to be so that with ivr of MAX_IVR or more,
# the max money is the cuadruple of MIN_MONEY
MULTIPLIER = MAX_PLUS / float(MAX_IVR - MIN_IVR)

def quantity(ivr, spy_vol_ratio):
    ratio = 0
    if ivr >= MIN_IVR:
        plus = (ivr - MIN_IVR) * MULTIPLIER
        if plus > MAX_PLUS:
            plus = MAX_PLUS
        ratio = (MIN_MONEY + plus) / spy_vol_ratio
    return round(ratio)