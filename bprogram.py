import sys, os
import logging
from datetime import datetime, date
import readline
import urllib.request
import time

from lib import util, core
from lib.errors import *
from models.datahandler import DataHandler
from models.iv import IV
from models.hv import HV
from models.mixed_vs import MixedVs
from models.stock import Stock
from models.pair import Pair

from helpers.bprogram_helper import *

import gcnv

#from texttable import Texttable
from lib import html


# INITIALIZATION
# Detects if it is executed as the main file/import OR through a console exec to 
# make import available and initialize variables
# __file__ variable is not available in python console
exec_in_console = '__file__' not in vars()

# Set root path
if exec_in_console:
    gcnv.APP_PATH = os.path.abspath("")
else:
    gcnv.APP_PATH = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(filename=f"{gcnv.APP_PATH}/log/bprogram.log", level=logging.INFO)

parameters = sys.argv + 5 * ['']
gcnv.connected = (parameters[1] == "connect")
gcnv.data_handler = DataHandler(gcnv.connected)
gcnv.data_handler.wait_for_api_ready()
try:
    gcnv.back_days = int(parameters[2]) * 30
except ValueError as e:
    gcnv.back_days = 365 * 2


# MAIN METHOD
if __name__ == "__main__" and not exec_in_console:
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
                    gcnv.data_handler.stop()
                except KeyError as e:
                    print(f"Exit with error: {e}")
                break

            if command[0] == "":
                continue

            elif command[0] == "help":
                print("HELP")
                print("delete [nr_of_back_days] => deletes current date, or number of back days, or entry")
                print("corr symbol1 symbol2")
                print("corrs file.txt => prints all the correlations with correlation bigger than 0.60")
                print("chart pair symbol1 symbol2 fixed_stdev_ratio")
                print("prvol file.txt|symbol [back_days] [ord]")
                print("pair (file.txt)|(symbol1 symbol2 [fixed_stdev_ratio]) [ord]")
                print("print symbol")
                continue

            elif command[0] == "delete":
                if command[1] == "":
                    gcnv.data_handler.delete_at(util.today_in_string())
                    print("Today deleted")
                else:
                    try:
                        gcnv.data_handler.delete_back(int(command[1]))
                        print("Back days deleted")
                    except (ValueError, TypeError) as e:
                        gcnv.data_handler.delete_ticker(command[1].upper())
                        print("Ticker deleted")
                continue

            elif command[0] == "corr":
                pair = Pair(gcnv.data_handler, command[1].upper(), command[2].upper())

                back_days = gcnv.back_days
                if command[3] != "":
                    try:
                        back_days = int(command[3])
                    except ValueError:
                        pass

                print(f"  Correlation: {format(pair.correlation(back_days), '.2f')}")
                print(f"  Beta:        {format(pair.beta(back_days), '.2f')}")
                print(f"  Volat ratio: {format(pair.stdev_ratio(back_days), '.2f')}")
                continue

            elif command[0] == "corrs" or command[0] == "uncorrs":
                symbols = util.read_symbol_list(f"{gcnv.APP_PATH}/input/{command[1]}.txt")
                text_output_file = open(f"/media/ramd/{'-'.join(command)}", "w")
                for symbol1 in symbols:
                    print(symbol1)
                    text_output_file.write(f"{symbol1}\n")
                    for symbol2 in symbols:
                        if symbol1 == symbol2 or symbol1 == "---" or symbol2 == "---":
                            continue
                        try:
                            pair = Pair(gcnv.data_handler, symbol2, symbol1)
                            out_string = f"  {symbol2}: {format(pair.correlation(gcnv.back_days), '.2f')} | {format(pair.stdev_ratio(gcnv.back_days), '.2f')}"
                            if command[0] == "corrs":
                                if symbol1 in gcnv.BETA_REFERENCES or (pair.correlation(gcnv.back_days) > gcnv.MIN_CORRELATED_CORRELATION or pair.correlation(gcnv.back_days) < -gcnv.MIN_CORRELATED_CORRELATION):
                                    print(out_string)
                                    text_output_file.write(f"{out_string}\n")
                            else:
                                if pair.correlation(gcnv.back_days) > -gcnv.MAX_UNCORRELATED_CORRELATION and pair.correlation(gcnv.back_days) < gcnv.MAX_UNCORRELATED_CORRELATION:
                                    print(out_string)
                                    text_output_file.write(f"{out_string}\n")
                        except GettingInfoError as e:
                            pass
                text_output_file.close()
                continue

            elif command[0] == "chart":
                if command[1] == "pair":
                    print("Remember to bring data before with the 'pair' command (if needed).")
                    ps = process_pair_string(command[2])
                    pair = Pair(gcnv.data_handler, ps.ticker1, ps.ticker2, ps.stdev_ratio)
                    pair.output_chart()
                continue

            elif command[0] == "print":
                if command[1] == "price":
                    try:
                        header = ['Date', 'Price'] * 8
                        values_printed = 0
                        row = None
                        rows = []
                        for key, value in gcnv.data_handler.stock[command[2].upper()].items():
                            if values_printed % 8 == 0:
                                if row is not None:
                                    rows.append(row)
                                row = []
                            row.append(key)
                            row.append(value)
                            values_printed += 1
                        for i in range(16 - len(row)):
                            row.append('x')
                        rows.append(row)
                    except KeyError:
                        print("Ticker not found")
                elif command[1] == "keys":
                    print("IV:")
                    print(gcnv.data_handler.implied_volatility.keys())
                    print("HV:")
                    print(gcnv.data_handler.historical_volatility.keys())
                    print("STOCK:")
                    print(gcnv.data_handler.stock.keys())
                    continue

            elif command[0] == "prvol":

                header = get_iv_header()
                
                rows = read_symbol_file_and_process(command, get_iv_row)

                # Remove year from date
                current_year = time.strftime('%Y')
                for row in rows:
                    row[1] = row[1].replace(current_year, "")

                # Filter
                if 'filter' in command:
                    rank_column = header.index("LngRnk")
                    options_list = util.read_symbol_list(f"{gcnv.APP_PATH}/input/options.txt") + util.read_symbol_list(f"{gcnv.APP_PATH}/input/stocks.txt")
                    rows = [row for row in rows if not (isinstance(row[rank_column], (int, float)) and 
                            35 < row[rank_column] < 65 and row[0] not in options_list)] # conditions are for exclusion, note the 'not' at the beginning of the if condition

                # Sorting
                order_column = command[3] if command[3] in header else "LngRnk"
                order_column = header.index(order_column)
                def key_select(row):
                    if isinstance(row[order_column], (int, float)):
                        return row[order_column]
                    else:
                        return core.safe_execute(50, ValueError, int, command[4])
                rows.sort(key = key_select, reverse = True)

            elif command[0] == "pair":

                header = get_pairs_header()

                rows = read_pairs_file_and_process(command, get_pairs_row)

                # Sorting
                order_column = command[2] if command[2] in header else "Rank"
                order_column = header.index(order_column)
                def key_select(row):
                    if isinstance(row[order_column], (int, float)):
                        return row[order_column]
                    else:
                        return core.safe_execute(50, ValueError, int, command[4])
                rows.sort(key = key_select, reverse = True)

            elif command[0] == "update":
                update_stock(command)
                print("Updating stock values...")
                gcnv.data_handler.wait_for_async_request()
                continue

            elif command[0] == "earnings":
                # store earnings
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
                save_earnings(earnings_data)
                continue

            else:
                print("Command not recognized")
                continue

            print("Waiting for async request...")
            gcnv.data_handler.wait_for_async_request()

            # t = Texttable(max_width = 0)
            # t.set_precision(2)
            # t.add_row(header)
            # for row in rows:
            #     t.add_row(row)
            # print(t.draw())

            command = filter(lambda c: c != '', command)
            with open(f"/media/ramd/{'-'.join(command)}.html", "w") as f:
                for row in rows:
                    for i in range(len(row)):
                        if isinstance(row[i], float):
                            # row[i] = round(row[i], 2)
                            row[i] = f"{row[i]:.2f}"
                f.write(html.table(rows, header_row=header,
                    style="border: 1px solid #000000; border-collapse: collapse; font: 12px arial, sans-serif;"))

            print("Finished. Stored report on /media/ramd.")

        except GettingInfoError as e:
            print(e)

        except FileNotFoundError as e:
            print(f"Didn't find file: {e}")

        except:
            gcnv.data_handler.disconnect()
            raise
