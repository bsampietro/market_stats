from models.pair import Pair
from lib import util, core
import gcnv

def pair(command):
    pair = Pair(command[1].upper(), command[2].upper())
    back_days = core.safe_execute(gcnv.BACK_DAYS, ValueError,
                    lambda x: int(x) * 30, command[3])

    print(f"  Correlation: {format(pair.correlation(back_days), '.2f')}")
    print(f"  Beta:        {format(pair.beta(back_days), '.2f')}")
    print(f"  Volat ratio: {format(pair.stdev_ratio(back_days), '.2f')}")

def table(command):
    back_days = core.safe_execute(gcnv.BACK_DAYS, ValueError,
                    lambda x: int(x) * 30, command[2])
    header = ["", "SPY", "TLT", "IEF", "GLD", "USO", "UNG", "FXE", "FXY",
                "FXB", "IYR", "XLU", "EFA", "EEM", "VXX"]
    rows = []
    for symbol in util.read_symbol_list(
            f"{gcnv.APP_PATH}/input/{command[1]}.txt"):
        row = [symbol]
        for head_symbol in header[1:]:
            if symbol == head_symbol:
                row.append("-")
            else:
                try:
                    pair = Pair(head_symbol, symbol)
                    row.append(pair.correlation(back_days))
                except GettingInfoError:
                    row.append("-")
        rows.append(row)
    return header, rows