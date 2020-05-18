import os

from lib import util, core
import gcnv

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
    if gcnv.BRING_VOLATILITY_DATA and ticker in gcnv.v_tickers:
        max_stored_date = gcnv.data_handler.get_max_stored_date("iv", ticker)
        if (max_stored_date is None) or max_stored_date.date() < date.today():
            print(f"Getting IV data for ticker {ticker}...")
            gcnv.ib.request_historical_data("iv", ticker)

        max_stored_date = gcnv.data_handler.get_max_stored_date("hv", ticker)
        # Using arbitrary 4 days because is not needed day to day
        if (max_stored_date is None) or (max_stored_date.date() < (date.today() - timedelta(days = 4))):
            print(f"Getting HV data for ticker {ticker}...")
            gcnv.ib.request_historical_data("hv", ticker)

    max_stored_date = gcnv.data_handler.get_max_stored_date("stock", ticker)
    if (max_stored_date is None) or max_stored_date.date() < date.today(): # need to modify if today the market is not open (weekend)
        print(f"Getting stock data for ticker {ticker}...")
        gcnv.ib.request_historical_data("stock", ticker)
    gcnv.ib.wait_for_async_request()

def up_down_closes_str(stock, back_days):
    map = ["+" if udc == 1 else "-" for udc in stock.up_down_closes(back_days)]
    map.reverse()
    map = map[1:] # remove first element which is today
    return str(" ").join(map)

def get_tickers_from_command(name):
    text_file = f"{gcnv.APP_PATH}/input/{name}.txt"
    rows = []
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
        tickers = list(set(tickers))
    else:
        tickers = [name.upper()]
    return tickers