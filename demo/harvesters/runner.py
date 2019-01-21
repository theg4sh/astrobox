# -*- coding: utf-8 -*-

import random

from .drone_unit_with_strategies import DroneUnitWithStrategies
from .strategies import StrategyApproach


class RunnerDrone(DroneUnitWithStrategies):
    # TODO этот ничего не собирает? тогда он не нужен
    # TODO если в тестовых целях - назови TestDrone

    def anyAsteroid(self):
        return random.choice(self.scene.asteroids)

    def on_born(self):
        self.append_strategy(StrategyApproach(unit=self, target_point=self.anyAsteroid().coord, distance=0))

    def game_step(self):
        super(RunnerDrone, self).game_step()
        if self.is_strategy_finished():
            self.append_strategy(StrategyApproach(unit=self, target_point=self.anyAsteroid().coord, distance=0))
