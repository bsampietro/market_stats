import sys
import logging
from datetime import datetime, date, timedelta
import os.path
import statistics
import json
from json.decoder import JSONDecodeError

from lib import util, core
from lib.errors import *
from models.datahandler import DataHandler
from models.iv import IV
from models.hv import HV
from models.mixed_vs import MixedVs
from models.stock import Stock
from models.pair import Pair
from models import notional

import config.constants as const
from config import main_vars

def get_iv_header():
    header = ['Tckr', 'Date']
    header += [
        'Last',
        'LngInt',
        'LngRnk',
        'LngV%',
        'Shrt%',
        'L%chg',
        'UD15',
        'SPCrr',
        'SP-R',
        'Erngs'
    ]
    header += [
        'I2Iav',
        'I2Hav',
        'IV2HV-',
        'I2HAv',
        'Ntnl',
        'Jmp',
        '%Rnk',
        'IVR'
    ]
    header += ['-'] * (const.IVR_RESULTS - 1) # 1 is the IVR title
    return header

def get_iv_row(ticker, date, back_days):
    try:
        iv = IV(main_vars.data_handler, ticker)
        hv = HV(main_vars.data_handler, ticker)
        mixed_vs = MixedVs(main_vars.data_handler, iv, hv)
        stock = Stock(main_vars.data_handler, ticker)
        spy_pair = Pair(main_vars.data_handler, ticker, "SPY")
        spy_iv = IV(main_vars.data_handler, "SPY")
        row = [ticker, date]
        # Price related data
        row += [
            stock.get_close_at(date),
            f"{stock.min(365)} - {stock.max(365)}",
            stock.min_max_rank(date, 365),
            stock.current_to_ma_percentage(date, 365) / core.safe_execute(1, GettingInfoError, spy_pair.stdev_ratio, back_days),
            stock.current_to_ma_percentage(date, 14),
            stock.get_last_percentage_change(),
            stock.closes_nr(15, up = True) - stock.closes_nr(15, up = False),
            core.safe_execute(1, GettingInfoError, spy_pair.correlation, back_days),
            core.safe_execute(1, GettingInfoError, spy_pair.stdev_ratio, back_days),
            '-'
        ]
        # Volatility related data
        try:
            row += [
                iv.current_to_average_ratio(date, back_days),
                mixed_vs.iv_current_to_hv_average(date, back_days),
                mixed_vs.negative_difference_ratio(back_days),
                mixed_vs.difference_average(back_days),
                notional.quantity(iv.current_weighted_iv_rank(back_days), core.safe_execute(1, GettingInfoError, spy_pair.stdev_ratio, back_days)),
                notional.jumps(stock.get_close_at(date), core.safe_execute(1, GettingInfoError, spy_pair.stdev_ratio, back_days)),
                iv.current_percentile_iv_rank(back_days)
            ]
            row += iv.period_iv_ranks(back_days, max_results = const.IVR_RESULTS)
        except (GettingInfoError, ZeroDivisionError, statistics.StatisticsError) as e:
            result_row_len = 7
            row += ['-'] * (result_row_len + const.IVR_RESULTS)
        return row
    except (GettingInfoError, ZeroDivisionError, statistics.StatisticsError) as e:
        print(e)
        return []


def get_hv_header():
    header = ['Ticker',
        'Date',
        'HV30',
        'HV365',
        '-',
        'HV30%',
        'HV365%',
        'HV365to10',
        '-',
        'HVacc30%',
        'HVacc365%']
    return header


# back_days parameter added for compliance with get_xxx_row methods
# as they are passed as parameter to read_symbol_file_and_process
def get_hv_row(ticker, date, back_days = None):
    try:
        stock = Stock(main_vars.data_handler, ticker)
        row = [ticker,
            date,
            stock.hv(30),
            stock.hv(365),
            '-',
            stock.percentage_hv(30),
            stock.percentage_hv(365),
            stock.to_10_ratio(365),
            '-',
            stock.accumulative_percentage_hv(30),
            stock.accumulative_percentage_hv(365)]
        return row
    except (GettingInfoError, ZeroDivisionError, statistics.StatisticsError) as e:
        print(e)
        return []


