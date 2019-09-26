import json
from json.decoder import JSONDecodeError
from datetime import datetime, date, timedelta
import time
from collections import defaultdict

from lib import util, core
import gcnv

def get_query_date(ticker):
    if gcnv.ib:
        return util.today_in_string()
    else:
        max_stored_date = gcnv.data_handler.get_max_stored_date("STOCK", ticker)
        if max_stored_date is None:
            return util.today_in_string()
        else:
            return util.date_in_string(max_stored_date)

def chart_link(ticker):
    return f"<a href=\"https://finance.yahoo.com/chart/{ticker}\" target=\"_blank\">--&gt;</a>"

def process_pair_string(pair_string):
    data = core.Struct()
    data.ticker1, data.ticker2, data.stdev_ratio, *_ = pair_string.split('-') + [None]
    data.ticker1 = data.ticker1.upper()
    data.ticker2 = data.ticker2.upper()
    data.stdev_ratio = core.safe_execute(None, (ValueError, TypeError),
                                            float, data.stdev_ratio)
    return data

def bring_if_connected(ticker):
    if gcnv.ib is None:
        return
    try:
        if ticker in gcnv.v_tickers:
            max_stored_date = gcnv.data_handler.get_max_stored_date("IV", ticker)
            if (max_stored_date is None) or max_stored_date.date() < date.today():
                print(f"Getting IV data for ticker {ticker}...")
                gcnv.ib.request_historical_data("IV", ticker)

            max_stored_date = gcnv.data_handler.get_max_stored_date("HV", ticker)
            # Using arbitrary 4 days because is not needed day to day
            if (max_stored_date is None) or (max_stored_date.date() < (date.today() - timedelta(days = 4))):
                print(f"Getting HV data for ticker {ticker}...")
                gcnv.ib.request_historical_data("HV", ticker)

        max_stored_date = gcnv.data_handler.get_max_stored_date("STOCK", ticker)
        if (max_stored_date is None) or max_stored_date.date() < date.today():
            print(f"Getting STOCK data for ticker {ticker}...")
            gcnv.ib.request_historical_data("STOCK", ticker)

        gcnv.ib.wait_for_async_request()
    except InputError as e:
        print(e)

def load_earnings():
    data = None
    try:
        with open(f"{gcnv.APP_PATH}/data/earnings.json", "r") as f:
            data = json.load(f)
    except (JSONDecodeError, FileNotFoundError) as e:
        data = {}
    data = defaultdict(lambda: ["-", "-"], data)
    today = date.today()
    yesterday = today - timedelta(days=1)
    for ticker in data.keys():
        try:
            earnings_date = datetime.strptime(data[ticker][:10], "%m/%d/%Y").date()
            if earnings_date == today:
                data[ticker] = "T" + data[ticker][10:]
            elif earnings_date == yesterday:
                data[ticker] = "Y" + data[ticker][10:]
            elif earnings_date < yesterday:
                data[ticker] = "P"
            else:
                data[ticker] = data[ticker].replace(f"/{today.year}", "")
            data[ticker] = [data[ticker], (earnings_date - today).days]
        except ValueError:
            data[ticker] = ["PrsErr", "-"]
    return data

def up_down_closes_str(stock, back_days):
    map = ["+" if udc == 1 else "-" for udc in stock.up_down_closes(back_days)]
    map.reverse()
    map = map[1:] # remove first element which is today
    return str(" ").join(map)