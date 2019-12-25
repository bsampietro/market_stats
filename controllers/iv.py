import statistics
from lib import util, core
from lib.errors import *
from controllers.helper import *
from models.iv import IV
from models.hv import HV
from models.mixed_vs import MixedVs
from models.stock import Stock
from models.pair import Pair
from models import notional
import gcnv

def table(command):
    header = get_header()
    rows = get_rows(command)

    # Remove year from date
    current_year = time.strftime('%Y')
    for row in rows:
        row[1] = row[1].replace(current_year, "")

    # Filter
    if 'filter' in command:
        rank_column = header.index("BDRnk")
        options_list = (util.read_symbol_list(f"{gcnv.APP_PATH}/input/options.txt") +
                        util.read_symbol_list(f"{gcnv.APP_PATH}/input/stocks.txt"))
        rows = [row for row in rows if not (
                    isinstance(row[rank_column], (int, float)) and 
                    35 < row[rank_column] < 65 and row[0] not in options_list)]
                    # conditions are for exclusion, note the 'not' at 
                    #the beginning of the if condition

    # Sorting
    order_column = command[3] if command[3] in header else "BDRnk"
    order_column = header.index(order_column)
    rows.sort(key = lambda row: row[order_column], reverse = True)
    util.add_separators_to_list(rows, lambda row, sep: row[order_column] <= sep, [50])

    return header, rows, order_column


def get_rows(command):
    tickers = get_tickers_from_command(command[1])
    rows = []
    for ticker in tickers:
        row = get_row(ticker, command)
        if len(row) > 0:
            rows.append(row)
    return rows

def get_header():
    header = ['Tckr', 'Date']
    header += [
        'Last',
        'BDInterval',
        'BDRnk',
        'Rng28',
        'Rng14',
        'Move7',
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

def get_row(ticker, command):
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
            stock.range(28) / stock.hv_to_10_ratio(back_days),
            stock.range(14) / stock.hv_to_10_ratio(back_days),
            stock.move(7) / stock.hv_to_10_ratio(back_days),
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