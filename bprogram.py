import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

# import argparse
# import collections
# import inspect

# import logging
# import time
# import os.path

from ibapi import wrapper
from ibapi.client import EClient

from ibapi.contract import *

from threading import Thread

import time
import logging
import pickle
import os.path

from ibapi.common import *

import json
from json.decoder import JSONDecodeError

# from ibapi.utils import iswrapper

# types
# from ibapi.common import *
# from ibapi.order_condition import *
# from ibapi.contract import *
# from ibapi.order import *
# from ibapi.order_state import *
# from ibapi.execution import Execution
# from ibapi.execution import ExecutionFilter
# from ibapi.commission_report import CommissionReport
# from ibapi.scanner import ScannerSubscription
# from ibapi.ticktype import *

# from ibapi.account_summary_tags import *

# from ContractSamples import ContractSamples
# from OrderSamples import OrderSamples
# from AvailableAlgoParams import AvailableAlgoParams
# from ScannerSubscriptionSamples import ScannerSubscriptionSamples
# from FaAllocationSamples import FaAllocationSamples

from datetime import datetime, timedelta
import calendar

def get_option_expiration(date):
    day = 21 - (calendar.weekday(date.year, date.month, 1) + 2) % 7
    return datetime(date.year, date.month, day)
# print option_expiration(datetime.today())


def get_options_contract(symbol, date_str, strike, right):
    contract = Contract()
    contract.secType = "OPT"
    contract.exchange = "SMART"
    # contract.primaryExch = "ISLAND"
    contract.currency = "USD"
    contract.multiplier = "100"
    contract.symbol = symbol
    contract.lastTradeDateOrContractMonth = date_str
    contract.strike = strike
    contract.right = right
    return contract

def get_stock_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = "SMART"
    # Specify the Primary Exchange attribute to avoid contract ambiguity 
    contract.primaryExch = "ISLAND"
    return contract

def today_in_string():
    return datetime.today().strftime("%Y%m%d")



class GettingInfoError(Exception):
    pass




class TestWrapper(wrapper.EWrapper):
    def __init__(self):
        wrapper.EWrapper.__init__(self)

class TestClient(EClient):
    def __init__(self, wrapper):
        # print(self.__class__)
        # print(wrapper.__class__)
        EClient.__init__(self, wrapper)

    def keyboardInterrupt(self):
        #intended to be overloaded
        self.disconnect()



