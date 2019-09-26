import statistics
from lib import core
from lib.errors import *
from controllers.helper import *
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

def get_iv_row(ticker, command):
    bring_if_connected(ticker)
    date = get_query_date(ticker)
    back_days = core.safe_execute(gcnv.BACK_DAYS, ValueError, 
        lambda x: int(x) * 30, command[2])
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