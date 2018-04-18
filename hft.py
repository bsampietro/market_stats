import sys
import logging
from datetime import datetime, date
import time

from ib.ib_hft import IBHft
from models.hft_monitor import HftMonitor

# Main method
if __name__ == "__main__":
    logging.basicConfig(filename='./log/_hft.log', level=logging.INFO)
    
    try:
        ib_hft = IBHft()
        # ib_hft.wait_for_readiness()
        monitors = []
        tickers = [sys.argv[1]] # can be taken from list in the future
        for ticker in tickers:
            monitors.append(HftMonitor(ticker, ib_hft))

        # Waiting indefinitely to catch the program termination exception
        time.sleep(999999999)
    except (KeyboardInterrupt, SystemExit) as e:
        ib_hft.clear_all()
        print("Program stopped")
    except:
        ib_hft.clear_all()
        raise
