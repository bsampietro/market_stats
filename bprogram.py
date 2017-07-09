import sys

import time
import logging

from util import *
from datahandler import *
from errors import *
from iv import *
from hv import *

from texttable import Texttable

# Global variables
data_handler = None
connected = False
MAX_RESULTS = 8


# Helper methods
def get_row(ticker, date):
    try:
        iv = IV(data_handler, ticker)
        hv = HV(data_handler, ticker)

        row = [ticker,
            date,
            iv.get_at(date),
            iv.current_to_average_ratio(date),
            iv.get_at(date) / hv.period_average(),
            iv.period_average(),
            hv.period_average(),
            iv.period_average() / hv.period_average(),
            iv.min(),
            iv.max()]
        row += ['-']
        row += iv.period_iv_ranks(max_results = MAX_RESULTS)
        return row
    except GettingInfoError as e:
        print(e)
        print("Try again when available message appears...")
        return [ticker] + ['-'] * (MAX_RESULTS + 10) # 10 is row initial size

def get_query_date(ticker):
    if connected:
        return today_in_string()
    else:
        return date_in_string(data_handler.get_max_stored_date("IV", ticker))


# Main method
if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler("output.log"))
    ## logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        connected = (sys.argv[1] == "connect")
    data_handler = DataHandler(connected)

    while True:
        command = input('--> ')
        if command == "":
            continue

        command = command.split(" ")

        if command[0] == "exit" or command[0] == "e":
            try:
                data_handler.stop()
            except KeyError as e:
                print(f"Exit with error: {e}")
            break
        elif command[0] == "delete":
            data_handler.delete_at(today_in_string())
            print("Entries deleted")
            continue

        try:

            t = Texttable(max_width = 0)
            t.set_precision(2)

            header = ['Ticker',
                'Date',
                'IV',
                'IV2IVavg',
                'IV2HVavg',
                'IVavg',
                'HVavg',
                'Avg2Avg',
                'IV min',
                'IV max',
                '-', 
                'IVR']
            header += ['-'] * (MAX_RESULTS - 1) # 1 is the IVR title
            t.add_row(header)

            if command[0] == "list":
                tickers = read_stock_list('daily_list.txt')
                for ticker in tickers:
                    t.add_row(get_row(ticker, get_query_date(ticker)))

            else:
                ticker = command[0].upper()
                
                duration = 365
                if len(command) == 2:
                    duration = command[1]

                t.add_row(get_row(ticker, get_query_date(ticker)))

            print(t.draw())

        except FileNotFoundError as e:
            print(f"Didn't find file: {e}")

        except GettingInfoError as e:
            print(e)

        except:
            data_handler.stop()
            raise


#time.sleep(60)
