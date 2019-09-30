import os
import gcnv
import json
import urllib.request

from models.pair import Pair
from controllers.helper import *

from lib import util, core

def update_stock(command):
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
        for ticker in tickers:
            gcnv.ib.request_market_data("STOCK", ticker)
    else:
        ticker = command[1].upper()
        gcnv.ib.request_market_data("STOCK", ticker)
    if gcnv.ib:
        gcnv.ib.wait_for_async_request()

def save_earnings(command):
    earnings_data = {}
    for ticker in util.read_symbol_list(f"{gcnv.APP_PATH}/input/{command[1]}.txt"):
        f = urllib.request.urlopen(f"https://www.nasdaq.com/earnings/report/{ticker}")
        page_bytes = f.read()
        location = page_bytes.find(b"earnings on")
        if location == -1:
            print(f"Couldn't find earnings for {ticker}")
        else:
            earnings_data[ticker] = page_bytes[location+13:location+25].decode()
            print(f"Stored earnings for {ticker}")
    
    with open(f"{gcnv.APP_PATH}/data/earnings.json", "w") as f:
        json.dump(earnings_data, f, indent=4)

def delete(command):
    if command[1] == "":
        gcnv.data_handler.delete_at(util.today_in_string())
        print("Today deleted")
    elif command[1].isdigit():
        gcnv.data_handler.delete_back(int(command[1]))
        print("Back days deleted")
    else:
        for ticker in filter(lambda p: p != '', command[1:]):
            gcnv.data_handler.delete_ticker(ticker.upper())
            print(f"{ticker} deleted")

def chart_pair(command):
    print("Remember to bring data before with the 'pair' command (if needed).")
    ps = process_pair_string(command[2])
    pair = Pair(ps.ticker1, ps.ticker2, ps.stdev_ratio)
    back_days = core.safe_execute(gcnv.PAIR_BACK_DAYS, ValueError,
                    lambda x: int(x) * 30, command[3])
    pair.output_chart(back_days)