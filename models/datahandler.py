import pickle
import json
from json.decoder import JSONDecodeError
import os.path

from lib.util import *
from lib.errors import *
from ib_data import *


class DataHandler:
    def __init__(self, connect:bool):
        
        self.load()
        # implied_volatility and historical_volatility variables are loaded now...

        self.remote = None
        if connect:
            self.remote = IBData(self)

        # smart saving variables
        self.modified_iv = False
        self.modified_hv = False
        self.modified_stock = False


    # def save_data(self):
    #     with open('data.pk', 'wb') as f:
    #         pickle.dump(self.implied_volatility, f)

    # def load_data(self):
    #     if os.path.isfile('data.pk'):
    #         with open('data.pk', 'rb') as f:
    #             self.implied_volatility = pickle.load(f)
    #     else:
    #         self.implied_volatility = {}

    def save_data_json(self):
        if self.modified_iv:
            with open('./data/data_implied_volatility.json', 'w') as f:
                json.dump(self.implied_volatility, f)

        if self.modified_hv:
            with open('./data/data_historical_volatility.json', 'w') as f:
                json.dump(self.historical_volatility, f)

        if self.modified_stock:
            with open('./data/stock.json', 'w') as f:
                json.dump(self.stock, f)

    def load_data_json(self):
        try:
            with open('./data/data_implied_volatility.json', 'r') as f:
                self.implied_volatility = json.load(f)
        except (JSONDecodeError, FileNotFoundError) as e:
            self.implied_volatility = {}

        try:
            with open('./data/data_historical_volatility.json', 'r') as f:
                self.historical_volatility = json.load(f)
        except (JSONDecodeError, FileNotFoundError) as e:
            self.historical_volatility = {}

        try:
            with open('./data/stock.json', 'r') as f:
                self.stock = json.load(f)
        except (JSONDecodeError, FileNotFoundError) as e:
            self.stock = {}


    def connected(self):
        return self.remote is not None


    def load(self):
        self.load_data_json()

    def save(self):
        self.save_data_json()

    def disconnect(self):
        if self.connected():
            self.remote.disconnect()

    def stop(self):
        self.save()
        if self.connected():
            self.disconnect()
        

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
    

    def find_in_data(self, requested_data, ticker, the_day = None, silent = False):
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
            if the_day is None:
                return data[ticker]
            else:
                the_day = date_in_string(the_day)
                return data[ticker][the_day]
        except KeyError as e:
            if silent:
                return None
            elif self.connected():
                # self.request_historical_data(requested_data, ticker) # Now getting it before hand (bring_if_connected method)
                raise GettingInfoError(f"{ticker} not stored, getting it in background...")
            else:
                raise GettingInfoError(f"{ticker} info not available and remote not connected")


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
            delete_day = date_in_string(today - timedelta(days = i))
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


    def wait_for_async_request(self):
        if self.connected():
            self.remote.wait_for_async_request()