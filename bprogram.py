import sys

import time
import logging

from util import *
from datahandler import *
from errors import *
from ivrank import *

from texttable import Texttable

# Global variables
data_handler = None


# Helper methods
def get_row(ticker, date):
    try:
        iv_rank = IVRank(data_handler, ticker)

        row = [ticker, date, iv_rank.get_iv_rank_at(date), iv_rank.get_iv_at(date),
            iv_rank.average_period_iv(), iv_rank.min_iv(), iv_rank.max_iv()]
        row += iv_rank.get_period_iv_ranks(max_results = 10)
        return row
    except GettingInfoError as e:
        print(e)
        print("Try again when available message appears...")
        return ['-'] * 17


# Main method
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


        t = Texttable(max_width = 0)
        t.set_precision(2)

        header = ['Ticker', 'Date', 'IVR', 'IV', 'IV avg', 'IV min', 'IV max']
        header += ['-'] * 10
        t.add_row(header)

        if command[0] == "list":
            tickers = read_stock_list(command[1])
            for ticker in tickers:
                t.add_row(get_row(ticker, today_in_string()))

        else:
            ticker = command[0].upper()
            
            duration = 365
            if len(command) == 2:
                duration = command[1]

            t.add_row(get_row(ticker, today_in_string()))

        print(t.draw())


#time.sleep(60)