class TestApp(TestWrapper, TestClient):
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        # logging.getLogger().setLevel(logging.INFO)
        ## logging.basicConfig(level=logging.INFO)

        # variables
        self.next_req_id = 0
        self.req_id_to_stock_ticker_map = {}

        # self.load_data()
        self.load_data_json()

        self.connect(ipaddress, portid, clientid)
        print("serverVersion:%s connectionTime:%s" % (self.serverVersion(), self.twsConnectionTime()))

        # Try without calling self.run() ??
        thread = Thread(target = self.run)
        thread.start()
        # self.run()

    # Wrapper
    def tickSnapshotEnd(self, reqId: int):
        # super().tickSnapshotEnd(reqId)
        print("Async Bruno answer for snapshot:", reqId)

    def currentTime(self, time: int):
        # super().currentTime(time)
        print(f"Async Bruno answer for time: {time}")

    # def connectAck(self):
    #     """ callback signifying completion of successful connection """
    #     # self.logAnswer(current_fn_name(), vars())
    #     super().connectAck()
    #     # Another option instead of using Threading
    #     # self.do_stuff()

    
    def nextValidId(self, orderId:int):
        """ Receives next valid order id."""
        super().nextValidId(orderId)
        # self.next_req_id = orderId

    def historicalData(self, reqId:TickerId , date:str, open:float, high:float,
                       low:float, close:float, volume:int, barCount:int,
                        WAP:float, hasGaps:int):
        # super().historicalData(reqId, date, open, high, low, close, volume, barCount, WAP, hasGaps)

        if not self.req_id_to_stock_ticker_map[reqId] in self.implied_volatility:
            self.implied_volatility[self.req_id_to_stock_ticker_map[reqId]] = {}
        self.implied_volatility[self.req_id_to_stock_ticker_map[reqId]][date] = close

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        """ Marks the ending of the historical bars reception. """
        # super().historicalDataEnd(reqId, start, end)

        # self.save_data()
        self.save_data_json()
        
        print("Historical data fetched, you can request again...")

    # Client method wrappers
    def request_historical_data(self, contract, what_to_bring = "IV"):
        next_req_id = self.get_next_req_id()
        self.req_id_to_stock_ticker_map[next_req_id] = contract.symbol

        duration_string = "1 Y"
        if contract.symbol in self.implied_volatility:
            last = max(self.implied_volatility[contract.symbol].keys())
            last = datetime.strptime(last, "%Y%m%d")
            delta = datetime.today() - last

            if delta.days <= 0:
                return
            else:
                duration_string = f"{delta.days + 1} D"

        print(f"Last historical query duration string: {duration_string}")

        self.reqHistoricalData(next_req_id, contract, '', duration_string, "1 day", "OPTION_IMPLIED_VOLATILITY", 1, 1, [])



    # App functions
    def get_next_req_id(self, next = True):
        if next:
            self.next_req_id += 1
        return self.next_req_id

    def get_iv_rank(self, ticker, days):
        # values = self.find_in_data(ticker).values()
        # min_value = min(values)
        # max_value = max(values)

        max_date = max(self.find_in_data(ticker).keys())
        max_date = datetime.strptime(max_date, "%Y%m%d")

        volatility_list = []
        for i in range(days):
            new_date = max_date - timedelta(days=i)
            volatility = self.find_in_data(ticker, new_date.strftime("%Y%m%d"), True)
            if volatility is not None:
                volatility_list.append(volatility)
        min_value = min(volatility_list) * 100
        max_value = max(volatility_list) * 100
        iv_today = self.get_iv_today(ticker) * 100
        
        # return (iv_today - min_value) / (max_value - min_value)
        return ((iv_today - min_value) / (max_value - min_value) * 100, iv_today, min_value, max_value)
        
    
    def get_iv_today(self, ticker):
        return self.find_in_data(ticker, today_in_string())
        

    def find_in_data(self, ticker, the_day = None, silent = False):
        try:
            if the_day is None:
                return self.implied_volatility[ticker]
            else:
                return self.implied_volatility[ticker][the_day]
        except KeyError as e:
            if silent:
                return None
            else:
                self.request_historical_data(get_stock_contract(ticker))
                raise GettingInfoError(f"Trying to get historical info for ticker {ticker}")


    def save_data(self):
        with open('data.pk', 'wb') as f:
            pickle.dump(self.implied_volatility, f)

    def load_data(self):
        if os.path.isfile('data.pk'):
            with open('data.pk', 'rb') as f:
                self.implied_volatility = pickle.load(f)
        else:
            self.implied_volatility = {}

    def save_data_json(self):
        with open('data.json', 'w') as f:
            json.dump(self.implied_volatility, f)

    def load_data_json(self):
        if os.path.isfile('data.json'):
            with open('data.json', 'r') as f:
                try:
                    self.implied_volatility = json.load(f)
                except JSONDecodeError:
                    self.implied_volatility = {}
        else:
            self.implied_volatility = {}


    # Main method
    def do_stuff(self):
        # self.reqCurrentTime()

        # contract2 = get_options_contract("SPY", "20170616", 235, "C")
        # self.req_id_to_stock_ticker_map[2] = "SPY"
        # self.reqMktData(2, contract2, "", True, False, [])

        # contract3 = get_stock_contract("SPY")

        # self.req_id_to_stock_ticker_map[3] = "SPY"
        # self.reqHistoricalData(3, contract3, '', "1 Y", "1 day", "OPTION_IMPLIED_VOLATILITY", 1, 1, [])

        while True:
            command = input('--> ')
            if command != "":
                command = command.split(" ")
                stock = command[0]
                duration = 365
                if len(command) == 2:
                    duration = command[1]
                
                try:
                    ivr, iv, iv_min, iv_max = self.get_iv_rank(stock, int(duration))
                    ivr, iv, iv_min, iv_max = format(ivr, '.2f'), format(iv, '.2f'), \
                        format(iv_min, '.2f'), format(iv_max, '.2f')
                    # print(f"IV today is: {iv}")
                    # print(f"IV min is: {iv_min}")
                    # print(f"IV max is: {iv_max}")
                    # print(f"IV rank is: {ivr}")
                    
                    show = format(f"Stock: {stock}", '<18')
                    show += format(f"IV rank: {ivr}", '<19')
                    show += format(f"IV today: {iv}", '<20')
                    show += format(f"IV min: {iv_min}", '<18')
                    show += format(f"IV max: {iv_max}", '<18')
                    print(show)
                except GettingInfoError as e:
                    print(e)
                    print("Try again when available message appears...")


app = TestApp("127.0.0.1", 7496, 0)
# app.connect("127.0.0.1", 4096, clientId=0)
# print("serverVersion:%s connectionTime:%s" % (app.serverVersion(), app.twsConnectionTime()))
app.do_stuff()



#time.sleep(60)
#app.disconnect()
