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
        # implied_volatility and historical_volatility variables are loaded now...

        self.remote = None
        if connect:
            self.remote = TestApp(self)
        

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
        with open('data_implied_volatility.json', 'w') as f:
            json.dump(self.implied_volatility, f)

        with open('data_historical_volatility.json', 'w') as f:
            json.dump(self.historical_volatility, f)

    def load_data_json(self):
        try:
            with open('data_implied_volatility.json', 'r') as f:
                self.implied_volatility = json.load(f)
        except (JSONDecodeError, FileNotFoundError) as e:
            self.implied_volatility = {}

        try:
            with open('data_historical_volatility.json', 'r') as f:
                self.historical_volatility = json.load(f)
        except (JSONDecodeError, FileNotFoundError) as e:
            self.historical_volatility = {}


    def connected(self):
        return self.remote is not None


    def load(self):
        self.load_data_json()

    def save(self):
        self.save_data_json()

    def disconnect(self):
        self.remote.disconnect()

    def stop(self):
        if self.connected():
            self.save()
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

    def store_hv(self, ticker, date, value):
        if not ticker in self.historical_volatility:
            self.historical_volatility[ticker] = {}
        self.historical_volatility[ticker][date] = value


    def request_historical_data(self, requested_data, ticker):
        self.remote.request_historical_data(requested_data, ticker)
    

    def find_in_data(self, requested_data, ticker, the_day = None, silent = False):
        data = None
        if requested_data == "IV":
            data = self.implied_volatility
        else:
            data = self.historical_volatility

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
                self.request_historical_data(requested_data, ticker)
                raise GettingInfoError(f"Getting {requested_data} data for ticker {ticker}...")
            else:
                raise GettingInfoError("Unavailable info and remote not connected, please restart again with connect parameter")


    def delete_at(self, date):
        for key in self.implied_volatility.keys():
            self.implied_volatility[key].pop(date, None)
        for key in self.historical_volatility.keys():
            self.historical_volatility[key].pop(date, None)

    def wait_for_async_request(self):
        if self.connected():
            self.remote.wait_for_async_request()