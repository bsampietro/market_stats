from ib.ib_data import IBData

# Instantiate this class in test mode from main.py
class IBDataTest(IBData):
    def __init__(self):
        IBData.__init__(self)
        self.nextValidId(0)

    def connect(self, host, port, app_number):
        pass # overwrite method for not doing anything

    def reqMktData(self, next_req_id, contract, some1, some2, some3, some4):
        pass

    def run(self):
        pass

    # Here methods that need to be tested

    def request_options_contract(self, ticker, strike, right, expiration_date):
        super().request_options_contract(ticker, strike, right, expiration_date)
        reqId = list(self.calling_info.keys())[0]
        self.tickOptionComputation(
            reqId, 11, None, 0.5, 12.02, None, None, None, None, None)
        self.tickSnapshotEnd(reqId)