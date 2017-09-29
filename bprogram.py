import sys

import logging

from datetime import datetime, date
import os.path

from util import *
from datahandler import *
from errors import *
from iv import *
from hv import *
from mixed_vs import *
from stock import *
from pair import *

from texttable import Texttable

# Helper methods
def get_iv_header():
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
    header += ['-'] * (IVR_RESULTS - 1) # 1 is the IVR title
    return header

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
        row += ['-']
        row += iv.period_iv_ranks(back_days, max_results = IVR_RESULTS)
        return row
    except GettingInfoError as e:
        print(e)
        return []


def get_stock_header():
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
        'Max200',
        '-',
        'UpCl15',
        'DoCl15',
        'ConsUp15',
        'ConsDwn15']
    return header


# back_days parameter added for compliance with get_xxx_row methods
# as they are passed as parameter to read_symbol_file_and_process
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
            stock.max(200),
            '-',
            stock.closes_nr(15, up = True),
            stock.closes_nr(15, up = False),
            stock.consecutive_nr(15, up = True),
            stock.consecutive_nr(15, up = False)
            ]
        return row
    except GettingInfoError as e:
        print(e)
        return []


def get_hv_header():
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
    return header


# back_days parameter added for compliance with get_xxx_row methods
# as they are passed as parameter to read_symbol_file_and_process
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
        return row
    except GettingInfoError as e:
        print(e)
        return []


def get_pairs_header():
    header = ['Pair',
        'Date',
        '-',
        'Last200',
        'Min200',
        'Max200',
        'Rank200',
        'MA200',
        '-',
        'Last50',
        'Min50',
        'Max50',
        'Rank50',
        'MA50',
        '-',
        'VRatio',
        'Corr',
        '-']
    header += ['-'] * 5
    return header


def get_pairs_row(ticker1, ticker2, fixed_stdev_ratio = None):
    try:
        pair = Pair(data_handler, ticker1, ticker2, fixed_stdev_ratio)
        date = '-' if data_handler.get_max_stored_date("STOCK", ticker1) is None else date_in_string(data_handler.get_max_stored_date("STOCK", ticker1))
        row = [ticker1 + '-' + ticker2,
            date,
            '-',
            pair.get_last_close(200),
            pair.min(200),
            pair.max(200),
            pair.current_rank(200),
            pair.ma(200),
            '-',
            pair.get_last_close(50),
            pair.min(50),
            pair.max(50),
            pair.current_rank(50),
            pair.ma(50),
            '-',
            pair.stdev_ratio(365),
            pair.correlation(365),
            '-']
        # ranks = pair.period_ranks(50)[-5:]
        # ranks.reverse()
        # row += ranks
        closes = pair.closes(50)[-5:]
        closes.reverse()
        row += closes
        return row
    except GettingInfoError as e:
        print(e)
        return []


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
        if ticker not in NO_OPTIONS:
            max_stored_date = data_handler.get_max_stored_date("IV", ticker)
            if (max_stored_date is None) or max_stored_date.date() < date.today():
                print(f"Getting IV data for ticker {ticker}...")
                data_handler.request_historical_data("IV", ticker)

        if ticker not in NO_OPTIONS:
            max_stored_date = data_handler.get_max_stored_date("HV", ticker)
            if (max_stored_date is None) or (max_stored_date.date() < (date.today() - timedelta(days = 4))): # arbitrary 4 days because is not needed day to day
                print(f"Getting HV data for ticker {ticker}...")
                data_handler.request_historical_data("HV", ticker)

        max_stored_date = data_handler.get_max_stored_date("STOCK", ticker)
        if (max_stored_date is None) or max_stored_date.date() < date.today():
            print(f"Getting STOCK data for ticker {ticker}...")
            data_handler.request_historical_data("STOCK", ticker)


def read_symbol_file_and_process(command, get_row_method, back_days = None):
    text_file = command + ".txt"
    rows = []
    if os.path.isfile(text_file):
        tickers = read_symbol_list(text_file)
        for ticker in tickers:
            if ticker == '---':
                if len(rows) > 0:
                    rows.append(['-'] * len(rows[0]))
                continue
            bring_if_connected(ticker)
            row = get_row_method(ticker, get_query_date(ticker), back_days)
            if len(row) > 0:
                rows.append(row)
    else:
        ticker = command.upper()
        bring_if_connected(ticker)
        row = get_row_method(ticker, get_query_date(ticker), back_days)
        if len(row) > 0:
            rows.append(row)
    return rows


def read_pairs_file_and_process(command, get_row_method):
    text_file = command[1] + ".txt"
    rows = []
    if os.path.isfile(text_file):
        pairs = read_symbol_list(text_file)
        for pair in pairs:
            if pair == '---':
                if len(rows) > 0:
                    rows.append(['-'] * len(rows[0]))
                continue
            data = pair.split('-') + [None] * 5
            ticker1 = data[0]; ticker2 = data[1]; stdev_ratio = data[2]
            bring_if_connected(ticker1)
            bring_if_connected(ticker2)
            row = get_row_method(ticker1, ticker2, stdev_ratio)
            if len(row) > 0:
                rows.append(row)
    else:
        ticker1 = command[1].upper(); ticker2 = command[2].upper(); stdev_ratio = command[3]
        bring_if_connected(ticker1)
        bring_if_connected(ticker2)
        row = get_row_method(ticker1, ticker2, stdev_ratio)
        if len(row) > 0:
            rows.append(row)
    return rows



