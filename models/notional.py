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


SPY_JUMPS = 2

def jumps(stock_price, spy_vol_ratio):
	return stock_price * ((SPY_JUMPS * spy_vol_ratio) / 100.0)


SPY_DIRECTIONAL_DOLLARS = 12000

def directional_quantity(spy_vol_ratio):
	return round((SPY_DIRECTIONAL_DOLLARS / spy_vol_ratio) * 0.33) # 0.33 is mid between average credit spread 0.25 and debit spread 0.40