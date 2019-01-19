# -*- coding: utf-8 -*-

import math
import random
from operator import mul

from astrobox.guns import Projectile
from astrobox.units import (DroneUnit)
from demo.drones.drone_unit_with_strategies import DroneUnitWithStrategies
from demo.events import EventUnitDamage
from demo.strategies import Strategy
from robogame_engine.geometry import Point, Vector
from robogame_engine.theme import theme

from demo.drones.dijkstra import Dijkstra
from demo.drones.states import DroneStateIdle

# from robogame_engine.user_interface import Lines

# Pipeline. Bring elerium from far asteroids to nearest.
# One group brings elerium to near asteroids, another one
# brings elerium from near asteroids to the base.
class ReaperStrategy(Strategy):
    _center_of_mass = None
    _distance_limit = 300

    # Data contains information for team. It usefull when
    # have more than one drone with that strategy
    class Data:
        def __init__(self):
            self._path = []
            self._path_unload = []
            self._drones = []

    _data = {}
    _test_unit = None

    @property
    def data(self):
        if ReaperStrategy._data.get(self.unit.team) is None:
            ReaperStrategy._data[self.unit.team] = ReaperStrategy.Data()
        return ReaperStrategy._data[self.unit.team]

    def __init__(self, **kwargs):
        super(ReaperStrategy, self).__init__(**kwargs)
        self.data._drones.append(self.unit)

        # PathFinder
        if self.unit.pathfind is None:
            self.unit.pathfind = Dijkstra(self.unit)
        if self.unit.pathfind_unload is None:
            self.unit.pathfind_unload = Dijkstra(self.unit)
        self.data._enemy_drones = [d for d in self.unit.scene.drones if d.team != self.unit.team]


    def weight_harvest_func(self, a, b):
        dist = a.distance_to(b)
        if dist > ReaperStrategy._distance_limit:
            return float("inf")
        if b.cargo.fullness == 0.0:
            return float("inf")
        k = math.sqrt(theme.FIELD_HEIGHT * theme.FIELD_HEIGHT + theme.FIELD_WIDTH * theme.FIELD_WIDTH)
        coef = [0.5 / k, 1.0]
        values = [dist, b.cargo.fullness]
        return sum(map(mul, coef, values))

    def getHarvestTarget(self):
        self.unit.pathfind.update_units(func=lambda a: not a.cargo.is_empty)
        uclosest = self.unit.pathfind.get_closest(self.unit)


        self.unit.pathfind.calc_weights(func=self.weight_harvest_func)
        # TODO: do better choice than a fattest asteroid
        fat_source = [p for p in self.unit.pathfind.points if p != self.unit.mothership()]
        k = math.sqrt(theme.FIELD_HEIGHT * theme.FIELD_HEIGHT + theme.FIELD_HEIGHT * theme.FIELD_WIDTH)
        fat_source.sort(key=lambda a: a.cargo.payload / a.scene.max_elerium + self.unit.mothership().distance_to(a) / k,
                        reverse=True)
        if not fat_source:
            return None
        fat_source = fat_source[0]
        #self.unit.pathfind.weights

        path = self.unit.pathfind.find_path(self.unit.mothership(), fat_source, as_objects=True, info="harv")
        if path is None:
            return None

        pos = self.data._drones.index(self.unit)
        sz = len(path)
        idx = min(sz, (pos % (sz - 1)) + 1 if sz > 1 else 0)
        # print("Team {}:{} #{},{} path[{}] target #{}: {}".format(self.unit.team, self.unit.id, pos, idx, "harv", idx, path[idx]))
        return path[idx]

    def weight_unload_func(self, a, b):
        dist = a.distance_to(b)
        if dist > ReaperStrategy._distance_limit:
            return float("inf")
        vdist = 0.0
        if dist != 0.0:
            vdist = float(self.unit.distance_to(self.unit.mothership())) / dist
        coef = [1.0, 1.0]
        values = [vdist, 1.0 - b.cargo.fullness]
        return sum(map(mul, coef, values))

    def getUnloadTarget(self):
        if len([a for a in self.unit.scene.asteroids if a.cargo.payload > 0]) == 0:
            return self.unit.mothership()

        self.unit.pathfind_unload.update_units(func=lambda u: u.cargo.fullness < 0.7)

        uclosest = self.unit.pathfind_unload.get_closest(self.unit)
        self.unit.pathfind_unload.calc_weights(func=self.weight_unload_func)

        path_unload = self.unit.pathfind_unload.find_path(uclosest, self.unit.mothership(), as_objects=True,
                                                          info="unld")
        if path_unload is None:
            return None

        pos = self.data._drones.index(self.unit)
        sz = len(path_unload)
        # Возврат, проекция бинарного поиска в отношении path-finding
        idx = min(len(path_unload) - 1, int(len(path_unload) / 2) + 1) if sz > 1 else 0
        # print("Team {}:{} #{},{} path[{}] target #{}: {}".format(self.unit.team, self.unit.id, pos, idx, "unld", idx, path_unload[idx]))
        return path_unload[-idx]

    @property
    def is_finished(self):
        return False

    @property
    def fsm_state(self):
        return self.unit.fsm_state

    def gun_fire(self):
        if not self.unit.have_gun:
            return

        def is_on_straight(b):
            v = Vector.from_points(self.unit.coord, b.coord)
            v.rotate(-self.unit.direction)
            if v.direction < 90.0:
                a = v.direction / 180.0 * math.pi
                limit = (DroneUnit.radius + Projectile.radius)
                if self.unit.team == b.team:
                    limit *= 1.5
                return math.fabs(self.unit.distance_to(b) * math.sin(a)) < limit
            return False

        if self._test_unit is None:
            test = [d for d in self.unit.scene.drones if self.unit.team != d.team][0]
            self._test_unit = [self.unit.id, test.id]

        def target_drones():
            for d in self.unit.scene.drones:
                if not d.is_alive or d.id == self.unit.id:
                    continue
                if self.unit.distance_to(d) > theme.PROJECTILE_TTL * theme.PROJECTILE_SPEED * 0.8:
                    continue
                if is_on_straight(d):
                    yield d

        targets = list(target_drones())
        if targets:
            if is_on_straight(self.unit.mothership()):
                targets.append(self.unit.mothership())
            targets.sort(key=lambda t: self.unit.distance_to(t))

            # print("Team {}:{}\t{} {}".format(self.unit.team, self.unit.id, len(targets), len(teammates)))
            # print("Team {}:{}\t{}".format(self.unit.team, self.unit.id, targets))
            if self.unit.team != targets[0].team:
                # print("Team {}:{} {}".format(self.unit.team, self.unit.id, targets))
                self.unit.gun.shot([d for d in targets if d.team != self.unit.team][0])

    def game_step(self, **kwargs):
        super(ReaperStrategy, self).game_step(**kwargs)

        self.gun_fire()

        newState = self.fsm_state.make_transition()
        if newState != self.fsm_state.__class__:
            self.unit.set_fsm_state(newState(self))

        if self.unit.fsm_state:
            self.unit.fsm_state.game_step()


