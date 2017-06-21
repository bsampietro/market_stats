import sys

import time
import logging

from util import *
from datahandler import *
from errors import *
from ivrank import *

def print_ticker(ticker, date):
    try:
        print(f"{ticker} at {date}")

        iv_rank = IVRank(data_handler, ticker)
        show = format(f"IVR: {format(iv_rank.get_iv_rank_at(date), '.2f')}", '<19')
        show += format(f"IV: {format(iv_rank.get_iv_at(date), '.2f')}", '<20')
        show += format(f"IV avg: {format(iv_rank.average_period_iv(), '.2f')}", '<21')
        show += format(f"IV min: {format(iv_rank.min_iv(), '.2f')}", '<18')
        show += format(f"IV max: {format(iv_rank.max_iv(), '.2f')}", '<18')
        print(show)

        show = ""
        for iv in iv_rank.get_period_iv_ranks(max_results = 15):
            show += format(iv, '<10.2f')
        print(show)
        
    except GettingInfoError as e:
        print(e)
        print("Try again when available message appears...")

    
if __name__ == "__main__":
    connect = False
    if len(sys.argv) > 1:
        connect = (sys.argv[1] == "connect")
    data_handler = DataHandler(connect)

    while True:
        command = input('--> ')
        if command == "":
            continue

        command = command.split(" ")

        if command[0] == "exit" or command[0] == "e":
            data_handler.stop()
            break

        if command[0] == "list":
            tickers = read_stock_list(command[1])
            for ticker in tickers:
                print_ticker(ticker, today_in_string())
        else:
            ticker = command[0].upper()
            
            duration = 365
            if len(command) == 2:
                duration = command[1]

            # print_ticker(ticker, "20170619")
            print_ticker(ticker, today_in_string())


#time.sleep(60)
