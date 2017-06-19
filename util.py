import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')
from ibapi.contract import *

from datetime import datetime, timedelta

def get_options_contract(symbol, date_str, strike, right):
    contract = Contract()
    contract.secType = "OPT"
    contract.exchange = "SMART"
    # contract.primaryExch = "ISLAND"
    contract.currency = "USD"
    contract.multiplier = "100"
    contract.symbol = symbol
    contract.lastTradeDateOrContractMonth = date_str
    contract.strike = strike
    contract.right = right
    return contract

def get_stock_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = "SMART"
    # Specify the Primary Exchange attribute to avoid contract ambiguity 
    contract.primaryExch = "ISLAND"
    return contract

def today_in_string():
    return datetime.today().strftime("%Y%m%d")

def read_stock_list(path):
    stock_list = []
    with open(path) as stocks:
        for stock in stocks:
            stock = stock.strip()
            if stock != '' and stock[0] != '#':
                stock_list.append(stock)
    return stock_list

    # stock_list = read_stock_list("/home/bruno/source/python/IB/stock_list.txt")

    # # use stock list here ...

    # print(str(stock_list))
    # for stock in stock_list:
    #     print(stock)

def get_option_expiration(date):
    day = 21 - (calendar.weekday(date.year, date.month, 1) + 2) % 7
    return datetime(date.year, date.month, day)
# print option_expiration(datetime.today())