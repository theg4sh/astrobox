# -*- coding: utf-8 -*-

from demo.harvesters.strategies import StrategyHarvesting, StrategyDestroyer, DroneUnitWithStrategies


class DestroyerDrone(DroneUnitWithStrategies):
    _hunters = []

    def __init__(self, **kwargs):
        super(DestroyerDrone, self).__init__(**kwargs)
        self._victim = None
        self._next_victim = None
        self._target_mship = None
        self._elerium_stock = None

    @property
    def elerium_stock(self):
        return self._elerium_stock

    def set_elerium_stock(self, stock):
        self._elerium_stock = stock

    def on_born(self):
        if self.have_gun:
            self.append_strategy(StrategyDestroyer(unit=self))
        else:
            self.append_strategy(StrategyHarvesting(unit=self))

    def game_step(self):
        super(DestroyerDrone, self).game_step()
        if self.have_gun:
            if self.is_strategy_finished():
                self.append_strategy(StrategyHarvesting(unit=self))
