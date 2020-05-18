# Need to set PYTHONPATH environment variable with path to ibapi library

from threading import Thread
import logging
import time
from datetime import datetime

from ibapi.wrapper import EWrapper
from ibapi.client import EClient

from lib import util, core
from lib.errors import *
import gcnv

class IBData(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, wrapper = self)
        
        # variables
        self.next_req_id = 0
        self.calling_info = {}
        self.session_requested_data = set()
        self.api_ready = False

        self.connect("127.0.0.1", 7496, 0)

        self.message_loop = Thread(target = self.run)
        self.message_loop.start()

    def request_historical_data(self, requested_data, ticker):
        # Remember queries in this session
        requested_data_key = f"{requested_data},{ticker}"
        if requested_data_key in self.session_requested_data:
            gcnv.messages.append(f"{requested_data_key} already requested")
            return
        else:
            self.session_requested_data.add(requested_data_key)

        if requested_data == "iv":
            what_to_show = "OPTION_IMPLIED_VOLATILITY"
        elif requested_data == "hv":
            what_to_show = "HISTORICAL_VOLATILITY"
        elif requested_data == "stock":
            what_to_show = "ASK"
        else:
            raise RuntimeError("Unknown requested_data parameter")

        # Adjusting max duration_string query variable
        duration_string = "2 Y"
        if util.contract_type(ticker) == "FUT":
            duration_string = "3 M"

        last = gcnv.data_handler.get_max_stored_date(requested_data, ticker)
        if last is not None:
            delta = datetime.today() - last
            if delta.days <= 0:
                return
            elif delta.days >= 365:
                gcnv.data_handler.delete_ticker(ticker)
            else:
                duration_string = f"{delta.days + 1} D"

        logging.info(f"Last historical query duration string: {duration_string}")
        
        # Class level mappings
        next_req_id = self.get_next_req_id()
        self.calling_info[next_req_id] = core.Struct(
                                            ticker=ticker,
                                            requested_data=requested_data)

        # Query
        self.reqHistoricalData(next_req_id, util.get_contract(ticker), '',
                            duration_string, "1 day", what_to_show, 1, 1, False, [])

    def historicalData(self, reqId, bar_data):
        super().historicalData(reqId, bar_data)

        gcnv.data_handler.store_history(
                self.calling_info[reqId].requested_data,
                self.calling_info[reqId].ticker,
                bar_data.date,
                bar_data.close
            )

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        self.calling_info.pop(reqId, None)
        logging.info(f"Historical data fetched for reqId: {reqId}")

    ## Commented while developing the options part
    def request_market_data(self, requested_data, ticker):
        next_req_id = self.get_next_req_id()
        self.calling_info[next_req_id] = core.Struct(
                                ticker=ticker,
                                requested_data=requested_data,
                                method='request_market_data')
        self.reqMktData(next_req_id, util.get_contract(ticker), "", True, False, [])

    def tickPrice(self, reqId, tickType, price:float, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        logging.info(f"Snapshot data fetched for reqId: {reqId}")

        if price <= 0:
            return
        if tickType != 4:
            return

        calling_info = self.calling_info[reqId]
        if calling_info.method == 'request_market_data':
            gcnv.data_handler.store_history('stock',
                                            calling_info.ticker,
                                            util.today_in_string(),
                                            price)

    def tickSnapshotEnd(self, reqId:int):
        super().tickSnapshotEnd(reqId)
        self.calling_info.pop(reqId, None)

    # bring specific options details
    def request_options_contract(self, ticker, strike, right, expiration_date):
        next_req_id = self.get_next_req_id()
        self.calling_info[next_req_id] = core.Struct(
                ticker=ticker,
                strike=strike,
                right=right,
                method='request_options_contract')
        
        contract = util.get_options_contract(ticker)
        contract.lastTradeDateOrContractMonth = expiration_date
        contract.strike = strike
        contract.right = right
        
        self.reqMktData(next_req_id, contract, "", True, False, [])

    def tickOptionComputation(self, reqId, tickType, impliedVol, delta,
                optPrice, pvDividend, gamma, vega, theta, undPrice):
        super().tickOptionComputation(reqId, tickType, impliedVol, delta,
                optPrice, pvDividend, gamma, vega, theta, undPrice)
        if tickType != 11: # ask price
            return

        calling_info = self.calling_info[reqId]
        if calling_info.method == 'request_options_contract':
            gcnv.options[calling_info.ticker].append({
                                        'delta': delta,
                                        'price': optPrice,
                                        'strike': calling_info.strike, 
                                        'right': calling_info.right})

    def error(self, reqId, errorCode:int, errorString:str):
        super().error(reqId, errorCode, errorString)
        logging.info(f"Bruno says: Error logged with reqId: {reqId}")
        
        self.calling_info.pop(reqId, None)

    # Async

    def wait_for_async_request(self):
        for i in range(20):
            if len(self.calling_info) == 0:
                return
            time.sleep(1)
        self.calling_info.clear()
        raise GettingInfoError("Timeout while getting data")

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

    # Overwritten

    def keyboardInterrupt(self):
        self.disconnect()

    def nextValidId(self, orderId:int):
        super().nextValidId(orderId)
        logging.info(f"Bruno says: App ready with orderId: {orderId}")
        self.api_ready = True