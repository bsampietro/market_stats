import sys
sys.path.append('/home/bruno/ib_api/9_73/IBJts/source/pythonclient')
from ibapi.contract import *

from datetime import datetime, timedelta
import statistics

def get_contract(symbol):
    ctype = contract_type(symbol)
    if ctype == "FUT":
        return get_futures_contract(symbol)
    elif ctype == "OPT":
        return get_options_contract(symbol)
    else:
        return get_stock_contract(symbol)

def contract_type(symbol):
    if "_" in symbol:
        return "FUT"
    elif len(symbol) >= 6:
        return "OPT"
    else:
        return "STK"

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
    if symbol in ("GLD", "GDX", "GDXJ"):
        contract.exchange = "ARCA"
    elif symbol in ("MSFT", "INTC", "CSCO"):
        contract.exchange = "ISLAND"
        # contract.primaryExchange = "ISLAND"
    return contract

def get_futures_contract(symbol):
    contract = get_basic_contract()
    contract.secType = "FUT"
    if symbol[1:3] in ("GC", "SI", "NG", "CL"):
        contract.exchange = "NYMEX"
    elif symbol[1:3] in ("ES", "6E", "6J", "GE"):
        contract.exchange = "GLOBEX"
    elif symbol[1:3] in ("UB" ,"ZB", "ZN", "ZF", "ZT"):
        contract.exchange = "ECBOT" # on IB is ECBOT
        # contract.exchange = "GLOBEX"
    
    # using localSymbol
    # contract.localSymbol = symbol[1:5]
    
    # using symbol and date
    contract.symbol = symbol[1:3]
    contract.lastTradeDateOrContractMonth = get_futures_date(symbol[3:5]) # eg. "201612"

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
        raise RuntimeError("Unknown futures month")

    if fdcode[1] == "8":
        year = "2018"
    elif fdcode[1] == "9":
        year = "2019"
    # more elifs...
    else:
        raise RuntimeError("Unknown futures year")

    return year + month


# ----------- to implement ---------------

def get_option_expiration(date):
    day = 21 - (calendar.weekday(date.year, date.month, 1) + 2) % 7
    return datetime(date.year, date.month, day)

