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

from helpers.main_helper import *

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
gcnv.messages = []
gcnv.v_tickers = util.read_symbol_list(f"{gcnv.APP_PATH}/input/options.txt")
gcnv.store_dir = "/media/ramd"

# MAIN METHOD
if __name__ == "__main__" and not exec_in_console:
    last_command = []

    while True:
        command = input('--> ')
        if command == "":
            continue

        command = command.split()
        # adding empty strings to the list to make it easier to manage the command
        command += [""] * 5

        if command[0] == "":
            continue

        if command[0] == "l":
            command = last_command
        else:
            last_command = command

        try:
            if command[0] == "exit" or command[0] == "e":
                gcnv.data_handler.save()
                gcnv.data_handler.disconnect()
                break

            elif command[0] == "e!":
                gcnv.data_handler.disconnect()
                break

            elif command[0] == "delete" or command[0] == "del":
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
                continue

            elif command[0] == "corr":
                pair = Pair(gcnv.data_handler, command[1].upper(), command[2].upper())
                back_days = core.safe_execute(gcnv.BACK_DAYS, ValueError,
                                lambda x: int(x) * 30, command[3])

                print(f"  Correlation: {format(pair.correlation(back_days), '.2f')}")
                print(f"  Beta:        {format(pair.beta(back_days), '.2f')}")
                print(f"  Volat ratio: {format(pair.stdev_ratio(back_days), '.2f')}")
                continue

            elif command[0] == "corrs":
                back_days = core.safe_execute(gcnv.BACK_DAYS, ValueError,
                                lambda x: int(x) * 30, command[2])
                header = ["", "SPY", "TLT", "IEF", "GLD", "USO", "UNG", "FXE", "FXY",
                            "FXB", "IYR", "XLU", "EFA", "EEM", "VXX"]
                rows = []
                for symbol in util.read_symbol_list(
                        f"{gcnv.APP_PATH}/input/{command[1]}.txt"):
                    row = [symbol]
                    for head_symbol in header[1:]:
                        if symbol == head_symbol:
                            row.append("-")
                        else:
                            try:
                                pair = Pair(gcnv.data_handler, head_symbol, symbol)
                                row.append(pair.correlation(back_days))
                            except GettingInfoError:
                                row.append("-")
                    rows.append(row)

            elif command[0] == "chart":
                if command[1] == "pair":
                    print("Remember to bring data before with the 'pair' command (if needed).")
                    ps = process_pair_string(command[2])
                    pair = Pair(gcnv.data_handler, ps.ticker1, ps.ticker2, ps.stdev_ratio)
                    back_days = core.safe_execute(gcnv.PAIR_BACK_DAYS, ValueError,
                                    lambda x: int(x) * 30, command[3])
                    pair.output_chart(back_days)
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
                    iv = list(gcnv.data_handler.implied_volatility.keys())
                    iv.sort()
                    print(iv)

                    print("HV:")
                    hv = list(gcnv.data_handler.historical_volatility.keys())
                    hv.sort()
                    print(hv)

                    print("STOCK:")
                    stock = list(gcnv.data_handler.stock.keys())
                    stock.sort()
                    print(stock)

                    print("Futures:")
                    futures = [st for st in stock if util.contract_type(st) == "FUT"]
                    print(futures)

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
                    rank_column = header.index("BDRnk")
                    options_list = (util.read_symbol_list(f"{gcnv.APP_PATH}/input/options.txt") +
                                    util.read_symbol_list(f"{gcnv.APP_PATH}/input/stocks.txt"))
                    rows = [row for row in rows if not (
                                isinstance(row[rank_column], (int, float)) and 
                                35 < row[rank_column] < 65 and row[0] not in options_list)]
                                # conditions are for exclusion, note the 'not' at 
                                #the beginning of the if condition

                # Sorting
                order_column = command[3] if command[3] in header else "BDRnk"
                order_column = header.index(order_column)
                rows.sort(key = lambda row: row[order_column], reverse = True)
                util.add_separators_to_list(rows, lambda row, sep: row[order_column] <= sep, [50])

            elif command[0] == "pair":
                header = get_pairs_header()

                rows = read_pairs_file_and_process(command, get_pairs_row)

                # Sorting
                order_column = command[2] if command[2] in header else "Rank"
                order_column = header.index(order_column)
                rows.sort(key = lambda row: row[order_column], reverse = True)
                util.add_separators_to_list(rows, lambda row, sep: row[order_column] <= sep, [50])

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

            command = filter(lambda p: p != '', command)
            with open(f"{gcnv.store_dir}/{'-'.join(command)}.html", "w") as f:
                for row in rows:
                    for i in range(len(row)):
                        if isinstance(row[i], float):
                            # row[i] = round(row[i], 2)
                            row[i] = f"{row[i]:.2f}"
                        if vars().get("order_column") == i:
                            row[i] = f"<b>{row[i]}</b>"
                f.write(html.table(rows, header_row=header,
                    style=("border: 1px solid #000000; border-collapse: collapse;"
                            "font: 12px arial, sans-serif;")))
            print(f"Finished. Stored report on {gcnv.store_dir}.")

            if len(gcnv.messages) > 0:
                print("\n".join(gcnv.messages))
                gcnv.messages = []

        except GettingInfoError as e:
            print(e)

        except FileNotFoundError as e:
            print(f"Didn't find file: {e}")

        except:
            gcnv.data_handler.disconnect()
            # print(sys.exc_info()[0])
            raise