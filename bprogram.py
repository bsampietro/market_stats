import sys

import logging

from datetime import datetime, date

from util import *
from datahandler import *
from errors import *
from iv import *
from hv import *
from mixed_vs import *
from stock import *
from pair import *

from texttable import Texttable

import os.path


# Helper methods
def get_iv_row(ticker, date, back_days):
    try:
        iv = IV(data_handler, ticker)
        hv = HV(data_handler, ticker)
        mixed_vs = MixedVs(data_handler, iv, hv)

        row = [ticker,
            date,
            iv.get_at(date),
            iv.current_to_average_ratio(date, back_days),
            mixed_vs.iv_current_to_hv_average(date, back_days),
            iv.period_average(back_days),
            hv.period_average(back_days),
            mixed_vs.iv_average_to_hv_average(back_days),
            mixed_vs.negative_difference_ratio(back_days),
            mixed_vs.difference_average(back_days)]
        assert len(row) == DATA_RESULTS
        row += ['-']
        row += iv.period_iv_ranks(back_days, max_results = IVR_RESULTS)
        return row
    except GettingInfoError as e:
        print(e)
        return empty_row(ticker, IVR_RESULTS + DATA_RESULTS)


# back_days parameter added for compliance with get_xxx_row methods
# as they are passed as parameter to read_file_and_process
def get_stock_row(ticker, date, back_days = None):
    try:
        stock = Stock(data_handler, ticker)
        row = [ticker,
            date,
            stock.get_close_at(date),
            '-',
            stock.ma(30),
            stock.current_to_ma_percentage(date, 30),
            '-',
            stock.ma(50),
            stock.current_to_ma_percentage(date, 50),
            '-',
            stock.ma(200),
            stock.current_to_ma_percentage(date, 200),
            '-',
            stock.min(200),
            stock.max(200)]
        assert len(row) - 1 == STOCK_RESULTS
        return row
    except GettingInfoError as e:
        print(e)
        return empty_row(ticker, STOCK_RESULTS)


# back_days parameter added for compliance with get_xxx_row methods
# as they are passed as parameter to read_file_and_process
def get_hv_row(ticker, date, back_days = None):
    try:
        stock = Stock(data_handler, ticker)
        iv = IV(data_handler, ticker)
        row = [ticker,
            date,
            stock.hv(30),
            stock.hv(365),
            stock.hv_average(),
            max(stock.period_hvs()),
            '-',
            stock.percentage_hv(30),
            stock.percentage_hv(365),
            stock.percentage_hv_average(),
            max(stock.percentage_period_hvs())]
        assert len(row) - 1 == HV_RESULTS
        return row
    except GettingInfoError as e:
        print(e)
        return empty_row(ticker, STOCK_RESULTS)


def empty_row(ticker, blank_columns):
    return [ticker] + ['-'] * blank_columns


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
        max_stored_date = data_handler.get_max_stored_date("IV", ticker)
        if (max_stored_date is None) or max_stored_date.date() < date.today():
            print(f"Getting IV data for ticker {ticker}...")
            data_handler.request_historical_data("IV", ticker)

        max_stored_date = data_handler.get_max_stored_date("HV", ticker)
        if (max_stored_date is None) or (max_stored_date.date() < (date.today() - timedelta(days = 4))): # arbitrary 4 days because is not needed day to day
            print(f"Getting HV data for ticker {ticker}...")
            data_handler.request_historical_data("HV", ticker)

        max_stored_date = data_handler.get_max_stored_date("STOCK", ticker)
        if (max_stored_date is None) or max_stored_date.date() < date.today():
            print(f"Getting STOCK data for ticker {ticker}...")
            data_handler.request_historical_data("STOCK", ticker)


def read_file_and_process(command, get_row_method, back_days = None):
    text_file = command + ".txt"
    rows = []
    if os.path.isfile(text_file):
        tickers = read_symbol_list(text_file)
        for ticker in tickers:
            if ticker == '---':
                if len(rows) == 0:
                    raise RuntimeError("Separator can not be on the first row")
                rows.append(empty_row(ticker, len(rows[0]) - 1))
                continue
            bring_if_connected(ticker)
            row = get_row_method(ticker, get_query_date(ticker), back_days)
            if row[1] == '-' and len(rows) > 0:
                continue
            rows.append(row)
    else:
        ticker = command.upper()
        bring_if_connected(ticker)
        rows.append(get_row_method(ticker, get_query_date(ticker), back_days))
    return rows



