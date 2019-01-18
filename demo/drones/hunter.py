# -*- coding: utf-8 -*-

from astrobox.utils import nearest_angle_distance
from demo.drones.greedy import GreedyDrone
from demo.drones.worker import WorkerDrone
from demo.strategies import StrategyHarvesting, StrategyHunting
from robogame_engine.geometry import Vector


class HunterDrone(GreedyDrone):
    _hunters = []

    def __init__(self, **kwargs):
        super(HunterDrone, self).__init__(**kwargs)
        self._hunting_strategy = None
        self._approach_strategy = None
        self._victim = None
        # self._no_victim_strategy = False
        self._victim_stamp = 0
        self._next_victim = None
        self.substrategy = None

    @property
    def victim(self):
        return self._victim

    def on_born(self):
        super(WorkerDrone, self).on_born()
        if self.have_gun:
            self._hunting_strategy = StrategyHunting.getTeamStrategy(self.team, self)
        else:
            self.append_strategy(StrategyHarvesting(unit=self))

    def on_stop(self):
        pass

    def get_nearest_elerium_stock(self):
        # Сперва сбор элериума с жертв
        elerium_stocks = [drone for drone in self.unit.scene.drones if not drone.is_alive and drone.cargo.payload > 0]
        for drone in self.unit.teammates:
            if drone.elerium_stock is not None and \
                    not drone.cargo.is_full and \
                    drone.elerium_stock in elerium_stocks:
                elerium_stocks.remove(drone.elerium_stock)
        if elerium_stocks:
            elerium_stocks = sorted(elerium_stocks, key=lambda x: x.distance_to(self))
            return elerium_stocks[0]

        # Потом с астероидов
        elerium_stocks = [asteriod for asteriod in self.unit.scene.asteroids if asteriod.cargo.payload > 0]
        for drone in self.unit.teammates:
            if drone.elerium_stock is not None and \
                    not drone.cargo.is_full and \
                    drone.elerium_stock in elerium_stocks:
                elerium_stocks.remove(drone.elerium_stock)
        if not elerium_stocks:
            return None
        elerium_stocks = sorted(elerium_stocks, key=lambda x: x.distance_to(self))
        return elerium_stocks[0]

    def set_victim(self, victim):
        self._next_victim = None
        self._victim = victim
        self._victim_stamp = 0
        if not self.substrategy.is_finished:
            self.stop()
            self.state.stop()
        self.substrategy.reset()
        return victim.coord.copy()

    @property
    def is_unloading(self):
        return self.cargo.is_full or (self.substrategy is not None
                                      and self.substrategy.current_strategy_id == "approach&unload")

    def game_step(self):
        if not self.have_gun:
            super(HunterDrone, self).game_step()
            return

        self.native_game_step()
        if self._hunting_strategy is None:
            return
        self._hunting_strategy.game_step(self)
        if self.victim is not None:
            vector = Vector.from_points(self.coord, self.victim.coord,
                                        module=self.gun.shot_distance)
            if int(self.distance_to(self.victim)) < 1 or (
                    self.distance_to(self.victim) < vector.module
                    and abs(nearest_angle_distance(vector.direction, self.direction)) < 7
            ):
                self.gun.shot(self.victim)
        else:
            enemies = [enemy for enemy in self.scene.drones
                       if enemy.team != self.team and enemy.is_alive and
                       enemy.distance_to(self) < self.gun.shot_distance]
            enemie = sorted(enemies, key=lambda x: -x.cargo.payload)
            for enemy in enemies:
                vector = Vector.from_points(self.coord, enemy.coord)
                if abs(nearest_angle_distance(vector.direction, self.direction)) < 7:
                    self.gun.shot(enemy)
                    break
