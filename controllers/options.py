from controllers.helper import *
import gcnv

def get_options_header():
    header = ['Tckr']
    return header

def get_options_row(ticker, command):
    gcnv.ib.request_options_data()
    row = []
    return row