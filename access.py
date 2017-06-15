from ibapi import wrapper
from ibapi.client import EClient
from ibapi.contract import *
from ibapi.common import *


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
    def __init__(self, data):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        # logging.getLogger().setLevel(logging.INFO)
        ## logging.basicConfig(level=logging.INFO)

        self.implied_volatility = data

        # variables
        self.next_req_id = 0
        self.req_id_to_stock_ticker_map = {}

        self.connect("127.0.0.1", 7496, 0)

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

    


