import sys
import logging
from datetime import datetime, date
import os.path

from lib import util
from lib.errors import *
from models.datahandler import DataHandler
from models.iv import IV
from models.hv import HV
from models.mixed_vs import MixedVs
from models.stock import Stock
from models.pair import Pair

from helpers.bprogram_helper import *

import config.constants as const
from config import main_vars

from texttable import Texttable

# Main method
if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler("./log/_bprogram.log"))
    ## logging.basicConfig(level=logging.INFO)

    parameters = sys.argv + 5 * ['']

    main_vars.connected = (parameters[1] == "connect")
    main_vars.data_handler = DataHandler(main_vars.connected)
    try:
        main_vars.back_days = int(parameters[2]) * 30
    except ValueError as e:
        main_vars.back_days = 365


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
                    main_vars.data_handler.stop()
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
                print("print symbol")
                continue

            elif command[0] == "delete":
                if command[1] == "":
                    main_vars.data_handler.delete_at(util.today_in_string())
                else:
                    try:
                        main_vars.data_handler.delete_back(int(command[1]))
                    except (ValueError, TypeError) as e:
                        main_vars.data_handler.delete_ticker(command[1].upper())
                print("Entries deleted")
                continue

            elif command[0] == "corr":
                pair = Pair(main_vars.data_handler, command[1].upper(), command[2].upper())
                print(f"  Correlation: {format(pair.correlation(main_vars.back_days), '.2f')}")
                print(f"  Beta:        {format(pair.beta(main_vars.back_days), '.2f')}")
                print(f"  Volat ratio: {format(pair.stdev_ratio(main_vars.back_days), '.2f')}")
                continue

            elif command[0] == "corrs" or command[0] == "uncorrs":
                symbols = util.read_symbol_list("./input/" + command[1] + '.txt')
                text_output_file = open(f"/media/ramd/{'-'.join(command)}", "w")
                for symbol1 in symbols:
                    print(symbol1)
                    text_output_file.write(f"{symbol1}\n")
                    for symbol2 in symbols:
                        if symbol1 == symbol2 or symbol1 == "---" or symbol2 == "---":
                            continue
                        try:
                            pair = Pair(main_vars.data_handler, symbol2, symbol1)
                            out_string = f"  {symbol2}: {format(pair.correlation(main_vars.back_days), '.2f')} | {format(pair.stdev_ratio(main_vars.back_days), '.2f')}"
                            if command[0] == "corrs":
                                if symbol1 in const.BETA_REFERENCES or (pair.correlation(main_vars.back_days) > const.MIN_CORRELATED_CORRELATION or pair.correlation(main_vars.back_days) < -const.MIN_CORRELATED_CORRELATION):
                                    print(out_string)
                                    text_output_file.write(f"{out_string}\n")
                            else:
                                if pair.correlation(main_vars.back_days) > -const.MAX_UNCORRELATED_CORRELATION and pair.correlation(main_vars.back_days) < const.MAX_UNCORRELATED_CORRELATION:
                                    print(out_string)
                                    text_output_file.write(f"{out_string}\n")
                        except GettingInfoError as e:
                            pass
                text_output_file.close()
                continue

            elif command[0] == "chart":
                if command[1] == "pair":
                    print("Remember to bring data before with the 'pair' command (if needed).")
                    pair = Pair(main_vars.data_handler, command[2].upper(), command[3].upper(), command[4])
                    pair.output_chart()
                continue

            elif command[0] == "print":
                try:
                    header = ['Date', 'Price'] * 8
                    values_printed = 0
                    row = None
                    rows = []
                    for key, value in main_vars.data_handler.stock[command[1].upper()].items():
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

            elif command[0] == "vol":

                header = get_iv_header()

                back_days = main_vars.back_days
                if command[2] != "":
                    try:
                        back_days = int(command[2]) * 30
                    except ValueError:
                        pass

                rows = read_symbol_file_and_process(command, get_iv_row, back_days)

                if command[3] == "ord" or command[3] != "":
                    try:
                        order_column = int(command[3])
                    except (ValueError, TypeError) as e:
                        order_column = const.VOL_ORDER_COLUMN # order by WRnk
                    rows.sort(key = lambda row: row[order_column] if isinstance(row[order_column], (int, float)) else const.MIN_VOL_LINE, reverse = True)

            elif command[0] == "st":

                header = get_stock_header()

                rows = read_symbol_file_and_process(command, get_stock_row)

                if command[2] == "ord":
                    # order by MA50%
                    rows.sort(key = lambda row: row[8] if isinstance(row[8], (int, float)) else 0)

            elif command[0] == "hvol":

                header = get_hv_header()

                rows = read_symbol_file_and_process(command, get_hv_row)

                if command[2] == "ord" or command[2] != "":
                    try:
                        order_column = int(command[2])
                    except (ValueError, TypeError) as e:
                        order_column = 2 # order by HV30
                    rows.sort(key = lambda row: row[order_column] if isinstance(row[order_column], (int, float)) else 5, reverse = True)

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
            main_vars.data_handler.wait_for_async_request()
            print(t.draw())

            with open(f"/media/ramd/{'-'.join(command)}", "w") as f:
                f.write(t.draw())

        except GettingInfoError as e:
            print(e)

        except FileNotFoundError as e:
            print(f"Didn't find file: {e}")

        except:
            main_vars.data_handler.disconnect()
            raise
