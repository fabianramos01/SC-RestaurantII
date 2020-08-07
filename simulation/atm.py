from threading import Thread
from time import sleep

class ATM(Thread):

    def __init__(self, restaurant):
        Thread.__init__(self)
        self.restaurant = restaurant
        self.state = True
        self.pause = False
        self.diner_table = []

    def add_diner_table(self, diner_table_item):
        self.diner_table.append(diner_table_item)
        self.restaurant.socket.emit('pay_queue', len(self.diner_table))

    def run(self):
        while self.state:
            if not self.pause:
                if 0 < len(self.diner_table):
                    diner_item = self.diner_table.pop(0)
                    self.restaurant.socket.emit('pay_queue', len(self.diner_table))
                    self.restaurant.socket.emit('pay_attention', diner_item)
                    sleep(diner_item.pay_time)
                    self.restaurant.add_table_list_registry(diner_item)
                else:
                    sleep(3)
            else:
                sleep(10)