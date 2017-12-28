import sys
import logging
from datetime import datetime, date
import os.path

from lib import util
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
    header = ['Ticker',
        'Date',
        'IV',
        'IV2IVavg',
        'IV2HVavg',
        'Avg2Avg',
        'IV2HV-',
        'SPYCrr',
        'SPY R',
        'SPY RIV',
        'Ntnl',
        '%Rnk',
        'WRnk',
        '-', 
        'IVR']
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

        row = [ticker,
            date,
            iv.get_at(date),
            iv.current_to_average_ratio(date, back_days),
            mixed_vs.iv_current_to_hv_average(date, back_days),
            mixed_vs.iv_average_to_hv_average(back_days),
            mixed_vs.negative_difference_ratio(back_days),
            spy_pair.correlation(back_days),
            spy_pair.stdev_ratio(back_days),
            iv.period_average(back_days) / spy_iv.period_average(back_days),
            notional.quantity(iv.current_weighted_iv_rank(back_days), spy_pair.stdev_ratio(back_days)),
            iv.current_percentile_iv_rank(back_days),
            iv.current_weighted_iv_rank(back_days)]
        row += ['-']
        row += iv.period_iv_ranks(back_days, max_results = const.IVR_RESULTS)
        return row
    except GettingInfoError as e:
        print(e)
        return []


def get_stock_header():
    header = ['Ticker',
        'Date',
        'Close',
        '-',
        'MA30',
        'MA30%',
        '-',
        'MA50',
        'MA50%',
        '-',
        'MA200',
        'MA200%',
        '-',
        'Min200',
        'Max200',
        '-',
        'UpCl15',
        'DoCl15',
        'ConsUp15',
        'ConsDwn15']
    return header


# back_days parameter added for compliance with get_xxx_row methods
# as they are passed as parameter to read_symbol_file_and_process
def get_stock_row(ticker, date, back_days = None):
    try:
        stock = Stock(main_vars.data_handler, ticker)
        row = [ticker,
            date,
            stock.get_close_at(date),
            '-',
            stock.ma(30),
            stock.current_to_ma_percentage(date, 30),
            '-',
            stock.ma(50),
            stock.current_to_ma_percentage(date, 50),
            '-',
            stock.ma(200),
            stock.current_to_ma_percentage(date, 200),
            '-',
            stock.min(200),
            stock.max(200),
            '-',
            stock.closes_nr(15, up = True),
            stock.closes_nr(15, up = False),
            stock.consecutive_nr(15, up = True),
            stock.consecutive_nr(15, up = False)
            ]
        return row
    except GettingInfoError as e:
        print(e)
        return []


def get_hv_header():
    header = ['Ticker',
        'Date',
        'HV30',
        'HV365',
        'HVavg',
        'MaxHV',
        '-',
        'HV30%',
        'HV365%',
        'HVavg%',
        'MaxHV%']
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
            stock.hv_average(),
            max(stock.period_hvs()),
            '-',
            stock.percentage_hv(30),
            stock.percentage_hv(365),
            stock.percentage_hv_average(),
            max(stock.percentage_period_hvs())]
        return row
    except GettingInfoError as e:
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
    header += ['-'] * 4
    return header


def get_pairs_row(ticker1, ticker2, fixed_stdev_ratio = None):
    try:
        pair = Pair(main_vars.data_handler, ticker1, ticker2, fixed_stdev_ratio)
        date = '-' if main_vars.data_handler.get_max_stored_date("STOCK", ticker1) is None else util.date_in_string(main_vars.data_handler.get_max_stored_date("STOCK", ticker1))
        row = [ticker1 + '-' + ticker2,
            date,
            '-',
            pair.get_last_close(200),
            pair.min(200),
            pair.max(200),
            pair.current_rank(200),
            pair.ma(200),
            '-',
            pair.get_last_close(50),
            pair.min(50),
            pair.max(50),
            pair.current_rank(50),
            pair.ma(50),
            '-',
            pair.stdev_ratio(365),
            pair.correlation(365),
            pair.stdev(365) / Stock(main_vars.data_handler, 'SPY').stdev(365),
            '-']
        # ranks = pair.period_ranks(50)[-5:]
        # ranks.reverse()
        # row += ranks
        closes = pair.closes(50)[-4:]
        closes.reverse()
        row += closes
        return row
    except GettingInfoError as e:
        print(e)
        return []


def get_query_date(ticker):
    if main_vars.connected:
        return util.today_in_string()
    else:
        max_stored_date = main_vars.data_handler.get_max_stored_date("IV", ticker)
        if max_stored_date is None:
            return util.today_in_string()
        else:
            return util.date_in_string(max_stored_date)


def bring_if_connected(ticker):
    if main_vars.connected:
        if ticker not in const.NO_OPTIONS:
            max_stored_date = main_vars.data_handler.get_max_stored_date("IV", ticker)
            if (max_stored_date is None) or max_stored_date.date() < date.today():
                print(f"Getting IV data for ticker {ticker}...")
                main_vars.data_handler.request_historical_data("IV", ticker)

        if ticker not in const.NO_OPTIONS:
            max_stored_date = main_vars.data_handler.get_max_stored_date("HV", ticker)
            if (max_stored_date is None) or (max_stored_date.date() < (date.today() - timedelta(days = 4))): # arbitrary 4 days because is not needed day to day
                print(f"Getting HV data for ticker {ticker}...")
                main_vars.data_handler.request_historical_data("HV", ticker)

        max_stored_date = main_vars.data_handler.get_max_stored_date("STOCK", ticker)
        if (max_stored_date is None) or max_stored_date.date() < date.today():
            print(f"Getting STOCK data for ticker {ticker}...")
            main_vars.data_handler.request_historical_data("STOCK", ticker)


def read_symbol_file_and_process(command, get_row_method, back_days = None):
    text_file = "./input/" + command + ".txt"
    rows = []
    if os.path.isfile(text_file):
        tickers = util.read_symbol_list(text_file)
        for ticker in tickers:
            if ticker == '---':
                if len(rows) > 0:
                    rows.append(['-'] * len(rows[0]))
                continue
            bring_if_connected(ticker)
            row = get_row_method(ticker, get_query_date(ticker), back_days)
            if len(row) > 0:
                rows.append(row)
    else:
        ticker = command.upper()
        bring_if_connected(ticker)
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
            bring_if_connected(ticker1)
            bring_if_connected(ticker2)
            row = get_row_method(ticker1, ticker2, stdev_ratio)
            if len(row) > 0:
                rows.append(row)
    else:
        ticker1 = command[1].upper(); ticker2 = command[2].upper(); stdev_ratio = command[3]
        bring_if_connected(ticker1)
        bring_if_connected(ticker2)
        row = get_row_method(ticker1, ticker2, stdev_ratio)
        if len(row) > 0:
            rows.append(row)
    return rows