# Global variables
data_handler = None
connected = False
IVR_RESULTS = 7 # Number of historical IVR rows
BACK_DAYS = 365 # Number of back days to take into account for statistics
NO_OPTIONS = ['IEF', 'PPLT', 'URA', 'DBA', 'JJC'] # securities that should not bring options data
BETA_REFERENCES = ["SPY"]

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

            if command[0] == "":
                continue

            elif command[0] == "help":
                print("HELP")
                print("delete [nr_of_back_days] => deletes current date or number of back days")
                print("corr symbol1 symbol2")
                print("corrs file.txt => prints all the correlations with correlation bigger than 0.60")
                print("chart pair symbol1 symbol2 fixed_stdev_ratio")
                print("vol file.txt|symbol [back_days] [ord]")
                print("st file.txt [ord]")
                print("hvol file.txt|symbol")
                print("pair (file.txt)|(symbol1 symbol2 [fixed_stdev_ratio]) [ord]")
                continue

            elif command[0] == "delete":
                if command[1] == "":
                    data_handler.delete_at(today_in_string())
                else:
                    try:
                        data_handler.delete_back(int(command[1]))
                    except (ValueError, TypeError) as e:
                        data_handler.delete_ticker(command[1].upper())
                print("Entries deleted")
                continue

            elif command[0] == "corr":
                pair = Pair(data_handler, command[1].upper(), command[2].upper())
                print(f"  Correlation: {format(pair.correlation(365), '.2f')}")
                print(f"  Beta:        {format(pair.beta(365), '.2f')}")
                print(f"  Vol ratio:   {format(pair.stdev_ratio(365), '.2f')}")
                continue

            elif command[0] == "corrs" or command[0] == "uncorrs":
                symbols = read_symbol_list(command[1] + '.txt')
                text_output_file = open(f"/media/ramd/{'-'.join(command)}", "w")
                for symbol1 in symbols:
                    print(symbol1)
                    text_output_file.write(f"{symbol1}\n")
                    for symbol2 in symbols:
                        if symbol1 == symbol2 or symbol1 == "---" or symbol2 == "---":
                            continue
                        try:
                            pair = Pair(data_handler, symbol2, symbol1)
                            out_string = f"  {symbol2}: {format(pair.correlation(365), '.2f')} | {format(pair.stdev_ratio(365), '.2f')}"
                            if command[0] == "corrs":
                                if symbol1 in BETA_REFERENCES or (pair.correlation(365) > 0.60 or pair.correlation(365) < -0.60):
                                    print(out_string)
                                    text_output_file.write(f"{out_string}\n")
                            else:
                                if pair.correlation(365) > -0.20 and pair.correlation(365) < 0.20:
                                    print(out_string)
                                    text_output_file.write(f"{out_string}\n")
                        except GettingInfoError as e:
                            pass
                text_output_file.close()
                continue

            elif command[0] == "chart":
                if command[1] == "pair":
                    print("Remember to bring data before with the 'pair' command (if needed).")
                    pair = Pair(data_handler, command[2].upper(), command[3].upper(), command[4])
                    pair.output_chart()
                continue

            elif command[0] == "vol":

                header = get_iv_header()

                back_days = BACK_DAYS
                if command[2] != "":
                    try:
                        back_days = int(command[2])
                        if back_days <= 30:
                            # take it as months if less than 30
                            back_days *= 30
                    except ValueError:
                        pass

                rows = read_symbol_file_and_process(command[1], get_iv_row, back_days)

                if command[3] == "ord" or command[3] != "":
                    try:
                        order_column = int(command[3])
                    except (ValueError, TypeError) as e:
                        order_column = 11 # order by IVR%
                    rows.sort(key = lambda row: row[order_column] if isinstance(row[order_column], (int, float)) else 25)

            elif command[0] == "st":

                header = get_stock_header()

                rows = read_symbol_file_and_process(command[1], get_stock_row)

                if command[2] == "ord":
                    # order by MA50%
                    rows.sort(key = lambda row: row[8] if isinstance(row[8], (int, float)) else 0)

            elif command[0] == "hvol":

                header = get_hv_header()

                rows = read_symbol_file_and_process(command[1], get_hv_row)

            elif command[0] == "pair":

                header = get_pairs_header()

                rows = read_pairs_file_and_process(command, get_pairs_row)

                if "ord" in command:
                    # order by rank
                    rows.sort(key = lambda row: row[12] if isinstance(row[12], (int, float)) else 0)

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

            with open(f"/media/ramd/{'-'.join(command)}", "w") as f:
                f.write(t.draw())

        except GettingInfoError as e:
            print(e)

        except FileNotFoundError as e:
            print(f"Didn't find file: {e}")

        except:
            data_handler.disconnect()
            raise
