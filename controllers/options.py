from controllers.helper import *
import time
import gcnv

def get_header():
    return ['Tckr', 'Ratio', 'DeltaH', 'DeltaL', 
            'StrikeH', 'StrikeL', 'PriceH', 'PriceL']

def get_rows(command):
    tickers = get_tickers_from_command(command[1])
    for ticker in tickers:
        if ticker not in gcnv.v_tickers:
            continue
        closes = gcnv.data_handler.list_data([["stock", ticker]], 45)[0]
        if len(closes) == 0:
            continue
    
        current = int(closes[-1])
        min_ = int(min(closes))
        gcnv.options.pop(ticker, None) # delete all elements for ticker first
        try_strikes(ticker, current, 'P', command[2]) # command[2] is something like: "20191220"
        try_strikes(ticker, min_, 'P', command[2])

    print(gcnv.options)

    rows = []
    for ticker, values in gcnv.options.items():
        values = [v for v in values if v['price'] and v['price'] != 0]
        if len(values) == 2:
            values.sort(key=lambda v: v['price'])
            row = [
                ticker,
                values[1]['price'] / values[0]['price'],
                values[1]['delta'],
                values[0]['delta'],
                values[1]['strike'],
                values[0]['strike'],
                values[1]['price'],
                values[0]['price']
            ]
        else:
            row = ['-'] * 8
        rows.append(row)
    return rows

def try_strikes(ticker, strike, right, expiration_date):
    gcnv.ib.wait_for_async_request() # to be sure there are no pending requests
    for i in (0, 1, -1, 2, -2, 3, -3):
        sub_strike = strike + i
        gcnv.ib.request_options_contract(
                ticker, sub_strike, right, expiration_date)
        gcnv.ib.wait_for_async_request()
        if (ticker in gcnv.options and
                    next(filter(lambda d: d['strike'] == sub_strike,
                            gcnv.options[ticker]), None)):
            break