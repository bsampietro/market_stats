from controllers.helper import *
import time
import gcnv

def get_header():
    return ['Tckr', 'Ratio']

def get_rows(command):
    tickers = get_tickers_from_command(command[1])
    for ticker in tickers:
        if ticker not in gcnv.v_tickers:
            continue
        closes = gcnv.data_handler.list_data([["STOCK", ticker]], 45)[0]
        if len(closes) == 0:
            continue
    
        current = closes[-1]
        min_ = min(closes)
        #max_ = max(closes)
        gcnv.ib.request_options_contract(ticker, int(current), 'P', "20191115")
        gcnv.ib.request_options_contract(ticker, int(min_), 'P', "20191115")
        #gcnv.ib.request_options_contract(ticker, int(max_), 'C')
    if gcnv.ib:
        gcnv.ib.wait_for_async_request()
    
    print(gcnv.options)
    rows = []
    for ticker, values in gcnv.options.items():
        values = list(filter(lambda v: v['price'] is not None, values))
        if len(values) == 2:
            values.sort(key=lambda v: v['price'])
            ratio = values[1]['price'] / values[0]['price']
            rows.append([ticker, ratio])
    return rows

"""
defaultdict(<class 'list'>, {'SPY': [{'delta': -0.5988427070239228, 'price': 9.140000343322754}, {'delta': -0.3600924821349719, 'price': 5.159999847412109}], 'ABBV': [{'delta': -0.190729836733974, 'price': 0.8899999856948853}], 'AMAT': [{'delta': -0.4762451026528441, 'price': 2.7200000286102295}, {'delta': -0.22002472219108876, 'price': 1.0199999809265137}]})
"""