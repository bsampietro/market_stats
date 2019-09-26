import sys
import os
import logging
from datetime import datetime, date, timedelta
import statistics
import json
from json.decoder import JSONDecodeError
import time
from collections import defaultdict

from lib import util, core
from lib.errors import *
from models.datahandler import DataHandler
from models.iv import IV
from models.hv import HV
from models.mixed_vs import MixedVs
from models.stock import Stock
from models.pair import Pair
from models import notional

import gcnv

def get_iv_header():
    header = ['Tckr', 'Date']
    header += [
        'Last',
        'BDInterval',
        'BDRnk',
        'BDV%',
        '14%',
        'Rng14',
        'L%chg',
        'UD14',
        'SPCrr',
        '210R',
        'DStkNr',
        'NOptNr',
        'DOptNr',
        'Erngs',
        'D2Ern',
        'Chart'
    ]
    header += [
        'I2Iav',
        'I2Hav',
        'IV2HV-',
        'I2HAv',
        '%Rnk',
        'IVR'
    ]
    header += ['-'] * (gcnv.IVR_RESULTS - 1) # 1 is the IVR title
    return header

def get_iv_row(ticker, date, back_days):
    try:
        iv = IV(ticker)
        hv = HV(ticker)
        mixed_vs = MixedVs(iv, hv)
        stock = Stock(ticker)
        spy_pair = Pair(ticker, "SPY")
        spy_iv = IV("SPY")
        earnings_data = load_earnings()
        row = [ticker, date]
        # Price related data
        row += [
            stock.get_close_at(date), # GettingInfoError raised here if not stored data
            f"{stock.min(back_days)} - {stock.max(back_days)}",
            round(stock.min_max_rank(date, back_days)),
            stock.current_to_ma_percentage(date, back_days) / stock.hv_to_10_ratio(back_days),
            stock.current_to_ma_percentage(date, 14) / stock.hv_to_10_ratio(back_days),
            stock.range(14) / stock.hv_to_10_ratio(back_days),
            stock.get_last_percentage_change(),
            up_down_closes_str(stock, 14),
            core.safe_execute('-', GettingInfoError, spy_pair.correlation, back_days),
            stock.hv_to_10_ratio(back_days),
            round(notional.directional_stock_number(stock.get_close_at(date),
                stock.hv_to_10_ratio(back_days))),
            round(notional.neutral_options_number(stock.get_close_at(date),
                stock.hv_to_10_ratio(back_days)), 1),
            round(notional.directional_options_number(stock.get_close_at(date),
                stock.hv_to_10_ratio(back_days)), 1),
            earnings_data[ticker][0],
            earnings_data[ticker][1],
            chart_link(ticker)
        ]
        # Volatility related data
        try:
            row += [
                iv.current_to_average_ratio(date, back_days),
                mixed_vs.iv_current_to_hv_average(date, back_days),
                mixed_vs.positive_difference_ratio(back_days),
                mixed_vs.difference_average(back_days),
                iv.current_percentile_iv_rank(back_days)
            ]
            row += iv.period_iv_ranks(back_days, max_results = gcnv.IVR_RESULTS)
        except (GettingInfoError, ZeroDivisionError, statistics.StatisticsError) as e:
            result_row_len = 5 # Number of rows above
            row += ['-'] * (result_row_len + gcnv.IVR_RESULTS)
        return row
    except (GettingInfoError, ZeroDivisionError, statistics.StatisticsError) as e:
        print(e)
        return []


def get_pairs_header():
    header = ['Pair',
        'Date',
        '-',
        'Last',
        'Min',
        'Max',
        'Rank',
        'MA',
        '-',
        'VRat',
        'Corr',
        '210R',
        '-']
    header += ['-'] * gcnv.PAIR_PAST_RESULTS
    return header


def get_pairs_row(ticker1, ticker2, fixed_stdev_ratio, back_days):
    try:
        pair = Pair(ticker1, ticker2, fixed_stdev_ratio)
        max_stored_date = gcnv.data_handler.get_max_stored_date("STOCK", ticker1)
        date = '-' if max_stored_date is None \
                    else util.date_in_string(max_stored_date) # Need to change this
        row = [ticker1 + '-' + ticker2,
            date,
            '-',
            pair.get_last_close(back_days), # GettingInfoError raised here if not stored data
            pair.min(back_days),
            pair.max(back_days),
            pair.current_rank(back_days),
            pair.ma(back_days),
            '-',
            pair.stdev_ratio(back_days),
            pair.correlation(back_days),
            pair.hv_to_10_ratio(back_days),
            '-']
        closes = pair.closes(back_days)[-gcnv.PAIR_PAST_RESULTS:]
        closes.reverse()
        row += closes
        return row
    except (GettingInfoError, ZeroDivisionError, statistics.StatisticsError) as e:
        print(e)
        return []


def get_query_date(ticker):
    if gcnv.ib:
        return util.today_in_string()
    else:
        max_stored_date = gcnv.data_handler.get_max_stored_date("STOCK", ticker)
        if max_stored_date is None:
            return util.today_in_string()
        else:
            return util.date_in_string(max_stored_date)


def bring_if_connected(tickers):
    if gcnv.ib is None:
        return
    for ticker in tickers:
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
        except InputError as e:
            print(e)


def read_symbol_file_and_process(command, get_row_method):
    back_days = core.safe_execute(gcnv.BACK_DAYS, ValueError, 
        lambda x: int(x) * 30, command[2])
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    rows = []
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
    else:
        tickers = [command[1].upper()]
    bring_if_connected(tickers)
    if gcnv.ib:
        gcnv.ib.wait_for_async_request()
    for ticker in tickers:
        row = get_row_method(ticker, get_query_date(ticker), back_days)
        if len(row) > 0:
            rows.append(row)
    return rows


def read_pairs_file_and_process(command, get_row_method):
    back_days = core.safe_execute(gcnv.PAIR_BACK_DAYS, ValueError, 
        lambda x: int(x) * 30, command[2])
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    rows = []
    if os.path.isfile(text_file):
        pairs = util.read_symbol_list(text_file)
    else:
        pairs = [command[1]]
    for pair in pairs:
        ps = process_pair_string(pair)
        bring_if_connected([ps.ticker1, ps.ticker2])
        if gcnv.ib:
            gcnv.ib.wait_for_async_request()
        row = get_row_method(ps.ticker1, ps.ticker2, ps.stdev_ratio, back_days)
        if len(row) > 0:
            rows.append(row)
    return rows


def update_stock(command):
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
        for ticker in tickers:
            gcnv.ib.request_market_data("STOCK", ticker)
    else:
        ticker = command[1].upper()
        gcnv.ib.request_market_data("STOCK", ticker)


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


def save_earnings(data):
    with open(f"{gcnv.APP_PATH}/data/earnings.json", "w") as f:
        json.dump(data, f, indent=4)


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


def up_down_closes_str(stock, back_days):
    map = ["+" if udc == 1 else "-" for udc in stock.up_down_closes(back_days)]
    map.reverse()
    map = map[1:] # remove first element which is today
    return str(" ").join(map)