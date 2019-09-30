import gcnv
from lib import util

def price(command):
    header = ['Date', 'Price'] * 8
    values_printed = 0
    row = None
    rows = []
    for key, value in gcnv.data_handler.stock[command[2].upper()].items():
        if values_printed % 8 == 0:
            if row is not None:
                rows.append(row)
            row = []
        row.append(key)
        row.append(value)
        values_printed += 1
    for i in range(16 - len(row)):
        row.append('x')
    rows.append(row)
    return header, rows

def instruments(command):
    print("IV:")
    iv = list(gcnv.data_handler.implied_volatility.keys())
    iv.sort()
    print(iv)

    print("HV:")
    hv = list(gcnv.data_handler.historical_volatility.keys())
    hv.sort()
    print(hv)

    print("STOCK:")
    stock = list(gcnv.data_handler.stock.keys())
    stock.sort()
    print(stock)

    print("Futures:")
    futures = [st for st in stock if util.contract_type(st) == "FUT"]
    print(futures)