import gcnv

def directional_stock_number(stock_price, vol_ratio):
	return gcnv.DIRECTIONAL_DOLLARS / (stock_price * vol_ratio)

def directional_options_number(stock_price, vol_ratio):
	return (gcnv.DIRECTIONAL_DOLLARS / 
			(stock_price * 100 * vol_ratio * gcnv.AVERAGE_OPTIONS_DELTA))

def neutral_options_number(stock_price, vol_ratio):
	return gcnv.NEUTRAL_DOLLARS / (stock_price * 100 * vol_ratio)