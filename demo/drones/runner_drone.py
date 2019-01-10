from demo.drones.drone_unit_with_strategies import DroneUnitWithStrategies

from demo.strategies import StrategyApproach

class RunnerDrone(DroneUnitWithStrategies):

    def anyAsteroid(self):
        return random.choice(self.scene.asteroids)

    def on_born(self):
        self.append_strategy(StrategyApproach(unit=self, target_point=self.anyAsteroid().coord, distance=0))

    def game_step(self):
        super(RunnerDrone, self).game_step()
        if self.is_strategy_finished():
            self.append_strategy(StrategyApproach(unit=self, target_point=self.anyAsteroid().coord, distance=0))

