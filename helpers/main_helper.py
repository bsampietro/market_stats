import os
import json

from lib import util, core

import gcnv

def read_symbol_file_and_process(command, get_row_method):
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    rows = []
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
    else:
        tickers = [command[1].upper()]
    for ticker in tickers:
        row = get_row_method(ticker, command)
        if len(row) > 0:
            rows.append(row)
    return rows

def read_pairs_file_and_process(command, get_row_method):
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    rows = []
    if os.path.isfile(text_file):
        pairs = util.read_symbol_list(text_file)
    else:
        pairs = [command[1]]
    for pair in pairs:
        row = get_row_method(pair, command)
        if len(row) > 0:
            rows.append(row)
    return rows

def update_stock(command):
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
        for ticker in tickers:
            gcnv.ib.request_market_data("STOCK", ticker)
    else:
        ticker = command[1].upper()
        gcnv.ib.request_market_data("STOCK", ticker)

def save_earnings(data):
    with open(f"{gcnv.APP_PATH}/data/earnings.json", "w") as f:
        json.dump(data, f, indent=4)
