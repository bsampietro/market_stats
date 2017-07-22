import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread
import logging
import time

from ibapi import wrapper
from ibapi.client import EClient
from ibapi.contract import *
from ibapi.common import *

from util import *


class TestWrapper(wrapper.EWrapper):
    def __init__(self):
        wrapper.EWrapper.__init__(self)

class TestClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

    def keyboardInterrupt(self):
        self.disconnect()



class TestApp(TestWrapper, TestClient):
    def __init__(self, data_handler):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.data_handler = data_handler

        # variables
        self.next_req_id = 0
        self.req_id_to_stock_ticker_map = {}
        self.req_id_to_requested_historical_data = {}

        self.connect("127.0.0.1", 7496, 0)

        # Try without calling self.run() ??
        thread = Thread(target = self.run)
        thread.start()
        # self.run()


    def historicalData(self, reqId:TickerId , date:str, open:float, high:float,
                       low:float, close:float, volume:int, barCount:int,
                        WAP:float, hasGaps:int):
        super().historicalData(reqId, date, open, high, low, close, volume, barCount, WAP, hasGaps)
        
        if self.req_id_to_requested_historical_data[reqId] == "IV":
            self.data_handler.store_iv(self.req_id_to_stock_ticker_map[reqId], date, close)
        else: # HV
            self.data_handler.store_hv(self.req_id_to_stock_ticker_map[reqId], date, close)
    

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        self.req_id_to_stock_ticker_map.pop(reqId, None)
        logging.getLogger().info(f"Historical data fetched for reqId: {reqId}")


    # Client method wrappers
    def request_historical_data(self, requested_data, ticker):
        duration_string = "1 Y"
        last = self.data_handler.get_max_stored_date(requested_data, ticker)
        if last is not None:
            delta = datetime.today() - last

            if delta.days <= 0:
                return
            else:
                duration_string = f"{delta.days + 1} D"
        logging.getLogger().info(f"Last historical query duration string: {duration_string}")
        
        next_req_id = self.get_next_req_id()
        self.req_id_to_stock_ticker_map[next_req_id] = ticker
        self.req_id_to_requested_historical_data[next_req_id] = requested_data

        if requested_data == "IV":
            what_to_show = "OPTION_IMPLIED_VOLATILITY"
        else: # HV
            what_to_show = "HISTORICAL_VOLATILITY"

        self.reqHistoricalData(next_req_id, get_stock_contract(ticker), '', duration_string, "1 day", what_to_show, 1, 1, [])

        # next_req_id = self.get_next_req_id()
        # self.req_id_to_stock_ticker_map[next_req_id] = ticker
        # self.reqMktData(next_req_id, get_stock_contract(ticker), "", True, False, [])

    # App functions
    def get_next_req_id(self, next = True):
        if next:
            self.next_req_id += 1
        return self.next_req_id


    def wait_for_async_request(self):
        for i in range(120):
            if len(self.req_id_to_stock_ticker_map) == 0:
                break
            else:
                time.sleep(1)
    
    # def get_days_from_last_query(self, ticker):
    #     pass

    # Wrapper
    # def tickSnapshotEnd(self, reqId: int):
    #     # super().tickSnapshotEnd(reqId)
    #     # print("tickSnapshotEnd - reqId:", reqId)

    # def connectAck(self):
    #     """ callback signifying completion of successful connection """
    #     # self.logAnswer(current_fn_name(), vars())
    #     super().connectAck()

    
    # def nextValidId(self, orderId:int):
    #     """ Receives next valid order id."""
    #     super().nextValidId(orderId)
    #     # self.next_req_id = orderId

