import sys

import time
import logging

from datetime import datetime, date

from util import *
from datahandler import *
from errors import *
from iv import *
from hv import *
from mixed_vs import *

from texttable import Texttable

# Global variables
data_handler = None
connected = False
IVR_RESULTS = 5 # Number of historical IVR rows
DATA_RESULTS = 12 # Number of main data rows


# Helper methods
def get_row(ticker, date):
    try:
        iv = IV(data_handler, ticker)
        hv = HV(data_handler, ticker)
        mixed_vs = MixedVs(data_handler, iv, hv)

        row = [ticker,
            date,
            iv.get_at(date),
            iv.current_to_average_ratio(date),
            mixed_vs.iv_current_to_hv_average(date),
            iv.period_average(),
            hv.period_average(),
            mixed_vs.iv_average_to_hv_average(),
            mixed_vs.difference_average(),
            mixed_vs.negative_difference_ratio(),
            iv.min(),
            iv.max()]
        assert len(row) == DATA_RESULTS
        row += ['-']
        row += iv.period_iv_ranks(max_results = IVR_RESULTS)
        return row
    except GettingInfoError as e:
        print(e)
        print("Try again when available message appears...")
        return [ticker] + ['-'] * (IVR_RESULTS + DATA_RESULTS)

def get_query_date(ticker):
    if connected:
        return today_in_string()
    else:
        max_stored_date = data_handler.get_max_stored_date("IV", ticker)
        if max_stored_date is None:
            return today_in_string()
        else:
            return date_in_string(max_stored_date)

def bring_if_connected(ticker):
    if connected:
        # IV is brought by datahandler when requesting current day implied volatility
        # max_stored_date = data_handler.get_max_stored_date("IV", ticker)
        # if (max_stored_date is None) or max_stored_date.date() < date.today()
        #     data_handler.request_historical_data("IV", ticker)

        max_stored_date = data_handler.get_max_stored_date("HV", ticker)
        if (max_stored_date is None) or (max_stored_date.date() < (date.today() - timedelta(days = 4))): # arbitrary 4 days because is not needed day to day
            print("Getting HV data...")
            data_handler.request_historical_data("HV", ticker)


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
                'IV2HVdf',
                'IV2HV-',
                'IVmin',
                'IVmax',
                '-', 
                'IVR']
            assert DATA_RESULTS == (len(header) - 2)
            header += ['-'] * (IVR_RESULTS - 1) # 1 is the IVR title
            t.add_row(header)

            if command[0] == "list":
                tickers = read_stock_list('daily_list.txt')
                for ticker in tickers:
                    bring_if_connected(ticker)
                    t.add_row(get_row(ticker, get_query_date(ticker)))

            elif ".txt" in command[0]:
                tickers = read_stock_list(command[0])
                for ticker in tickers:
                    bring_if_connected(ticker)
                    t.add_row(get_row(ticker, get_query_date(ticker)))

            else:
                ticker = command[0].upper()
                
                duration = 365
                if len(command) == 2:
                    duration = command[1]

                bring_if_connected(ticker)
                t.add_row(get_row(ticker, get_query_date(ticker)))

            print(t.draw())

        except GettingInfoError as e:
            print(e)

        except FileNotFoundError as e:
            print(f"Didn't find file: {e}")

        except:
            data_handler.disconnect()
            raise


#time.sleep(60)
