import json
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta

from lib import util
from lib.errors import *
from ib.ib_data import IBData

import gcnv

DOCUMENTS = ['iv', 'hv', 'stock']

class DataHandler:
    def __init__(self):
        self.load()

    def load(self):
        for document in DOCUMENTS:
            setattr(self, f"modified_{document}", False)
            with open(f"{gcnv.APP_PATH}/data/{document}.json", "r") as f:
                setattr(self, document, json.load(f))

    def save(self):
        for document in DOCUMENTS:
            if getattr(self, f"modified_{document}"):
                with open(f"{gcnv.APP_PATH}/data/{document}.json", "w") as f:
                    json.dump(getattr(self, document), f)

    def store_history(self, document, ticker, date, value):
        assert document in DOCUMENTS
        data = getattr(self, document)
        if not ticker in data:
            data[ticker] = {}
        data[ticker][date] = value
        setattr(self, f"modified_{document}", True)

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
            for value in data.values():
                value.pop(date, None)
            setattr(self, f"modified_{document}", True)
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
            setattr(self, f"modified_{document}", True)
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