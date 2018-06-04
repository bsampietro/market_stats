import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread
import logging
import time
from datetime import datetime

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import *
from ibapi.common import *

from lib import util


class IBData(EClient, EWrapper):
    def __init__(self, data_handler):
        EClient.__init__(self, wrapper = self)

        self.data_handler = data_handler

        # variables
        self.next_req_id = 0
        self.req_id_to_stock_ticker_map = {}
        self.req_id_to_requested_historical_data = {}
        self.session_requested_data = set()
        self.api_ready = False

        self.connect("127.0.0.1", 7496, 0)

        self.message_loop = Thread(target = self.run)
        self.message_loop.start()


    def request_historical_data(self, requested_data, ticker):
        # Remember queries in this session
        requested_data_key = f"{requested_data},{ticker}"
        if requested_data_key in self.session_requested_data:
            logging.info(f"{requested_data_key} already requested")
            return
        else:
            self.session_requested_data.add(requested_data_key)

        # Setting query variables
        duration_string = "2 Y"
        
        if requested_data == "IV":
            what_to_show = "OPTION_IMPLIED_VOLATILITY"
        elif requested_data == "HV":
            what_to_show = "HISTORICAL_VOLATILITY"
        elif requested_data == "STOCK":
            what_to_show = "ASK"
        else:
            raise RuntimeError("Unknown requested_data parameter")

        # Adjusting max duration_string query variable
        last = self.data_handler.get_max_stored_date(requested_data, ticker)
        if last is not None:
            delta = datetime.today() - last
            if delta.days <= 0:
                return
            else:
                duration_string = f"{delta.days + 1} D"
        logging.info(f"Last historical query duration string: {duration_string}")
        
        # Class level mappings
        next_req_id = self.get_next_req_id()
        self.req_id_to_stock_ticker_map[next_req_id] = ticker
        self.req_id_to_requested_historical_data[next_req_id] = requested_data

        # Query
        self.reqHistoricalData(next_req_id, util.get_contract(ticker), '', duration_string, "1 day", what_to_show, 1, 1, [])


    def historicalData(self, reqId:TickerId , date:str, open:float, high:float,
                       low:float, close:float, volume:int, barCount:int,
                        WAP:float, hasGaps:int):
        super().historicalData(reqId, date, open, high, low, close, volume, barCount, WAP, hasGaps)

        if self.req_id_to_requested_historical_data[reqId] == "IV":
            self.data_handler.store_iv(self.req_id_to_stock_ticker_map[reqId], date, close)
        elif self.req_id_to_requested_historical_data[reqId] == "HV":
            self.data_handler.store_hv(self.req_id_to_stock_ticker_map[reqId], date, close)
        elif self.req_id_to_requested_historical_data[reqId] == "STOCK":
            self.data_handler.store_stock(self.req_id_to_stock_ticker_map[reqId], date, close)
        else:
            raise RuntimeError("Unknown requested_data parameter")


    def historicalDataEnd(self, reqId:int, start:str, end:str):
        self.req_id_to_stock_ticker_map.pop(reqId, None)
        logging.info(f"Historical data fetched for reqId: {reqId}")



    def request_market_data(self, requested_data, ticker):
        next_req_id = self.get_next_req_id()
        self.req_id_to_stock_ticker_map[next_req_id] = ticker
        self.reqMktData(next_req_id, util.get_contract(ticker), "", True, False, [])


    def tickPrice(self, reqId, tickType, price:float, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        logging.info(f"Snapshot data fetched for reqId: {reqId}")

        if price <= 0:
            return

        if tickType == 2:
            self.data_handler.store_stock(self.req_id_to_stock_ticker_map[reqId], util.today_in_string(), price)


    def tickSnapshotEnd(self, reqId:int):
        super().tickSnapshotEnd(reqId)
        self.req_id_to_stock_ticker_map.pop(reqId, None)


    # Async

    def wait_for_async_request(self):
        for i in range(120):
            if len(self.req_id_to_stock_ticker_map) == 0:
                break
            else:
                time.sleep(1)


    def wait_for_api_ready(self):
        for i in range(120):
            if self.api_ready:
                break
            else:
                time.sleep(1)


    # Private
    
    def get_next_req_id(self, next = True):
        if next:
            self.next_req_id += 1
        return self.next_req_id


    def reset_session_requested_data(self):
        self.session_requested_data = set()


    def error(self, reqId:TickerId, errorCode:int, errorString:str):
        super().error(reqId, errorCode, errorString)
        
        self.req_id_to_stock_ticker_map.pop(reqId, None)
        logging.info(f"Bruno says: Error logged with reqId: {reqId}")

    
    # Overwritten

    def keyboardInterrupt(self):
        self.disconnect()


    def nextValidId(self, orderId:int):
        super().nextValidId(orderId)
        logging.info(f"Bruno says: App ready with orderId: {orderId}")
        self.api_ready = True