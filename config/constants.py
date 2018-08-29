# Global constants
IVR_RESULTS = 8 # Number of historical IVR rows
BETA_REFERENCES = ["SPY"]
ST_ORDER_COLUMN = 6
MIN_CORRELATED_CORRELATION = 0.40
MAX_UNCORRELATED_CORRELATION = 0.20
TEN_PERCENTAGE_HV = 0.50 # 0.50 is the 10% percentage_hv with "my math"
VOL_ORD = {'vord': 14, 'pord': 20 + IVR_RESULTS}
VOL_DEFAULT_ORD = {'vord': 30, 'pord': 0} # where to put lines