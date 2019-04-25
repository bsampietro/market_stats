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
        'LngInt',
        'LngRnk',
        'LngV%',
        'Shrt%',
        'L%chg',
        'UD7',
        'SPCrr',
        'SP-R',
        '210R',
        'DrcQt',
        'CtrNr',
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
        iv = IV(gcnv.data_handler, ticker)
        hv = HV(gcnv.data_handler, ticker)
        mixed_vs = MixedVs(gcnv.data_handler, iv, hv)
        stock = Stock(gcnv.data_handler, ticker)
        spy_pair = Pair(gcnv.data_handler, ticker, "SPY")
        spy_iv = IV(gcnv.data_handler, "SPY")
        earnings_data = load_earnings()
        row = [ticker, date]
        # Price related data
        row += [
            stock.get_close_at(date),
            f"{stock.min(back_days)} - {stock.max(back_days)}",
            stock.min_max_rank(date, back_days),
            stock.current_to_ma_percentage(date, back_days) / core.safe_execute(1, GettingInfoError, spy_pair.stdev_ratio, back_days),
            stock.current_to_ma_percentage(date, 14),
            stock.get_last_percentage_change(),
            stock.closes_nr(7, 1) - stock.closes_nr(7, -1),
            core.safe_execute('-', GettingInfoError, spy_pair.correlation, back_days),
            core.safe_execute('-', GettingInfoError, spy_pair.stdev_ratio, back_days),
            stock.hv_to_10_ratio(back_days),
            util.int_round_to(notional.directional_quantity(stock.hv_to_10_ratio(back_days)), 100),
            round(notional.contract_number(stock.get_close_at(date), stock.hv_to_10_ratio(back_days)), 1),
            earnings_data[ticker][0],
            earnings_data[ticker][1],
            chart_link(ticker)
        ]
        # Volatility related data
        try:
            row += [
                iv.current_to_average_ratio(date, back_days),
                mixed_vs.iv_current_to_hv_average(date, back_days),
                mixed_vs.negative_difference_ratio(back_days),
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
        'Min365',
        'Max365',
        'Rank365',
        'MA365',
        '-',
        'VRat',
        'Corr',
        '210R',
        '-']
    header += ['-'] * 3
    return header


def get_pairs_row(ticker1, ticker2, fixed_stdev_ratio = None):
    try:
        pair = Pair(gcnv.data_handler, ticker1, ticker2, fixed_stdev_ratio)
        date = '-' if gcnv.data_handler.get_max_stored_date("STOCK", ticker1) is None else util.date_in_string(gcnv.data_handler.get_max_stored_date("STOCK", ticker1))
        row = [ticker1 + '-' + ticker2,
            date,
            '-',
            pair.get_last_close(gcnv.back_days),
            pair.min(gcnv.back_days),
            pair.max(gcnv.back_days),
            pair.current_rank(gcnv.back_days),
            pair.ma(gcnv.back_days),
            '-',
            pair.stdev_ratio(gcnv.back_days),
            pair.correlation(gcnv.back_days),
            pair.hv_to_10_ratio(gcnv.back_days),
            '-']
        closes = pair.closes(70)[-3:]
        closes.reverse()
        row += closes
        return row
    except (GettingInfoError, ZeroDivisionError, statistics.StatisticsError) as e:
        print(e)
        return []


def get_query_date(ticker):
    if gcnv.connected:
        return util.today_in_string()
    else:
        max_stored_date = gcnv.data_handler.get_max_stored_date("STOCK", ticker)
        if max_stored_date is None:
            return util.today_in_string()
        else:
            return util.date_in_string(max_stored_date)


def bring_if_connected(ticker, bring_volatility):
    if not gcnv.connected:
        return
    try:
        if bring_volatility:
            max_stored_date = gcnv.data_handler.get_max_stored_date("IV", ticker)
            if (max_stored_date is None) or max_stored_date.date() < date.today():
                print(f"Getting IV data for ticker {ticker}...")
                gcnv.data_handler.request_historical_data("IV", ticker)

            max_stored_date = gcnv.data_handler.get_max_stored_date("HV", ticker)
            if (max_stored_date is None) or (max_stored_date.date() < (date.today() - timedelta(days = 4))): # arbitrary 4 days because is not needed day to day
                print(f"Getting HV data for ticker {ticker}...")
                gcnv.data_handler.request_historical_data("HV", ticker)

        max_stored_date = gcnv.data_handler.get_max_stored_date("STOCK", ticker)
        if (max_stored_date is None) or max_stored_date.date() < date.today():
            print(f"Getting STOCK data for ticker {ticker}...")
            gcnv.data_handler.request_historical_data("STOCK", ticker)
    except InputError as e:
        print(e)


def read_symbol_file_and_process(command, get_row_method, back_days = None):
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    v_tickers = util.read_symbol_list(f"{gcnv.APP_PATH}/input/options.txt") + util.read_symbol_list(f"{gcnv.APP_PATH}/input/stocks.txt")
    rows = []
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
        for ticker in tickers:
            if ticker == '---':
                if len(rows) > 0:
                    rows.append(['-'] * len(rows[0]))
                continue
            bring_if_connected(ticker, ticker in v_tickers)
            row = get_row_method(ticker, get_query_date(ticker), back_days)
            if len(row) > 0:
                rows.append(row)
    else:
        ticker = command[1].upper()
        bring_if_connected(ticker, ticker in v_tickers)
        row = get_row_method(ticker, get_query_date(ticker), back_days)
        if len(row) > 0:
            rows.append(row)
    return rows


def read_pairs_file_and_process(command, get_row_method):
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    rows = []
    if os.path.isfile(text_file):
        pairs = util.read_symbol_list(text_file)
        for pair in pairs:
            if pair == '---':
                if len(rows) > 0:
                    rows.append(['-'] * len(rows[0]))
                continue
            data = pair.split('-') + [None] * 5
            ticker1 = data[0]; ticker2 = data[1]; stdev_ratio = data[2]
            bring_if_connected(ticker1, False)
            bring_if_connected(ticker2, False)
            row = get_row_method(ticker1, ticker2, stdev_ratio)
            if len(row) > 0:
                rows.append(row)
    else:
        ticker1 = command[1].upper(); ticker2 = command[2].upper(); stdev_ratio = command[3]
        bring_if_connected(ticker1, False)
        bring_if_connected(ticker2, False)
        row = get_row_method(ticker1, ticker2, stdev_ratio)
        if len(row) > 0:
            rows.append(row)
    return rows


def update_stock(command):
    text_file = f"{gcnv.APP_PATH}/input/{command[1]}.txt"
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
        for ticker in tickers:
            if ticker != '---':
                gcnv.data_handler.request_market_data("STOCK", ticker)
    else:
        ticker = command[1].upper()
        gcnv.data_handler.request_market_data("STOCK", ticker)


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