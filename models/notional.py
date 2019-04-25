MIN_IVR = 0
MAX_IVR = 85
MIN_MONEY = 10 # minimum money (in thousands) to put
MAX_MONEY = 50
MAX_PLUS = MAX_MONEY - MIN_MONEY

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


DIRECTIONAL_DOLLARS = 20000 # for a 10 volatility ratio

def directional_quantity(vol_ratio):
	return round(DIRECTIONAL_DOLLARS / vol_ratio)


NEUTRAL_DOLLARS = DIRECTIONAL_DOLLARS * 2

def contract_number(stock_price, vol_ratio):
	return NEUTRAL_DOLLARS / (stock_price * 100 * vol_ratio)