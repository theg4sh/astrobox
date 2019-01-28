# -*- coding: utf-8 -*-

from demo.harvesters.strategies import StrategyHarvesting, DroneUnitWithStrategies


class WorkerDrone(DroneUnitWithStrategies):
    counter_attrs = dict(size=22, position=(75, 135), color=(255, 255, 255))

    def __init__(self, **kwargs):
        super(WorkerDrone, self).__init__(**kwargs)
        self._elerium_stock = None

    @property
    def elerium_stock(self):
        return self._elerium_stock

    def set_elerium_stock(self, stock):
        self._elerium_stock = stock

    def on_born(self):
        super(WorkerDrone, self).on_born()
        self.append_strategy(StrategyHarvesting(unit=self))
