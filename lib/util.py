# Need to set PYTHONPATH environment variable with path to ibapi library

from datetime import datetime, timedelta
import math
import statistics

from ibapi.contract import *

from lib.errors import *

def get_contract(symbol):
    ctype = contract_type(symbol)
    if ctype == "FUT":
        return get_futures_contract(symbol)
    elif ctype == "STK":
        return get_stock_contract(symbol)
    else:
        return get_options_contract(symbol)

def contract_type(symbol):
    if len(symbol) in (4, 5) and symbol[-1].isdigit():
        return "FUT"
    elif len(symbol) <= 5:
        return "STK"
    else:
        return "" # is nothing

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
            if '#' in symbol:
                symbol = symbol[:symbol.index('#')]
            symbol = symbol.strip()
            if symbol == '':
                continue
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

def int_round_to(number, rounder):
    return round(number / rounder) * rounder

def add_separators_to_list(lst, condition, separators):
    i = 0
    while i < len(lst) and len(separators) > 0:
        if condition(lst[i], separators[0]):
            lst.insert(i, ["**"] * len(lst[0]))
            separators.pop(0)
            i += 1
        i += 1

# ------ Private ------

def get_basic_contract():
    contract = Contract()
    contract.currency = "USD"
    contract.exchange = "SMART"
    return contract

# Not working method
def get_options_contract(symbol):
    contract = get_basic_contract()
    contract.symbol = symbol
    contract.secType = "OPT"
    contract.multiplier = "100"
    # contract.lastTradeDateOrContractMonth = date_str
    # contract.strike = strike
    # contract.right = right
    return contract

def get_stock_contract(symbol):
    contract = get_basic_contract()
    contract.symbol = symbol
    contract.secType = "STK"
    if symbol in ("GLD", "GDX", "GDXJ", "SOYB", "CORN", "WEAT"):
        contract.exchange = "ARCA"
    elif symbol in ("MSFT", "INTC", "CSCO"):
        contract.exchange = "ISLAND"
        # contract.primaryExchange = "ISLAND"
    return contract

def get_futures_contract(symbol):
    contract = get_basic_contract()
    contract.secType = "FUT"
    
    underlying_symbol = symbol[:-2]

    if underlying_symbol in ("GC", "SI", "NG", "CL", "HG"):
        contract.exchange = "NYMEX"
    elif underlying_symbol in ("ES", "GE"):
        contract.exchange = "GLOBEX"
    elif underlying_symbol in ("UB" ,"ZB", "ZN", "ZF", "ZT", "ZS", "ZC", "ZW", "YM"):
        contract.exchange = "ECBOT"
    elif underlying_symbol in ("EUR", "JPY", "CAD", "AUD"):
        contract.exchange = "GLOBEX"
    elif underlying_symbol in ("VIX"):
        contract.exchange = "CFE"
        contract.localSymbol = "VX" + symbol[-2:]
    
    contract.symbol = underlying_symbol
    contract.lastTradeDateOrContractMonth = get_futures_date(symbol[-2:]) # eg. "201612"

    return contract

# fd code is something like U8
def get_futures_date(fdcode):
    month = None
    year = None

    if fdcode[0] == "F":
        month = "01"
    elif fdcode[0] == "G":
        month = "02"
    elif fdcode[0] == "H":
        month = "03"
    elif fdcode[0] == "J":
        month = "04"
    elif fdcode[0] == "K":
        month = "05"
    elif fdcode[0] == "M":
        month = "06"
    elif fdcode[0] == "N":
        month = "07"
    elif fdcode[0] == "Q":
        month = "08"
    elif fdcode[0] == "U":
        month = "09"
    elif fdcode[0] == "V":
        month = "10"
    elif fdcode[0] == "X":
        month = "11"
    elif fdcode[0] == "Z":
        month = "12"
    else:
        raise InputError("Unknown futures month")

    if fdcode[1] == "8":
        year = "2018"
    elif fdcode[1] == "9":
        year = "2019"
    elif fdcode[1] == "0":
        year = "2020"
    elif fdcode[1] == "1":
        year = "2021"
    elif fdcode[1] == "2":
        year = "2022"
    # more elifs...
    else:
        raise InputError("Bruno: Unknown futures year")

    return year + month