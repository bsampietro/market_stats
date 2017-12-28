import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread
import logging

from datetime import datetime, date
import time

from ibapi import wrapper
from ibapi.client import EClient
from ibapi.contract import *
from ibapi.common import *

from lib import util


class IBHedgeWrapper(wrapper.EWrapper):
    def __init__(self):
        wrapper.EWrapper.__init__(self)

class IBHedgeClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)



class IBHedge(IBHedgeWrapper, IBHedgeClient):
    # LIMIT = -1.00
    # RANGE = 14400 # 4 hours in seconds
    LIMIT = -0.01
    RANGE = 20

    def __init__(self, test_mode=False):
        IBHedgeWrapper.__init__(self)
        IBHedgeClient.__init__(self, wrapper=self)

        # general variables
        self.next_req_id = 0
        self.req_id_to_stock_ticker_map = {}
        self.req_id_to_requested_historical_data = {}

        # price variables
        self.initial_price = None
        self.time_price = {}

        # state variables
        self.test_mode = test_mode

        # tws variables
        self.next_order_id = None


        self.connect("127.0.0.1", 7496, 1)

        # Try without calling self.run() ??
        thread = Thread(target = self.run)
        thread.start()
        # self.run()


    def keyboardInterrupt(self):
        self.clear_all()


    def clear_all(self):
        print("Clearing all...")
        
        for req_id in self.req_id_to_stock_ticker_map.keys():
            self.cancelMktData(req_id)
        self.disconnect()

        print("Finished clearing.")


    def start_monitoring(self, ticker, last_trade_date = None):
        self.request_market_data(ticker, last_trade_date)


    def request_market_data(self, ticker, last_trade_date = None):
        next_req_id = self.get_next_req_id()
        self.req_id_to_stock_ticker_map[next_req_id] = ticker
        self.reqMktData(next_req_id, util.get_special_contract(ticker, last_trade_date), "", False, False, [])


    def tickPrice(self, reqId, tickType, price:float, attrib):
        super().tickPrice(reqId, tickType, price, attrib)

        if price <= 0:
            print(f"Returned 0 or under 0 price: '{price}', for ticker {self.req_id_to_stock_ticker_map[reqId]}")
            return

        if tickType == 2:
            now = int(time.time())
            if self.initial_price is None:
                self.initial_price = price
            self.time_price[now] = price

            # print(f"{now} : {self.req_id_to_stock_ticker_map[reqId]} - {price}")

            compared_to_when = now - IBHedge.RANGE
            compared_to_price = None
            for i in range(120):
                if compared_to_when in self.time_price and compared_to_when <= now:
                    compared_to_price = self.time_price[compared_to_when]
                    break
                compared_to_when += 1
            if compared_to_price is None:
                compared_to_price = self.initial_price

            percentage_change = (price / compared_to_price - 1) * 100

            print(f"{now} : {self.req_id_to_stock_ticker_map[reqId]} | {format(price, '.2f')} | {format(percentage_change, '.5f')} %")
            print(f"Compared to when: {compared_to_when}")
            print(f"Compared to price: {compared_to_price}")
            if percentage_change < IBHedge.LIMIT:
                print("Do something!") # buy put and maybe try to sell it ?!

            print("")


    def nextValidId(self, orderId:int):
        super().nextValidId(orderId)
        self.next_order_id = orderId


    # App functions
    def get_next_req_id(self, next = True):
        if next:
            self.next_req_id += 1
        return self.next_req_id


    def is_ready(self):
        return self.next_order_id is not None


    def wait_for_readiness(self):
        for i in range(120):
            if self.is_ready():
                break
            else:
                time.sleep(1)
        if self.is_ready():
            print("IB Ready")
        else:
            # raise exception ?
            print("IB was not reported ready after 120 seconds")




    # Overload methods for test mode
    def reqMktData(self, reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions):
        if self.test_mode:
            # manually call tickPrice
            pass
        else:
            super().reqMktData(reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)
