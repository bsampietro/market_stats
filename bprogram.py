import sys

import time
import logging

from util import *
from datahandler import *
from errors import *
from ivrank import *

    
class BProgram:
    def __init__(self, connect:bool):
        self.data_handler = DataHandler(connect)

        # Executing main code
        self.do_stuff()

    def do_stuff(self):
        while True:
            command = input('--> ')
            if command != "":
                command = command.split(" ")
                stock = command[0]
                duration = 365
                if len(command) == 2:
                    duration = command[1]

                if stock == "exit" or stock == "e":
                    self.data_handler.disconnect()
                    # self.data_handler.save()
                    break
                stock = stock.upper()
                
                try:
                    print(stock)

                    iv_rank = IVRank(self.data_handler, stock)
                    show = format(f"IV rank: {format(iv_rank.get_iv_rank_today(), '.2f')}", '<19')
                    show += format(f"IV today: {format(iv_rank.get_iv_today(), '.2f')}", '<20')
                    show += format(f"IV average: {format(iv_rank.average_period_iv(), '.2f')}", '<21')
                    show += format(f"IV min: {format(iv_rank.min_iv(), '.2f')}", '<18')
                    show += format(f"IV max: {format(iv_rank.max_iv(), '.2f')}", '<18')
                    print(show)

                    show = ""
                    for iv in iv_rank.get_period_iv_ranks()[0:15]:
                        show += format(iv, '<10.2f')
                    print(show)
                    
                    # print(list(map((lambda iv: format(iv, '<5.2f')), iv_rank.get_period_iv_ranks()[0:15])))
                    # for iv in iv_rank.get_period_iv_ranks()[0:15]
                    # print(iv_rank.get_period_iv_ranks())


                    # ivr, iv, iv_min, iv_max = self.get_iv_rank(stock, int(duration))
                    # ivr, iv, iv_min, iv_max = format(ivr, '.2f'), format(iv, '.2f'), \
                    #     format(iv_min, '.2f'), format(iv_max, '.2f')
                    
                    # show = format(f"Stock: {stock}", '<18')
                    # show += format(f"IV rank: {ivr}", '<19')
                    # show += format(f"IV today: {iv}", '<20')
                    # show += format(f"IV min: {iv_min}", '<18')
                    # show += format(f"IV max: {iv_max}", '<18')
                    # print(show)
                except GettingInfoError as e:
                    print(e)
                    print("Try again when available message appears...")


if __name__ == "__main__":
   BProgram(sys.argv[0] == "connect")



#time.sleep(60)
#app.disconnect()
