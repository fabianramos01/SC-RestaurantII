from threading import Thread
from time import sleep


class Waiter(Thread):

    def __init__(self, id_waiter, restaurant):
        Thread.__init__(self)
        self.id_waiter = id_waiter
        self.available = True
        self.diner_table = None
        self.restaurant = restaurant

    def set_diner_table(self, diner_table):
        self.available = False
        self.diner_table = diner_table

    def run(self):
        sleep(self.diner_table.attention_time)
        self.available = True
        self.diner_table.run()
        self.diner_table = None
        self.restaurant.assign_waiter()
