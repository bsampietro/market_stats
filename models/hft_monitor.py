from datetime import datetime, date
import time
import logging
import statistics

import pygal

from lib import util

class HftMonitor:
    SPEED_RATIO_THRESHOLD = 3
    MAX_STORED_SPEEDS = 100

    def __init__(self, ticker, remote):
        # price variables
        self.last_price = None
        self.last_time = None
        self.speeds = []
        self.position = 0
        self.confirmed_position = 0
        self.order_price = 0
        self.confirmed_price = 0

        self.prices = []
        self.times = []

        self.price_change_times = 0
        
        # general variables
        self.ticker = ticker.upper()
        self.contract = util.get_contract(self.ticker)

        #self.req_id = remote.get_next_req_id()
        remote.start_monitoring(self)
        #remote.request_market_data(self.req_id, ticker) # this starts the whole process


    def price_change(self, tickType, price):
        if price <= 0:
            print(f"Returned 0 or under 0 price: '{price}', for ticker {self.req_id_to_stock_ticker_map[reqId]}")
            return

        # bid price = 1
        # ask price = 2
        # last traded price = 4

        if tickType == 2:
            now = time.time()

            self.price_change_times += 1

            self.prices.append(price)
            self.times.append(now)

            if self.last_price is None or self.last_time is None:
                self.last_price = price
                self.last_time = now
                return

            price_line_str = f"P: {price} | LP {self.last_price} | T: {now} | LT: {self.last_time}"
            logging.info(price_line_str)

            delta_time = now - self.last_time
            if delta_time < 0.25:
                delta_time = 0.25

            v = (price - self.last_price) / delta_time
            abs_v = abs(v)

            self.speeds.append(abs_v)

            self.last_price = price
            self.last_time = now

            if self.price_change_times % 25 == 0:
                self.output_chart()
            
            # if len(self.speeds) < HftMonitor.MAX_STORED_SPEEDS:
            #     return

            if len(self.speeds) > HftMonitor.MAX_STORED_SPEEDS:
                self.speeds.pop(0)

            speeds_mean = statistics.mean(self.speeds)
            speed_ratio = abs_v / speeds_mean

            speed_line_str = f"V = {v} | Mean: {speeds_mean} | Speed ratio: {speed_ratio}"
            logging.info(speed_line_str)
            
            # All position querying should be done with self.confirmed_position once the system is executing orders

            # Start position
            if self.position == 0 and speed_ratio > HftMonitor.SPEED_RATIO_THRESHOLD:
                if v > 0:
                    # buy at ask_price - tick
                    # remote.place_order(self, "BUY", 1, price)
                    
                    self.position = 1

                    print(price_line_str)
                    print(speed_line_str)
                    print(f"Bought at: {price}")
                else:
                    # sell at bid price + tick
                    # remote.place_order(self, "SELL", 1, price)

                    self.position = -1

                    print(price_line_str)
                    print(speed_line_str)
                    print(f"Sold at: {price}")
                self.order_price = price

            # Get out of position
            if self.position == 1 and (self.order_price > price or speed_ratio < HftMonitor.SPEED_RATIO_THRESHOLD):
                # remote.place_order(self, "SELL", 1, price, self.active_order_id)
                print(price_line_str)
                print(speed_line_str)
                print(f"Sold back at: {price}")
                print(f"Profit of {price - self.order_price}")
                self.position = 0

            if self.position == -1 and (self.order_price < price or speed_ratio < HftMonitor.SPEED_RATIO_THRESHOLD):
                # remote.place_order(self, "BUY", 1, price, self.active_order_id)
                print(price_line_str)
                print(speed_line_str)
                print(f"Bought back at: {price}")
                print(f"Profit of {self.order_price - price}")
                self.position = 0


    def order_change(self, order_id, status, remaining):
        if status == "Filled":
            self.active_order_id = None
            self.confirmed_position = remaining
            self.confirmed_price = self.order_price
            print(remaining)
        elif status == "Cancelled":
            self.active_order_id = None
        else:
            # get the order id after placing the order so
            # it is managed only on remote
            self.active_order_id = order_id

    # Private

    def active_order(self):
        self.active_order_id is not None


    def output_chart(self):
        line_chart = pygal.Line()
        # line_chart.title = f"{self.ticker1}-{self.ticker2}"
        # line_chart.x_title = f"Ratio: {format(self.stdev_ratio(365), '.2f')} - Corr: {format(self.correlation(365), '.2f')}"
        # x_labels = []
        # for time in range(len(self.times)):
        #     if time % 5 == 0:
        #         x_labels.append(int(time))
        #     else:
        #         x_labels.append('')
        # x_labels.reverse()
        line_chart.x_labels = self.times
        line_chart.add("Prices", self.prices)
        # line_chart.add("Speeds", self.speeds)
        # line_chart.add(self.ticker1, self.parallel_accumulative_percentage_changes(365)[0])
        # line_chart.add(self.ticker2, self.parallel_accumulative_percentage_changes(365)[1])
        # line_chart.show_dots = False
        line_chart.render_to_file(f"/media/ramd/prices_speeds-{int(time.time())}.svg")