def get_pairs_header():
    header = ['Pair',
        'Date',
        '-',
        'Last200',
        'Min200',
        'Max200',
        'Rank200',
        'MA200',
        '-',
        'Last50',
        'Min50',
        'Max50',
        'Rank50',
        'MA50',
        '-',
        'VRat',
        'Corr',
        'SPYVRat',
        '-']
    header += ['-'] * 3
    return header


def get_pairs_row(ticker1, ticker2, fixed_stdev_ratio = None):
    try:
        pair = Pair(main_vars.data_handler, ticker1, ticker2, fixed_stdev_ratio)
        date = '-' if main_vars.data_handler.get_max_stored_date("STOCK", ticker1) is None else util.date_in_string(main_vars.data_handler.get_max_stored_date("STOCK", ticker1))
        row = [ticker1 + '-' + ticker2,
            date,
            '-',
            pair.get_last_close(280),
            pair.min(280),
            pair.max(280),
            pair.current_rank(280),
            pair.ma(280),
            '-',
            pair.get_last_close(70),
            pair.min(70),
            pair.max(70),
            pair.current_rank(70),
            pair.ma(70),
            '-',
            pair.stdev_ratio(main_vars.back_days),
            pair.correlation(main_vars.back_days),
            pair.stdev(main_vars.back_days) / Stock(main_vars.data_handler, 'SPY').stdev(main_vars.back_days),
            '-']
        closes = pair.closes(70)[-3:]
        closes.reverse()
        row += closes
        return row
    except (GettingInfoError, ZeroDivisionError, statistics.StatisticsError) as e:
        print(e)
        return []


def get_query_date(ticker):
    if main_vars.connected:
        return util.today_in_string()
    else:
        max_stored_date = main_vars.data_handler.get_max_stored_date("STOCK", ticker)
        if max_stored_date is None:
            return util.today_in_string()
        else:
            return util.date_in_string(max_stored_date)


def bring_if_connected(ticker, bring_volatility):
    if not main_vars.connected:
        return
    try:
        if bring_volatility:
            max_stored_date = main_vars.data_handler.get_max_stored_date("IV", ticker)
            if (max_stored_date is None) or max_stored_date.date() < date.today():
                print(f"Getting IV data for ticker {ticker}...")
                main_vars.data_handler.request_historical_data("IV", ticker)

            max_stored_date = main_vars.data_handler.get_max_stored_date("HV", ticker)
            if (max_stored_date is None) or (max_stored_date.date() < (date.today() - timedelta(days = 4))): # arbitrary 4 days because is not needed day to day
                print(f"Getting HV data for ticker {ticker}...")
                main_vars.data_handler.request_historical_data("HV", ticker)

        max_stored_date = main_vars.data_handler.get_max_stored_date("STOCK", ticker)
        if (max_stored_date is None) or max_stored_date.date() < date.today():
            print(f"Getting STOCK data for ticker {ticker}...")
            main_vars.data_handler.request_historical_data("STOCK", ticker)
    except InputError as e:
        print(e)


def read_symbol_file_and_process(command, get_row_method, back_days = None):
    text_file = "./input/" + command[1] + ".txt"
    v_tickers = util.read_symbol_list("./input/options.txt") + util.read_symbol_list("./input/stocks.txt")
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
    text_file = "./input/" + command[1] + ".txt"
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
    text_file = "./input/" + command[1] + ".txt"
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
        for ticker in tickers:
            if ticker != '---':
                main_vars.data_handler.request_market_data("STOCK", ticker)
    else:
        ticker = command[1].upper()
        main_vars.data_handler.request_market_data("STOCK", ticker)


def load_earnings():
    try:
        with open('./data/earnings.json', 'r') as f:
            earnings_data = json.load(f)
    except (JSONDecodeError, FileNotFoundError) as e:
        earnings_data = {}
    return earnings_data


def save_earnings(data):
    with open('./data/earnings.json', 'w') as f:
        json.dump(data, f, indent=4)