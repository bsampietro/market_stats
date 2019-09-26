import statistics
from lib import util, core
from lib.errors import *
from controllers.helper import *
from models.pair import Pair
from controllers.helper import *
import gcnv

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

def get_pairs_row(pair, command):
    ps = process_pair_string(pair)
    ticker1 = ps.ticker1
    ticker2 = ps.ticker2
    fixed_stdev_ratio = ps.stdev_ratio
    back_days = core.safe_execute(gcnv.PAIR_BACK_DAYS, ValueError, 
        lambda x: int(x) * 30, command[2])
    bring_if_connected(ticker1)
    bring_if_connected(ticker2)
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
