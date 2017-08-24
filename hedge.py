import sys

import logging

from datetime import datetime, date
from ib_hedge import *

from util import *
from errors import *


# Global variables
# data_handler = None
# connected = False
# IVR_RESULTS = 7 # Number of historical IVR rows
# DATA_RESULTS = 10 # Number of main data rows

# Main method
if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler("output.log"))
    ## logging.basicConfig(level=logging.INFO)

    # if len(sys.argv) > 1:
    #     connected = (sys.argv[1] == "connect")
    
    try:
        ib_hedge = IBHedge()
        ib_hedge.request_market_data("SPY")

        # Waiting indefinitely to catch the program termination exception
        time.sleep(999999999)
    except (KeyboardInterrupt, SystemExit) as e:
        ib_hedge.terminateEverything()
        print("Program stopped")
    except:
        ib_hedge.terminateEverything()
        raise
