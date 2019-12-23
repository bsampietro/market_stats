""" Global Constants aNd Variables """

# +++++++++ Global Configuration +++++++++++

IVR_RESULTS = 8 # Number of historical IVR rows
PAIR_PAST_RESULTS = 5
BACK_DAYS = 365
PAIR_BACK_DAYS = 90
BRING_VOLATILITY_DATA = False

# Notional
DIRECTIONAL_DOLLARS = 3000 # for a 10 volatility ratio
NEUTRAL_DOLLARS = DIRECTIONAL_DOLLARS * 3 # assuming 0.33 delta is average size of position when going against you
AVERAGE_OPTIONS_DELTA = 0.30


# ++++ Declaring constants and variables (to be set on initialization) ++++

# Constants
APP_PATH = None

# Variables
data_handler = None
messages = None
v_tickers = None
store_dir = None
ib = None


# temp variable to hold options data
# until datahandler is restructured
from collections import defaultdict
options = defaultdict(list)