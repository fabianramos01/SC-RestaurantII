import numpy as np
from threading import Thread
from time import sleep
from simulation.atm import ATM
from simulation.dinerTable import DinerTable
from simulation.waiter import Waiter
from simulation.table import Table
from simulation.dish import Dish

restaurant = None

class MyTimer(Thread):

    def __init__(self, time, restaurant_n):
        Thread.__init__(self)
        self.restaurant_n = restaurant_n
        self.time = time * 60
        self.state = True
        self.pause = False

    def run(self):
        while self.state:
            if not self.pause:
                sleep(self.time)
                self.restaurant_n.send_hour()
            else:
                sleep(10)

class DinerArriveTimer(Thread):

    def __init__(self, time, restaurant_n, diners):
        Thread.__init__(self)
        self.restaurant_n = restaurant_n
        self.time = time
        self.diners = diners
        self.state = True
        self.pause = False
        self.run()

    def run(self):
        while self.state:
            if not self.pause:
                sleep(self.time)
                self.restaurant_n.add_diner()
                self.state = True if 0 < self.diners else False
            else:
                sleep(5)

class Restaurant:

    def __init__(self, hour, socket_io):
        self.hours = hour
        self.socket = socket_io
        self.period = 0
        self.users = 0
        self.tables = 5
        self.waiters = 2
        self.table_list = []
        self.diner_table_list = []
        self.waiter_list = []
        self.period_list = []
        self.user_list = []
        self.count_periods = 0
        self.atm = ATM(self)
        self.count_users = 0
        self.count_diner_table = 0
        self.count_hours = 0
        self.time_in = 0
        self.diner_timer = None
        self.dishs = []
        self.dishs_options = [{'name': 'Bandeja Paisa', 'price': 18000},
                              {'name': 'Cuchuco de Trigo con Espinazo', 'price': 12000},
                              {'name': 'Paella a la Valenciana', 'price': 20000},
                              {'name': 'Arroz con Pollo', 'price': 17000}]
        self.pause = False
        self.diner_wait_list = []
        self.state = True
        self.init_vars()
        self.timer_res = MyTimer(1, self)
        self.timer_res.start()
        self.assign_period()

    def init_vars(self):
        for item in self.dishs_options:
            self.dishs.append(Dish(item['name'], item['price']))
        for i in range(self.tables):
            self.table_list.append(Table('Mesa ' + str(i + 1), True))
        for i in range(self.waiters):
            self.waiter_list.append(Waiter('Mesero ' + str(i + 1), self))

    def assign_period(self):
        self.socket.emit('hours', sum(i for i in self.period_list))
        if self.hours < 1:
            print('Listo')
            self.state = False
            self.timer_res.state = False
            self.atm.state = False
            self.socket.emit('end_simulation', 'ok')
        else:
            if self.hours < 10:
                self.period = self.hours
                self.hours = 0
                self.users = int(np.random.randint(200, 300) / 8 * self.period)
            else:
                if self.hours < 13:
                    self.period = self.hours
                    self.hours = 0
                else:
                    self.period = np.random.randint(10, 12)
                    self.hours -= self.period
                self.users = np.random.randint(200, 300)
            self.time_in = ((self.period * 60) / int(self.users / self.tables))
            self.period_list.append(self.period)
            print(str(self.users) + ' ' + str(self.period) + ' ' + str(self.time_in))
            self.count_periods += 1
            self.count_users = 0
            self.diner_timer = DinerArriveTimer(5, self, self.users)
            self.socket.emit('period', self.count_periods)

    def add_diner(self):
        for i in range(4):
            quantity = np.random.randint(1, 3)
            self.users -= quantity
            self.diner_wait_list.append(quantity)
        self.socket.emit('wait_queue', {'count': int(np.sum(self.diner_wait_list))})
        self.assign_table()

    def assign_table(self):
        if self.table_available():
            for i in self.table_list:
                if i.available and 0 < len(self.diner_wait_list):
                    i.available = False
                    diner_count = self.diner_wait_list.pop(0)
                    self.socket.emit('wait_queue', int(np.sum(self.diner_wait_list)))
                    self.count_diner_table += 1
                    diner_table = DinerTable(diner_count, self.count_diner_table, self.period, self.count_users,
                                             i, self, self.socket, self.dishs.copy(),
                                             self.time_in, self.time_in, self.time_in)
                    self.count_users += diner_count
                    self.socket.emit('count_users', self.count_users)
                    self.diner_table_list.append(diner_table)
                    self.socket.emit('diner_table',
                                     {'table': diner_table.table.name, 'users': len(diner_table.diner_list),
                                      'attention_time': diner_table.attention_time, 'pay_time': diner_table.pay_time,
                                        'usage_time': diner_table.usage_time})
                    self.assign_waiter()

    def assign_waiter(self):
        waiter = self.available_waiter()
        if waiter is not None and len(self.diner_table_list):
            waiter.set_diner_table(self.diner_table_list.pop(0))
            self.socket.emit('waiter_table', {'waiter': waiter.id_waiter, 'table': waiter.diner_table.table.name})
            waiter.run()

    def dinner_not_in_restaurant(self):
        for i in self.table_list:
            if not i.available:
                return False
        for w in self.waiter_list:
            if w.diner_table is not None:
                return False
        return False if 0 < len(self.atm.diner_table) and 0 < len(self.diner_wait_list) else True

    def table_available(self):
        for i in self.table_list:
            if i.available:
                return True

    def available_waiter(self):
        for i in self.waiter_list:
            if i.available:
                return i
        return None

    def to_pay(self, diner_table):
        diner_table.table.available = True
        self.assign_table()
        self.atm.add_diner_table(diner_table)

    def add_table_list_registry(self, diner_table):
        for diner in diner_table.diner_list:
            user = [diner_table.id_session, diner_table.id_diner_table, diner_table.table.name, diner.id_diner,
                    diner.id_diner_table, diner.dish_name, diner.rating]
            self.socket.emit('user', user)
            self.user_list.append(user)
            for dish in self.dishs:
                if dish.name == diner.dish_name:
                    dish.add_count()
                    if -1 < diner.rating:
                        dish.add_rating(diner.rating)
        self.socket.emit('dishs_prom', sorted(self.dishs, key=lambda Dish: dish.get_rating_prom(), reverse=True))
        self.socket.emit('dishs_count', sorted(self.dishs, key=lambda Dish: dish.count, reverse=True))
        if self.dinner_not_in_restaurant():
            self.assign_period()

    def send_hour(self):
        self.count_hours += 1
        self.socket.emit('hours', self.count_hours)

    def pause_simulation(self):
        self.state = False
        self.pause = True
        self.timer_res.pause = True

    def play_simulation(self):
        self.state = True
        self.pause = False
        self.timer_res.pause = False
        self.diner_timer.pause = False
        for t in self.diner_table_list:
            t.start()

def start_simulation_res(hours, socketio):
    global restaurant
    restaurant = Restaurant(hours, socketio)
    return restaurant
