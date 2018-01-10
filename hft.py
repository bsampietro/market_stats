import sys
import logging
from datetime import datetime, date
import time

from ib.ib_hft import IBHft
from models.hft_monitor import HftMonitor

# Main method
if __name__ == "__main__":
    logging.basicConfig(filename='./log/_hft.log', level=logging.INFO)
    
    # logger = logging.getLogger()
    # logger.setLevel(logging.INFO)
    # logger.addHandler(logging.FileHandler("./log/_hft.log"))
    # # logging.basicConfig(level=logging.INFO)
    
    try:
        ib_hft = IBHft()
        monitor1 = HftMonitor(sys.argv[1], ib_hft)
        # ib_hft.wait_for_readiness()
        # ib_hft.start_monitoring(sys.argv[1])
        
        # when having ticker list:
        # client_id = 100
        # monitors = []
        # for ticker in tickers:
        #     client_id += 1
        #     monitors.append(IBHft(ticker, client_id))

        # Waiting indefinitely to catch the program termination exception
        time.sleep(999999999)
    except (KeyboardInterrupt, SystemExit) as e:
        ib_hft.clear_all()
        print("Program stopped")
    except:
        ib_hft.clear_all()
        raise
