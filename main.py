import sys, os
import logging
import readline

from lib import util
from lib.errors import *
from models.datahandler import DataHandler
import controllers.iv as iv_controller
import controllers.pairs as pairs_controller
import controllers.options as options_controller
import controllers.helper
import controllers.general as general_controller
import controllers.correlations as correlations_controller
import controllers.show as show_controller

import gcnv
from lib import html
from ib.ib_data import IBData

from ib.ib_data_test import IBDataTest

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
test = 'test' in parameters
batch = 'batch' in parameters

if parameters[1] == "connect":
    gcnv.ib = IBData() if not test else IBDataTest()
    gcnv.ib.wait_for_api_ready()
gcnv.data_handler = DataHandler()
gcnv.messages = []
gcnv.v_tickers = set(util.read_symbol_list(f"{gcnv.APP_PATH}/input/options.txt"))
gcnv.store_dir = "/media/ramd"
if batch:
    batch_commands = iter(
        util.read_symbol_list(f"{gcnv.APP_PATH}/input/batch_commands.txt"))

# MAIN METHOD
if __name__ == "__main__" and not exec_in_console:
    last_command = []

    while True:
        if batch:
            try:
                next_command = next(batch_commands)
                print(f"-> Running: '{next_command}'")
                command = next_command
            except StopIteration:
                break
        else:
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

        header = rows = None
        try:
            if command[0] == "exit" or command[0] == "e":
                gcnv.data_handler.save()
                if gcnv.ib:
                    gcnv.ib.disconnect()
                break

            elif command[0] == "e!":
                if gcnv.ib:
                    gcnv.ib.disconnect()
                break

            elif command[0] == "delete" or command[0] == "del":
                general_controller.delete(command)

            elif command[0] == "corr":
                correlations_controller.pair(command)

            elif command[0] == "corrs":
                header, rows = correlations_controller.table(command)

            elif command[0] == "chart":
                if command[1] == "pair":
                    general_controller.chart_pair(command)

            elif command[0] == "print":
                if command[1] == "price":
                    try:
                        header, rows = show_controller.price(command)
                    except KeyError:
                        print("Ticker not found")
                elif command[1] == "keys":
                    show_controller.instruments(command)

            elif command[0] == "prvol":
                header, rows, order_column = iv_controller.table(command)

            elif command[0] == "pair":
                header, rows, order_column = pairs_controller.table(command)

            elif command[0] == "update":
                print("Updating stock values...")
                general_controller.update_stock(command)

            elif command[0] == "earnings":
                general_controller.save_earnings(command)

            elif command[0] == "options":
                header = options_controller.get_header()
                rows = options_controller.get_rows(command)

            else:
                print("Command not recognized")

            if gcnv.ib:
                print("Waiting for async request...")
                gcnv.ib.wait_for_async_request()

            if header and rows:
                command = filter(lambda p: p != '', command)
                with open(f"{gcnv.store_dir}/{'-'.join(command)}.html", "w") as f:
                    for row in rows:
                        for i in range(len(row)):
                            if isinstance(row[i], float):
                                row[i] = f"{row[i]:.2f}"
                            if vars().get("order_column") == i:
                                row[i] = f"<b>{row[i]}</b>"
                    f.write(html.table(rows, header_row=header,
                        style=("border: 1px solid #000000; border-collapse: collapse;"
                                "font: 11px arial, sans-serif;")))
                print(f"Finished. Stored report on {gcnv.store_dir}.")

            if len(gcnv.messages) > 0:
                print("\n".join(gcnv.messages))
                gcnv.messages = []

        except GettingInfoError as e:
            print(e)

        except FileNotFoundError as e:
            print(f"Didn't find file: {e}")

        except:
            if gcnv.ib:
                gcnv.ib.disconnect()
            # print(sys.exc_info()[0])
            raise