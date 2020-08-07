import numpy as np
from threading import Thread
from time import sleep

from simulation.diner import Diner

class DinerTable(Thread):

    def __init__(self, diner_count, id_diner_table, id_session, id_diner_session, table, restaurant, socket, dishs,
                 attention_time, pay_time, usage_time):
        Thread.__init__(self)
        self.id_session = id_session
        self.id_diner_table = id_diner_table
        self.restaurant = restaurant
        self.diner_list = []
        self.table = table
        self.socket = socket
        self.attention_time = attention_time
        self.pay_time = pay_time
        self.usage_time = usage_time
        for i in range(int(diner_count)):
            id_diner_session += 1
            dish = dishs.pop(int(np.random.random_integers(0, len(dishs)-1)))
            self.diner_list.append(
                Diner(id_diner_session, i + 1, dish.name))

    def run(self):
        sleep(self.usage_time)
        self.table.available = True
        self.restaurant.to_pay(self)
