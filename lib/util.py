import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')
from ibapi.contract import *

from datetime import datetime, timedelta
import statistics

def get_basic_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.currency = "USD"
    contract.exchange = "SMART"
    if symbol in ("GLD", "GDX", "GDXJ"):
        contract.exchange = "ARCA"
    elif symbol in ("MSFT", "INTC", "CSCO"):
        contract.exchange = "ISLAND"
        # contract.primaryExchange = "ISLAND"
    return contract

def get_options_contract(symbol, date_str, strike, right):
    contract = get_basic_contract(symbol)
    contract.secType = "OPT"
    contract.multiplier = "100"
    contract.lastTradeDateOrContractMonth = date_str
    contract.strike = strike
    contract.right = right
    return contract

def get_stock_contract(symbol):
    contract = get_basic_contract(symbol)
    contract.secType = "STK"
    return contract

def get_futures_contract(symbol, lastTradeDate):
    contract = get_basic_contract(symbol)
    contract.secType = "FUT"
    contract.lastTradeDateOrContractMonth = lastTradeDate # "201612"
    return contract

def get_special_contract(symbol, lastTradeDate = None):
    contract = None
    if symbol == "ES":
        contract = get_futures_contract(symbol, lastTradeDate)
        contract.exchange = "GLOBEX"
    else:
        contract = get_stock_contract(symbol)
    return contract

def today_in_string():
    return datetime.today().strftime("%Y%m%d")

def date_in_string(date):
    if type(date) is str:
        return date
    elif type(date) is datetime:
        return date.strftime("%Y%m%d")
    else:
        raise RuntimeError("Bruno: the_day argument is of wrong type")

def read_symbol_list(path):
    symbol_list = []
    with open(path) as symbols:
        for symbol in symbols:
            symbol = symbol.strip()
            if symbol != '' and symbol[0] != '#':
                symbol_list.append(symbol)
    return symbol_list

def covariance(data1, data2):
    if len(data1) != len(data2):
        raise RuntimeError("Covariance lists should have the same lenghts")

    data1_mean = statistics.mean(data1)
    data2_mean = statistics.mean(data2)

    sum = 0
    for i in range(len(data1)):
        sum += ((data1[i] - data1_mean) * (data2[i] - data2_mean))

    return sum / (len(data1) - 1)

def get_option_expiration(date):
    day = 21 - (calendar.weekday(date.year, date.month, 1) + 2) % 7
    return datetime(date.year, date.month, day)

