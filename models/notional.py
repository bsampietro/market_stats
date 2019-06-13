DIRECTIONAL_DOLLARS = 5000 # for a 10 volatility ratio

def directional_contract_number(stock_price, vol_ratio):
	return DIRECTIONAL_DOLLARS / (stock_price * vol_ratio)


NEUTRAL_DOLLARS = DIRECTIONAL_DOLLARS * 10

def neutral_contract_number(stock_price, vol_ratio):
	return NEUTRAL_DOLLARS / (stock_price * 100 * vol_ratio)