# -*- coding: utf-8 -*-

import random

from demo.drones.worker_drone import WorkerDrone


class GreedyDrone(WorkerDrone):

    def __init__(self, **kwargs):
        super(GreedyDrone, self).__init__(**kwargs)

    def get_nearest_elerium_stock(self):
        elerium_stocks = [es for es in self.scene.elerium_stocks if es.cargo.payload > 0]
        for drone in self.teammates:
            if drone.elerium_stock is not None and \
                    not drone.cargo.is_full and \
                    drone.elerium_stock in elerium_stocks:
                elerium_stocks.remove(drone.elerium_stock)

        if not elerium_stocks:
            return None
        # Берем наибольшее кол-во elerium-а, что сможем унести, из ближайшего
        elerium_stocks = sorted(elerium_stocks, key=lambda x: x.distance_to(self))
        nearest_stock = None
        max_elerium = 0
        for stock in elerium_stocks:
            if stock.cargo.payload >= self.cargo.free_space:
                return stock
            if stock.cargo.payload > max_elerium:
                nearest_stock = stock
                max_elerium = stock.cargo.payload
        if nearest_stock:
            return nearest_stock
        return random.choice(elerium_stocks)
