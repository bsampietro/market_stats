# Global Constants aNd Variables

import sys, os

# Global constants and configuration
IVR_RESULTS = 8 # Number of historical IVR rows
BETA_REFERENCES = ["SPY"]
MIN_CORRELATED_CORRELATION = 0.40
MAX_UNCORRELATED_CORRELATION = 0.20

# Declared constants and variables. They will be set on initialization.
# Constants
APP_PATH = None

# Variables
data_handler = None
connected = None
back_days = None