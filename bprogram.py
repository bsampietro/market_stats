import sys

import logging

from datetime import datetime, date

from util import *
from datahandler import *
from errors import *
from iv import *
from hv import *
from mixed_vs import *

from texttable import Texttable

import os.path


# Helper methods
def get_iv_row(ticker, date):
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
            mixed_vs.negative_difference_ratio(),
            mixed_vs.difference_average()]
        assert len(row) == DATA_RESULTS
        row += ['-']
        row += iv.period_iv_ranks(max_results = IVR_RESULTS)
        return row
    except GettingInfoError as e:
        print(e)
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
            print(f"Getting HV data for ticker {ticker}...")
            data_handler.request_historical_data("HV", ticker)



# Global variables
data_handler = None
connected = False
IVR_RESULTS = 7 # Number of historical IVR rows
DATA_RESULTS = 10 # Number of main data rows

# Main method
if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler("_bprogram.log"))
    ## logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        connected = (sys.argv[1] == "connect")
    data_handler = DataHandler(connected)

    while True:
        command = input('--> ')
        if command == "":
            continue

        command = command.split(" ")
        command += [""] * 5 # adding empty strings to the list to make it easier to manage the command

        try:

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

            elif command[0] == "" or command[1] == "":
                continue

            elif command[0] == "v":

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
                    'IV2HV-',
                    'IV2HVdf',
                    '-', 
                    'IVR']
                assert DATA_RESULTS == (len(header) - 2)
                header += ['-'] * (IVR_RESULTS - 1) # 1 is the IVR title
                t.add_row(header)

                text_file = command[1] + ".txt"

                if os.path.isfile(text_file):
                    tickers = read_stock_list(text_file)
                    for ticker in tickers:
                        bring_if_connected(ticker)
                        t.add_row(get_iv_row(ticker, get_query_date(ticker)))
                else:
                    ticker = command[1].upper()
                    
                    duration = 365
                    if command[2] != "":
                        duration = command[2]

                    bring_if_connected(ticker)
                    t.add_row(get_iv_row(ticker, get_query_date(ticker)))

                print("Waiting for async request...")
                data_handler.wait_for_async_request()
                print(t.draw())

            elif command[0] == "s":
                # get the stock thing going
                print("doing the 's' command...")

            else:
                print("Command not recognized")

        except GettingInfoError as e:
            print(e)

        except FileNotFoundError as e:
            print(f"Didn't find file: {e}")

        except:
            data_handler.disconnect()
            raise
