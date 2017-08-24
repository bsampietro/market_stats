import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread
import logging
# import time

from datetime import datetime, date
import time

from ibapi import wrapper
from ibapi.client import EClient
from ibapi.contract import *
from ibapi.common import *

from util import *


class IBHedgeWrapper(wrapper.EWrapper):
    def __init__(self):
        wrapper.EWrapper.__init__(self)

class IBHedgeClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)



class IBHedge(IBHedgeWrapper, IBHedgeClient):
    def __init__(self):
        IBHedgeWrapper.__init__(self)
        IBHedgeClient.__init__(self, wrapper=self)

        # variables
        self.next_req_id = 0
        self.req_id_to_stock_ticker_map = {}
        self.req_id_to_requested_historical_data = {}

        self.connect("127.0.0.1", 7496, 1)

        # Try without calling self.run() ??
        thread = Thread(target = self.run)
        thread.start()
        # self.run()

    def keyboardInterrupt(self):
        self.terminateEverything()

    def terminateEverything(self):
        print("Terminating everything...")
        
        for req_id in self.req_id_to_stock_ticker_map.keys():
            self.cancelMktData(req_id)
        self.disconnect()

        print("Finished terminating.")


    def request_market_data(self, ticker):
        next_req_id = self.get_next_req_id()
        self.req_id_to_stock_ticker_map[next_req_id] = ticker
        self.reqMktData(next_req_id, get_stock_contract(ticker), "", False, False, [])

    def tickPrice(self, reqId, tickType, price:float, attrib):
        """Market data tick price callback. Handles all price related ticks."""

        super().tickPrice(reqId, tickType, price, attrib)

        if tickType == 2:
            print(f"{int(time.time())} : {self.req_id_to_stock_ticker_map[reqId]} - {price}")


    # App functions
    def get_next_req_id(self, next = True):
        if next:
            self.next_req_id += 1
        return self.next_req_id

    
    # def nextValidId(self, orderId:int):
    #     """ Receives next valid order id."""
    #     super().nextValidId(orderId)
    #     # self.next_req_id = orderId

