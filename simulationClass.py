import random
from threading import Thread
from time import sleep
import operator

restaurant = None

class MyThread(Thread):
    def __init__(self, _id, time, table, restaurant):
        Thread.__init__(self)
        self.restaurant = restaurant
        self.time = time
        self._id = _id
        self.table_name = table

    def run(self):
        self.restaurant.socket.emit('user_in', {'_id': self._id, 'time_in': self.time, 'table': self.table_name})
        sleep(self.time)
        self.restaurant.user_action(self._id, self.table_name)

class MyTimer(Thread):
    def __init__(self, time, restaurant):
        Thread.__init__(self)
        self.restaurant = restaurant
        self.time = time * 60
        self.state = True
        self.pause = False

    def run(self):
        while self.state:
            if not self.pause:
                sleep(self.time)
                self.restaurant.send_hour()
            else:
                sleep(10)

class Restaurant():

    def __init__(self, hour, socket_io):
        self.hours = hour
        self.socket = socket_io
        self.period = 0
        self.users = 0
        self.tables = 2
        self.table_list = []
        self.user_list = []
        self.period_list = []
        self.count_periods = 0
        self.count_users = 0
        self.count_hours = 0
        self.time_in = 0
        self.dishs = {}
        self.dishs_prom = {}
        self.dishs_count = {}
        self.dishs_name = ['Bandeja Paisa', 'Cuchuco de Trigo con Espinazo', 'Paella a la Valenciana',
                           'Arroz con Pollo']
        self.pause = False
        self.threads = []
        for name in self.dishs_name:
            self.dishs.update([(name, [])])
            self.dishs_prom.update([(name, 0)])
            self.dishs_count.update([(name, 0)])
        self.state = True
        for i in range(self.tables):
            self.table_list.append({'name': 'Mesa ' + str(i + 1), 'state': True})
        self.timer_res = MyTimer(1, self)
        self.timer_res.start()
        self.assign_period()

    def assign_period(self):
        self.socket.emit('hours', sum(i for i in self.period_list))
        if self.hours < 1:
            print('Listo')
            self.state = False
            self.timer_res.state = False
            self.socket.emit('end_simulation', 'ok')
        else:
            if self.hours < 8:
                self.period = self.hours
                self.hours = 0
                self.users = int(random.randint(50, 180)/8 * self.period)
            else:
                if self.hours < 11:
                    self.period = self.hours
                    self.hours = 0
                else:
                    self.period = random.randint(8, 10)
                    self.hours -= self.period
                self.users = random.randint(50, 180)
            self.time_in = ((self.period*60) / int(self.users / self.tables))
            self.period_list.append(self.period)
            print(str(self.users) + ' ' + str(self.period) + ' ' + str(self.time_in))
            self.count_periods += 1
            self.count_users = 0
            self.socket.emit('period', self.count_periods)
            self.assign_user()

    def assign_user(self):
        flag = True
        for i in self.table_list:
            if not i['state']:
                flag = False
        if self.users < 1 and flag:
            self.assign_period()
        elif 0 < self.users:
            for i in self.table_list:
                if i['state'] and 0 < self.users:
                    i['state'] = False
                    self.count_users += 1
                    self.users -= 1
                    thread = MyThread(self.count_users, self.time_in, i['name'], self)
                    if self.pause:
                        self.threads.append(thread)
                    else:
                        self.socket.emit('count_users', self.count_users)
                        thread.start()

    def user_action(self, _id, table):
        dish = random.choice(self.dishs_name)
        calification = random.randint(0, 5) if random.choice([True, False]) else -1
        self.dishs_count[dish] += 1
        if calification != -1:
            self.dishs[dish].append(calification)
            self.dishs_prom[dish] = int((sum(n for n in self.dishs[dish])) / len(self.dishs[dish]))
        self.user_list.append([_id, self.count_periods, dish, table, calification])
        for i in self.table_list:
            if i['name'] == table:
                i['state'] = True
                break
        user = [_id, self.count_periods, dish, table, calification]
        self.user_list.append(user)
        self.socket.emit('user', user)
        self.socket.emit('dishs_count', sorted(self.dishs_count.items(), key=operator.itemgetter(1), reverse=True))
        self.socket.emit('dishs_prom', sorted(self.dishs_prom.items(), key=operator.itemgetter(1), reverse=True))
        self.assign_user()

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
        for t in self.threads:
            self.socket.emit('count_users', t._id)
            t.start()
        self.threads = []

def start_simulation_res(hours, socketio):
    global restaurant
    restaurant = Restaurant(hours, socketio)
    return restaurant