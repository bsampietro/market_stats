import pickle
import json
from json.decoder import JSONDecodeError
import os.path

from util import *
from access import *
from errors import *

class DataHandler:
    def __init__(self, connect:bool):
        
        self.load()
        # implied_volatility variable is loaded now...

        self.remote = None
        if connect:
            self.remote = TestApp(self.implied_volatility)
        

    def save_data(self):
        with open('data.pk', 'wb') as f:
            pickle.dump(self.implied_volatility, f)

    def load_data(self):
        if os.path.isfile('data.pk'):
            with open('data.pk', 'rb') as f:
                self.implied_volatility = pickle.load(f)
        else:
            self.implied_volatility = {}

    def save_data_json(self):
        with open('data.json', 'w') as f:
            json.dump(self.implied_volatility, f)

    def load_data_json(self):
        if os.path.isfile('data.json'):
            with open('data.json', 'r') as f:
                try:
                    self.implied_volatility = json.load(f)
                except JSONDecodeError:
                    self.implied_volatility = {}
        else:
            self.implied_volatility = {}

    def connected(self):
        return self.remote is not None

    def disconnect(self):
        if self.connected():
            self.remote.disconnect()

    def load(self):
        self.load_data_json()

    def save(self):
        self.save_data_json()
        
    def find_in_data(self, ticker, the_day = None, silent = False):
        try:
            if the_day is None:
                return self.implied_volatility[ticker]
            else:
                return self.implied_volatility[ticker][the_day]
        except KeyError as e:
            if silent:
                return None
            elif self.connected():
                self.remote.request_historical_data(get_stock_contract(ticker))
                raise GettingInfoError(f"Getting historical info for ticker {ticker}")
            else:
                raise GettingInfoError("Remote not connected, please restart again with connect parameter")