class ReaperDrone(DroneUnitWithStrategies):
    def __init__(self, **kwargs):
        super(ReaperDrone, self).__init__(**kwargs)
        self.pathfind = None
        self.pathfind_unload = None
        self.__fsm_state = None
        self._elerium_stock = None
        self._strategy = None

    @property
    def fsm_state(self):
        return self.__fsm_state

    def set_fsm_state(self, new_fsm_state):
        if new_fsm_state.__class__ != self.__fsm_state.__class__:
            # TODO заюзай termcolor - делает тоже самое, но проще
            print(u"\u001b[34;1m#{}\t{}\t{} [{}] -> [{}]\u001b[0m".format(self.id, self,
                                                                          "new fsm state transition",
                                                                          self.__fsm_state.__class__.__name__[11:],
                                                                          new_fsm_state.__class__.__name__[11:]))
        self.__fsm_state = new_fsm_state

    @property
    def elerium_stock(self):
        return self._elerium_stock

    def set_elerium_stock(self, stock):
        self._elerium_stock = stock

    def on_born(self):
        super(ReaperDrone, self).on_born()
        self._strategy = ReaperStrategy(unit=self)
        self.set_fsm_state(DroneStateIdle(self._strategy))
        self.append_strategy(self._strategy)

    def on_damage(self, victim=None, attacker=None):
        if victim == self:
            for tm in self.teammates:
                tm.add_event(EventUnitDamage(tm, victim=victim, attacker=attacker))
        else:
            # TODO: react on damaged teammate
            print(victim, attacker)
            pass
