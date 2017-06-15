import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')

from threading import Thread

import time
import logging
import pickle
import os.path


import json
from json.decoder import JSONDecodeError

from datetime import datetime, timedelta
import calendar


from util import *
from access import *


class GettingInfoError(Exception):
    pass

    
class BProgram:

    def __init__(self, connect:bool):
        
        # self.load_data()
        self.load_data_json()
        # implied_volatility variable is loaded now...

        self.remote = None
        if connect:
            self.remote = TestApp(self.implied_volatility)
        
        # Executing main code
        self.do_stuff()

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


    def get_iv_rank(self, ticker, days):
        max_date = max(self.find_in_data(ticker).keys())
        max_date = datetime.strptime(max_date, "%Y%m%d")

        volatility_list = []
        for i in range(days):
            new_date = max_date - timedelta(days = i)
            volatility = self.find_in_data(ticker, new_date.strftime("%Y%m%d"), True)
            if volatility is not None:
                volatility_list.append(volatility)
        min_value = min(volatility_list) * 100
        max_value = max(volatility_list) * 100
        iv_today = self.get_iv_today(ticker) * 100
        ivr_today = (iv_today - min_value) / (max_value - min_value) * 100

        latest_ivrs = []
        today = datetime.today()
        for i in range(10):
            volatility = self.find_in_data(ticker, (today - timedelta(days = i)).strftime("%Y%m%d"), True)
            if volatility is not None:
                latest_ivrs.append((volatility - min_value) / (max_value - min_value) * 100)
        
        return (ivr_today, iv_today, min_value, max_value)
        
    
    def get_iv_today(self, ticker, the_day = None):
        if the_day is None:
            the_day = today_in_string()
        return self.find_in_data(ticker, the_day)
        

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

    def do_stuff(self):
        while True:
            command = input('--> ')
            if command != "":
                command = command.split(" ")
                stock = command[0]
                duration = 365
                if len(command) == 2:
                    duration = command[1]

                if stock == "exit":
                    if self.connected():
                        self.remote.disconnect()
                    break
                stock = stock.upper()
                
                try:
                    ivr, iv, iv_min, iv_max = self.get_iv_rank(stock, int(duration))
                    ivr, iv, iv_min, iv_max = format(ivr, '.2f'), format(iv, '.2f'), \
                        format(iv_min, '.2f'), format(iv_max, '.2f')
                    
                    show = format(f"Stock: {stock}", '<18')
                    show += format(f"IV rank: {ivr}", '<19')
                    show += format(f"IV today: {iv}", '<20')
                    show += format(f"IV min: {iv_min}", '<18')
                    show += format(f"IV max: {iv_max}", '<18')
                    print(show)
                except GettingInfoError as e:
                    print(e)
                    print("Try again when available message appears...")


if __name__ == "__main__":
   BProgram(sys.argv[0] == "connect")



#time.sleep(60)
#app.disconnect()
