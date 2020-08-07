import numpy as np

class Diner:

    def __init__(self, id_diner, id_diner_table, dish_name):
        self.id_diner = id_diner
        self.id_diner_table = id_diner_table
        self.dish_name = dish_name
        self.rating = int(np.random.uniform(-1, 5))
