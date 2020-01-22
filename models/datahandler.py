import json
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta
import os

from lib import util
from lib.errors import *
from ib.ib_data import IBData

import gcnv

DOCUMENTS = ['iv', 'hv', 'stock']

class DataHandler:
    def __init__(self):
        self.modified = set()
        self.load()

    def load(self):
        for document in DOCUMENTS:
            setattr(self, document, {})
            data = getattr(self, document)
            filenames = os.listdir(f"{gcnv.APP_PATH}/data/{document}")
            tickers = [filename.replace('.json', '')
                        for filename in filenames 
                        if '.json' in filename] # could add file checking also
            for ticker in tickers:
                with open(f"{gcnv.APP_PATH}/data/{document}/{ticker}.json", "r") as f:
                    data[ticker] = json.load(f)


    def save(self):
        for document in DOCUMENTS:
            data = getattr(self, document)
            for ticker in data.keys():
                if (document, ticker) not in self.modified:
                    continue
                with open(f"{gcnv.APP_PATH}/data/{document}/{ticker}.json", "w") as f:
                    json.dump(data[ticker], f)

    def store_history(self, document, ticker, date, value):
        assert document in DOCUMENTS
        data = getattr(self, document)
        if not ticker in data:
            data[ticker] = {}
        data[ticker][date] = value
        self.modified.add((document, ticker))

    def get_max_stored_date(self, document, ticker):
        assert document in DOCUMENTS
        data = self.find_in_data(document, ticker, None, silent = True)
        if data is None:
            return None
        else:
            return datetime.strptime(max(data.keys()), "%Y%m%d")
    
    def find_in_data(self, document, ticker, date, silent):
        assert document in DOCUMENTS
        data = getattr(self, document)
        try:
            if date is None:
                return data[ticker]
            else:
                date = util.date_in_string(date)
                return data[ticker][date]
        except KeyError as e:
            if silent:
                return None
            elif gcnv.ib:
                raise GettingInfoError(
                    f"{ticker} not stored, getting it in background...")
            else:
                raise GettingInfoError(
                    f"{ticker} info not available and remote not connected")

    def delete_at(self, date):
        for document in DOCUMENTS:
            data = getattr(self, document)
            for ticker, prices in data.items():
                prices.pop(date, None)
                self.modified.add((document, ticker))
        if gcnv.ib:
            gcnv.ib.reset_session_requested_data()

    def delete_back(self, back_days):
        today = datetime.today()
        for i in range(back_days):
            delete_day = util.date_in_string(today - timedelta(days = i))
            self.delete_at(delete_day)

    def delete_ticker(self, ticker):
        for document in DOCUMENTS:
            data = getattr(self, document)
            data.pop(ticker, None)
            try:
                os.remove(f"{gcnv.APP_PATH}/data/{document}/{ticker}.json") # delete file
            except FileNotFoundError as e:
                gcnv.messages.append(f"Didn't find file: {gcnv.APP_PATH}/data/{document}/{ticker}.json")
        if gcnv.ib:
            gcnv.ib.reset_session_requested_data()

    # +++ Data +++

    # Last list element is the most recent value, achieved by data.reverse() statement
    def list_data(self, wtb, back_days):
        assert all(document in DOCUMENTS for document, _ in wtb)
        min_stored_date = min(
            self.get_max_stored_date(document, ticker) for document, ticker in wtb)
        missing_dates = []
        data = []
        for i in range(back_days):
            older_date = min_stored_date - timedelta(days = i)
            close = []
            for document, ticker in wtb:
                close.append(
                    self.find_in_data(
                            document,
                            ticker,
                            older_date.strftime("%Y%m%d"),
                            True))
            if all(close_i is not None for close_i in close):
                data.append(close)
            else:
                if older_date.weekday() not in (5,6): # not a weekend and still not stored
                    missing_dates.append(older_date.strftime("%Y%m%d"))
        if back_days < 365 * 2:
            cdl = round(back_days * (5 / 7)) # correct_data_length
            if len(data) < cdl - 30 or len(data) > cdl + 15:
                gcnv.messages.append(
                    f"Incorrect data length for {wtb}. "
                    f"Should return {cdl} but returning {len(data)}. "
                    f"Missing dates: {missing_dates}")
        data.reverse()
        data = list(zip(*data))
        return data