# Global Constants aNd Variables

import sys, os

# Global constants and configuration
IVR_RESULTS = 8 # Number of historical IVR rows
BETA_REFERENCES = ["SPY"]
MIN_CORRELATED_CORRELATION = 0.40
MAX_UNCORRELATED_CORRELATION = 0.20
TEN_PERCENTAGE_HV = 0.50 # 0.50 is the 10% percentage_hv with "my math"

# Constants
APP_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))

# Variables
data_handler = None
connected = False
back_days = 365