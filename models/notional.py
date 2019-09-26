DIRECTIONAL_DOLLARS = 15000 # for a 10 volatility ratio
NEUTRAL_DOLLARS = DIRECTIONAL_DOLLARS * 3 # assuming 0.33 delta is average size of position when going against you
AVERAGE_OPTIONS_DELTA = 0.30

def directional_stock_number(stock_price, vol_ratio):
	return DIRECTIONAL_DOLLARS / (stock_price * vol_ratio)

def directional_options_number(stock_price, vol_ratio):
	return (DIRECTIONAL_DOLLARS / 
			(stock_price * 100 * vol_ratio * AVERAGE_OPTIONS_DELTA))

def neutral_options_number(stock_price, vol_ratio):
	return NEUTRAL_DOLLARS / (stock_price * 100 * vol_ratio)