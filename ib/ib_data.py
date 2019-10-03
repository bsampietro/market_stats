import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread
import logging
import time
from datetime import datetime

from ibapi.wrapper import EWrapper
from ibapi.client import EClient

from lib import util, core
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

        if requested_data == "IV":
            what_to_show = "OPTION_IMPLIED_VOLATILITY"
        elif requested_data == "HV":
            what_to_show = "HISTORICAL_VOLATILITY"
        elif requested_data == "STOCK":
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
                                ticker=ticker, requested_data=requested_data)

        # Query
        self.reqHistoricalData(next_req_id, util.get_contract(ticker), '',
                            duration_string, "1 day", what_to_show, 1, 1, [])
        time.sleep(1)

    def historicalData(self, reqId, date:str, open:float, high:float,
                       low:float, close:float, volume:int, barCount:int,
                        WAP:float, hasGaps:int):
        super().historicalData(reqId, date, open, high, low, close,
                                volume, barCount, WAP, hasGaps)

        if self.calling_info[reqId].requested_data == "IV":
            gcnv.data_handler.store_iv(
                self.calling_info[reqId].ticker, date, close)
        elif self.calling_info[reqId].requested_data == "HV":
            gcnv.data_handler.store_hv(
                self.calling_info[reqId].ticker, date, close)
        elif self.calling_info[reqId].requested_data == "STOCK":
            gcnv.data_handler.store_stock(
                self.calling_info[reqId].ticker, date, close)
        else:
            raise RuntimeError("Unknown requested_data parameter")

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

        calling_info = self.calling_info[reqId]
        if calling_info.method != 'request_market_data':
            return
        if price <= 0:
            return
        if tickType != 4:
            return
        gcnv.data_handler.store_stock(calling_info.ticker,
                                        util.today_in_string(), price)

    def tickSnapshotEnd(self, reqId:int):
        super().tickSnapshotEnd(reqId)
        self.calling_info.pop(reqId, None)

    
    # bring specific options details
    def request_options_contract(self, ticker, price, right, expiration_date):
        next_req_id = self.get_next_req_id()
        self.calling_info[next_req_id] = core.Struct(ticker=ticker)
        
        contract = util.get_options_contract(ticker)
        contract.lastTradeDateOrContractMonth = expiration_date
        contract.strike = price
        contract.right = right
        
        self.reqMktData(next_req_id, contract, "", True, False, [])
        time.sleep(1)

    def tickOptionComputation(self, reqId, tickType, impliedVol, delta,
                optPrice, pvDividend, gamma, vega, theta, undPrice):
        if tickType != 12: # last price
            return
        ticker = self.calling_info[reqId].ticker
        gcnv.options[ticker].append({'delta': delta, 'price': optPrice})

    def error(self, reqId, errorCode:int, errorString:str):
        super().error(reqId, errorCode, errorString)
        logging.info(f"Bruno says: Error logged with reqId: {reqId}")
        
        self.calling_info.pop(reqId, None)

    # Async

    def wait_for_async_request(self):
        for i in range(300):
            if len(self.calling_info) == 0:
                break
            else:
                assert i != 299, "Timeout!"
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

    # Overwritten

    def keyboardInterrupt(self):
        self.disconnect()

    def nextValidId(self, orderId:int):
        super().nextValidId(orderId)
        logging.info(f"Bruno says: App ready with orderId: {orderId}")
        self.api_ready = True