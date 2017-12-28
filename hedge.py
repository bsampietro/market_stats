import sys

import logging

from datetime import datetime, date
from ib.ib_hedge import IBHedge


# Global variables and constants
MONITOR_TICKER = "ES" # SPY or ES
LAST_TRADE_DATE = "201712"
HEDGER_STRIKE = 230 # SPY:230 / ES:2300 # and use same last_trade_date than future

# Main method
if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler("./log/_hedge.log"))
    ## logging.basicConfig(level=logging.INFO)
    
    try:
        ib_hedge = IBHedge()
        ib_hedge.wait_for_readiness()
        ib_hedge.start_monitoring(MONITOR_TICKER, LAST_TRADE_DATE)

        # Waiting indefinitely to catch the program termination exception
        time.sleep(999999999)
    except (KeyboardInterrupt, SystemExit) as e:
        ib_hedge.clear_all()
        print("Program stopped")
    except:
        ib_hedge.clear_all()
        raise
