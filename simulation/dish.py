import numpy as np

class Dish:

    def __init__(self, name, price):
        self.name = name
        self.price = price
        self.rating = []
        self.count = 0

    def add_count(self):
        self.count += 1

    def add_rating(self, rating_value):
        self.rating.append(rating_value)

    def get_rating_prom(self):
        return np.sum(self.rating)/len(self.rating)