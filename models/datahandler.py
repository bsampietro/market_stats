import json
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta

from lib import util
from lib.errors import *
from ib.ib_data import IBData

import gcnv

class DataHandler:
    def __init__(self, connect:bool):
        
        # Path variables
        self.implied_volatility_data_file_path = \
                f"{gcnv.APP_PATH}/data/data_implied_volatility.json"
        self.historical_volatility_data_file_path = \
                f"{gcnv.APP_PATH}/data/data_historical_volatility.json"
        self.stock_data_file_path = \
                f"{gcnv.APP_PATH}/data/stock.json"

        self.load() # Load data variables

        self.remote = None
        if connect:
            self.remote = IBData(self)

        # smart saving variables
        self.modified_iv = False
        self.modified_hv = False
        self.modified_stock = False

    def save_data_json(self):
        if self.modified_iv:
            with open(self.implied_volatility_data_file_path, "w") as f:
                json.dump(self.implied_volatility, f)

        if self.modified_hv:
            with open(self.historical_volatility_data_file_path, "w") as f:
                json.dump(self.historical_volatility, f)

        if self.modified_stock:
            with open(self.stock_data_file_path, "w") as f:
                json.dump(self.stock, f)

    def load_data_json(self):
        with open(self.implied_volatility_data_file_path, "r") as f:
            self.implied_volatility = json.load(f)

        with open(self.historical_volatility_data_file_path, "r") as f:
            self.historical_volatility = json.load(f)

        with open(self.stock_data_file_path, "r") as f:
            self.stock = json.load(f)

    def connected(self):
        return self.remote is not None

    def load(self):
        self.load_data_json()

    def save(self):
        self.save_data_json()

    def disconnect(self):
        if self.connected():
            self.remote.disconnect()

    def get_max_stored_date(self, requested_data, ticker):
        data = self.find_in_data(requested_data, ticker, None, silent = True)
        if data is None:
            return None
        else:
            return datetime.strptime(max(data.keys()), "%Y%m%d")

    def store_iv(self, ticker, date, value):
        if not ticker in self.implied_volatility:
            self.implied_volatility[ticker] = {}
        self.implied_volatility[ticker][date] = value
        self.modified_iv = True

    def store_hv(self, ticker, date, value):
        if not ticker in self.historical_volatility:
            self.historical_volatility[ticker] = {}
        self.historical_volatility[ticker][date] = value
        self.modified_hv = True

    def store_stock(self, ticker, date, value):
        if not ticker in self.stock:
            self.stock[ticker] = {}
        self.stock[ticker][date] = value
        self.modified_stock = True

    def request_historical_data(self, requested_data, ticker):
        self.remote.request_historical_data(requested_data, ticker)

    def request_market_data(self, requested_data, ticker):
        self.remote.request_market_data(requested_data, ticker)
    
    def find_in_data(self, requested_data, ticker, date, silent):
        data = None
        if requested_data == "IV":
            data = self.implied_volatility
        elif requested_data == "HV":
            data = self.historical_volatility
        elif requested_data == "STOCK":
            data = self.stock
        else:
            raise RuntimeError("Unknown requested_data parameter")

        try:
            if date is None:
                return data[ticker]
            else:
                date = util.date_in_string(date)
                return data[ticker][date]
        except KeyError as e:
            if silent:
                return None
            elif self.connected():
                raise GettingInfoError(
                    f"{ticker} not stored, getting it in background...")
            else:
                raise GettingInfoError(
                    f"{ticker} info not available and remote not connected")

    def delete_at(self, date):
        for key in self.implied_volatility.keys():
            self.implied_volatility[key].pop(date, None)
        self.modified_iv = True

        for key in self.historical_volatility.keys():
            self.historical_volatility[key].pop(date, None)
        self.modified_hv = True

        for key in self.stock.keys():
            self.stock[key].pop(date, None)
        self.modified_stock = True

        if self.connected():
            self.remote.reset_session_requested_data()

    def delete_back(self, back_days):
        today = datetime.today()
        for i in range(back_days):
            delete_day = util.date_in_string(today - timedelta(days = i))
            self.delete_at(delete_day)

    def delete_ticker(self, ticker):
        self.implied_volatility.pop(ticker, None)
        self.modified_iv = True

        self.historical_volatility.pop(ticker, None)
        self.modified_hv = True

        self.stock.pop(ticker, None)
        self.modified_stock = True

        if self.connected():
            self.remote.reset_session_requested_data()

    # Async

    def wait_for_async_request(self):
        if self.connected():
            self.remote.wait_for_async_request()

    def wait_for_api_ready(self):
        if self.connected():
            self.remote.wait_for_api_ready()

    # Data

    # Last list element is the most recent value, achieved by data.reverse() statement
    def list_data(self, wtb, back_days):
        today = datetime.today()
        missing_dates = []
        data = []
        for i in range(back_days):
            older_date = today - timedelta(days = i)
            close = []
            for requested_data, ticker in wtb:
                close.append(
                        self.find_in_data(requested_data, ticker,
                                        older_date.strftime("%Y%m%d"), True))
            if all(close_i is not None for close_i in close):
                data.append(close)
            else:
                if older_date.weekday() not in (5,6): # not a weekend and still not stored
                    missing_dates.append(older_date.strftime("%Y%m%d"))
        if back_days < 365 * 2:
            cdl = round(back_days * (5 / 7)) # correct_data_length
            if len(data) < cdl - 30 or len(data) > cdl + 15:
                gcnv.messages.append(
                    f"Incorrect data length for {wtb}. "
                    f"Should return {cdl} but returning {len(data)}. "
                    f"Missing dates: {missing_dates}")
        data.reverse()
        data = list(zip(*data))
        return data