# Global variables
data_handler = None
connected = False
IVR_RESULTS = 7 # Number of historical IVR rows
DATA_RESULTS = 10 # Number of main data rows
BACK_DAYS = 365 # Number of back days to take into account for statistics
STOCK_RESULTS = 10 + 4 # Number of stock rows besides the ticker + separators
HV_RESULTS = 9 + 1 # Number of hv rows besides the ticker + separators

# Main method
if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler("_bprogram.log"))
    ## logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        connected = (sys.argv[1] == "connect")
    data_handler = DataHandler(connected)

    last_command = []

    while True:
        command = input('--> ')
        if command == "":
            continue

        command = command.split(" ")
        command += [""] * 5 # adding empty strings to the list to make it easier to manage the command

        if command[0] == "l":
            command = last_command
        else:
            last_command = command

        try:

            if command[0] == "exit" or command[0] == "e":
                try:
                    data_handler.stop()
                except KeyError as e:
                    print(f"Exit with error: {e}")
                break

            elif command[0] == "delete":
                if command[1] == "":
                    data_handler.delete_at(today_in_string())
                else:
                    data_handler.delete_back(int(command[1]))
                print("Entries deleted")
                continue

            elif command[0] == "" or command[1] == "":
                continue

            elif command[0] == "corr":
                pair = Pair(data_handler, command[1].upper(), command[2].upper())
                print(f"  Corr: {format(pair.correlation(365), '.2f')}")
                print(f"  Beta: {format(pair.beta(365), '.2f')}")
                continue

            elif command[0] == "corrs":
                symbols = read_symbol_list(command[1] + '.txt')
                for symbol1 in symbols:
                    print(symbol1)
                    for symbol2 in symbols:
                        if symbol1 == symbol2 or symbol1 == "---" or symbol2 == "---":
                            continue
                        pair = Pair(data_handler, symbol2, symbol1)
                        if pair.correlation(365) > 0.60:
                            print(f"  {symbol2}: {format(pair.correlation(365), '.2f')} | {format(pair.stdev_ratio(365), '.2f')}")
                continue

            elif command[0] == "vol":

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

                back_days = BACK_DAYS
                if command[2] != "":
                    try:
                        back_days = int(command[2])
                        if back_days <= 30:
                            # take it as months if less than 30
                            back_days *= 30
                    except ValueError:
                        pass

                rows = read_file_and_process(command[1], get_iv_row, back_days)
                if command[2] != "" and command[3] == "ord":
                    # order by IVR%
                    rows.sort(key = lambda row: row[11] if isinstance(row[11], (int, float)) else 25)

            elif command[0] == "st":

                header = ['Ticker',
                    'Date',
                    'Close',
                    '-',
                    'MA30',
                    'MA30%',
                    '-',
                    'MA50',
                    'MA50%',
                    '-',
                    'MA200',
                    'MA200%',
                    '-',
                    'Min200',
                    'Max200']
                assert STOCK_RESULTS == (len(header) - 1)

                rows = read_file_and_process(command[1], get_stock_row)
                if command[2] == "ord":
                    # order by MA50%
                    rows.sort(key = lambda row: row[8] if isinstance(row[8], (int, float)) else 0)

            elif command[0] == "hvol":

                header = ['Ticker',
                    'Date',
                    'HV30',
                    'HV365',
                    'HVavg',
                    'MaxHV',
                    '-',
                    'HV30%',
                    'HV365%',
                    'HVavg%',
                    'MaxHV%']
                assert HV_RESULTS == (len(header) - 1)

                rows = read_file_and_process(command[1], get_hv_row)

            elif command[0] == "pair":
                pair = Pair(data_handler, command[1].upper(), command[2].upper())
                print(f"  Last: {pair.get_last_close()}")
                print("")
                print(f"  MA50: {pair.ma(50)}")
                # print(f"  MA%: {pair.current_to_ma_diff(50)}")
                print(f"  Min50: {pair.min(50)}")
                print(f"  Max50: {pair.max(50)}")

                print(f"  MA200: {pair.ma(200)}")
                # print(f"  MA%: {pair.current_to_ma_diff(50)}")
                print(f"  Min200: {pair.min(200)}")
                print(f"  Max200: {pair.max(200)}")
                continue

            else:
                print("Command not recognized")
                continue

            t = Texttable(max_width = 0)
            t.set_precision(2)
            t.add_row(header)
            for row in rows:
                t.add_row(row)

            print("Waiting for async request...")
            data_handler.wait_for_async_request()
            print(t.draw())

        except GettingInfoError as e:
            print(e)

        except FileNotFoundError as e:
            print(f"Didn't find file: {e}")

        except:
            data_handler.disconnect()
            raise
