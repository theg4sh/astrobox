# -*- coding: utf-8 -*-

import math
import random
import sys
from operator import mul

from astrobox.cargo import CargoTransition
from astrobox.guns import Projectile
from astrobox.units import (DroneUnit)
from robogame_engine.geometry import Point, Vector
from robogame_engine.theme import theme
from .drone_unit_with_strategies import DroneUnitWithStrategies
from .strategies import Strategy

# TODO вынести в труперов
from demo.troopers.events import EventUnitDamage


# from robogame_engine.user_interface import Lines

def get_point_on_way_to(target, at_distance=None):
    if at_distance is None:
        at_distance = theme.CARGO_TRANSITION_DISTANCE * 0.9
    r = at_distance
    a = math.atan2(target.x, target.y) + math.pi
    a = math.atan2(target.x, target.y) + math.pi
    x = r * math.sin(a)
    y = r * math.cos(a)
    return Point(target.x + x, target.y + y)


class ReaperState(object):
    def __init__(self, strategy):
        assert (strategy is not None)
        self._strategy = strategy
        self._ttl = 0

    @property
    def strategy(self):
        return self._strategy

    @property
    def unit(self):
        return self._strategy.unit

    @property
    def scene(self):
        return self.unit.scene

    def make_transition(self):
        return None

    def game_step(self):
        self._ttl = self._ttl + 1


class ReaperStateIdle(ReaperState):
    def __init__(self, strategy):
        super(self.__class__, self).__init__(strategy)

    def make_transition(self):
        if not self.unit.is_alive:
            return ReaperStateDead
        if self.unit.have_gun:
            # raise Exception("Guns have not implemented yet")
            pass
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return ReaperStateRunout
        sources = self.scene.asteroids
        sources = sources + [m for m in self.unit.scene.motherships if not m.is_alive and m.team != self.unit.team]
        sources = sources + [d for d in self.unit.scene.drones if not d.is_alive]
        has_sources = len([s for s in sources if s.cargo.payload > 0]) > 0
        if self.unit.cargo.fullness < 0.5:
            if has_sources:
                return ReaperStateHarvest
        if not self.strategy.unit.cargo.is_empty:
            return ReaperStateUnload
        # if not has_sources:
        #    return ReaperStateUnload
        return self.__class__


class ReaperStateDead(ReaperState):
    def make_transition(self):
        return self.__class__


class ReaperStateUnload(ReaperState):
    def __init__(self, strategy):
        self._target = None
        self._target_cargo = None
        self._transition = None
        super(ReaperStateUnload, self).__init__(strategy)

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return ReaperStateRunout
        if self.unit.cargo.is_empty:
            return ReaperStateIdle
        if self._transition and self._transition.is_finished:
            return ReaperStateIdle
        return self.__class__

    def game_step(self):
        super(self.__class__, self).game_step()
        if self._target is None:
            target = self.strategy.getUnloadTarget()
            if target is None:
                target = self.unit.mothership()
            self._target = get_point_on_way_to(target, theme.CARGO_TRANSITION_DISTANCE * 0.9)
            self._target_cargo = target.cargo
            self.unit.move_at(self._target)
        if self._transition:
            self._transition.game_step()
            target = self.strategy.getHarvestTarget()
            if target is None:
                target = self.unit.mothership()
            self.unit.turn_to(target)
        elif self.unit.distance_to(self._target) <= 1.0:
            self._transition = CargoTransition(cargo_from=self.unit.cargo, cargo_to=self._target_cargo)


class ReaperStateHarvest(ReaperState):
    def __init__(self, strategy):
        self._target = None
        self._target_cargo = None
        self._transition = None
        super(ReaperStateHarvest, self).__init__(strategy)

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return ReaperStateRunout
        if self.unit.cargo.is_full:
            return ReaperStateUnload
        if self._target_cargo and self._target_cargo.fullness == 0.0:
            return ReaperStateIdle
        if self._transition and self._transition.is_finished:
            return ReaperStateUnload
        sources = self.scene.asteroids
        sources = sources + [m for m in self.unit.scene.motherships if not m.is_alive and m.team != self.unit.team]
        sources = sources + [d for d in self.unit.scene.drones if not d.is_alive]
        has_sources = len([s for s in sources if s.cargo.payload > 0]) > 0
        if not has_sources:
            if self.unit.cargo.is_empty:
                return ReaperStateIdle
            else:
                return ReaperStateUnload
        return self.__class__

    def game_step(self):
        super(self.__class__, self).game_step()
        if self._target is None:
            target = self.strategy.getHarvestTarget()
            if target is not None:
                self._target = get_point_on_way_to(target, theme.CARGO_TRANSITION_DISTANCE * 0.9)
                self._target_cargo = target.cargo
                self.unit.move_at(self._target.copy())
            elif self._transition is not None:
                return
        if self._transition:
            self._transition.game_step()
            target = self.strategy.getUnloadTarget()
            if target:
                self.unit.turn_to(target)
            else:
                self.unit.turn_to(self.unit.mothership())
        if self._transition is None and self._target and int(self.unit.distance_to(self._target)) <= 1:
            print(u"\u001b[36;1mNew cargo transition: {} -> {}\u001b[0m".format(self._target_cargo.owner.id,
                                                                                self.unit.id))
            self._transition = CargoTransition(cargo_from=self._target_cargo, cargo_to=self.unit.cargo)


class ReaperStateAttack(ReaperState):
    def __init__(self, strategy):
        super(ReaperStateAttack, self).__init__(strategy)

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return ReaperStateRunout
        if len([d for d in self.unit.teammates if d.health < 1.0]) > 0:
            return self.__class__
        return ReaperStateIdle


class ReaperStateRunout(ReaperState):
    def __init__(self, strategy):
        super(ReaperStateRunout, self).__init__(strategy)
        self._target = None
        self._directions = [-25, 25]
        random.shuffle(self._directions)

    def make_transition(self):
        if self.unit.health > 0.75:
            return ReaperStateIdle
        return self.__class__

    def game_step(self):
        # FIXME: when stuck on borders
        if self._target is None:
            v = Vector.from_points(self.unit.coord, self.unit.mothership().coord)
            nextdir = self._directions.pop(0)
            self._directions.append(nextdir)
            v = v.from_direction(v.direction + nextdir, max(125, min(225, v.module * 0.50)))
            target = self.unit.coord + v
            target.x = max(0, min(theme.FIELD_WIDTH, target.x))
            target.y = max(0, min(theme.FIELD_HEIGHT, target.y))
            # target = self.unit.mothership()
            if target is not None:
                self._target = get_point_on_way_to(target, theme.CARGO_TRANSITION_DISTANCE * 0.9)
                self.unit.move_at(self._target.copy())
            self.unit.move_at(self._target)
        elif self.unit.distance_to(self._target) <= 1.0:
            self._target = None


class Dijkstra:
    def __init__(self, unit, points=None):
        self._unit = unit
        self._points = points if points else []
        self._weights = [[0.0 for _ in range(len(self._points))] for _ in range(len(self._points))]
        # self._weights_range = [0.0, 0.0]

    @staticmethod
    def maxint():
        return sys.maxsize

    @property
    def points(self):
        return self._points

    @property
    def weights(self):
        return self._weights

    def update_units(self, func=None):
        if func is None:
            func = lambda a: True
        units = [self._unit.mothership(), ]
        units = units + [a for a in self._unit.scene.asteroids if func(a)]
        units = units + [m for m in self._unit.scene.motherships if
                         not m.is_alive and m.team != self._unit.team and func(m)]
        units = units + [d for d in self._unit.scene.drones if not d.is_alive and func(d)]
        weights = [[0.0 for _ in range(len(units))] for _ in range(len(units))]
        self._weights, self._points = weights, units

    def get_closest(self, unit):
        if not self._unit.is_alive:
            return
        uclosest = self._points[0]
        dclosest = self._points[0].distance_to(unit)
        for u in self._points:
            chkdist = unit.distance_to(u)
            if chkdist < dclosest:
                dclosest = chkdist
                uclosest = u
        return uclosest

    def to_objects(self, indexes):
        return [self._points[n] for n in indexes]

    def calc_weights(self, func=None):
        if not self._unit.is_alive:
            return
        if func is None:
            func = lambda a, b: float(a.distance_to(b))
        # self._weights_range = [self.maxint, 0.0]
        for f, a in enumerate(self._points):
            for t, b in enumerate(self._points):
                if f == t:
                    self._weights[f][t] = float(0.0)
                else:
                    d = float(func(a, b))
                    self._weights[f][t] = d
                    # if self._weights_range[0]>d:
                    #    self._weights_range[0]=d
                    # if self._weights_range[1]<d:
                    #    self._weights_range[1]=d
            # print("%s "%(self._unit.id) + ",".join(["%8.2f"%d for d in self._weights[k]]))
            # print("")

    def find_path(self, pt_from, pt_to, as_objects=False, info=None):
        if not self._unit.is_alive:
            return
        if pt_from not in self._points or pt_to not in self._points:
            print(pt_from, pt_to, self._points)
        fi = self._points.index(pt_from)
        fo = self._points.index(pt_to)
        if fi == fo:
            if as_objects:
                return self.to_objects([fi, ])
            else:
                return [fi, ]

        visited = []
        unvisited = list(range(len(self._points)))

        table = [dict((('cost', self.maxint()), ('prev', -1))) for p in range(len(self._points))]
        table[fi]['cost'] = 0
        root = fi
        while len(unvisited):
            visited.append(root)
            # print(root, fi, fo, root in unvisited)
            unvisited.pop(unvisited.index(root))

            neighbors = [uv for uv in unvisited if self._weights[root][uv] < float("inf")]
            for n in neighbors:
                cost = table[root]['cost'] + self._weights[root][n]
                if table[n]['cost'] > cost:
                    table[n]['cost'] = cost
                    table[n]['prev'] = root
            shortest = self.maxint()
            lastroot = root
            for uv in unvisited:
                if uv == lastroot:
                    continue
                if table[uv]['cost'] < shortest:
                    shortest = table[uv]['cost']
                    root = uv
            # FIXME
            if root == lastroot:
                if unvisited:
                    root = unvisited[0]
        # for k,t in enumerate(table):
        #    print(k, t)
        path = []
        root = fo
        while table[root]['prev'] > -1:
            path.insert(0, root)
            root = table[root]['prev']
        path.insert(0, root)
        # print("Team {}:{} path[{}]: {}".format(self._unit.team, self._unit.id, info if info else "?", path))
        if as_objects:
            return self.to_objects(path)
        else:
            return path


# Pipeline. Bring elerium from far asteroids to nearest.
# One group brings elerium to near asteroids, another one
# brings elerium from near asteroids to the base.
class ReaperStrategy(Strategy):
    _center_of_mass = None
    _distance_limit = 300

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

    def getHarvestTarget(self):
        self.unit.pathfind.update_units(func=lambda a: not a.cargo.is_empty)
        uclosest = self.unit.pathfind.get_closest(self.unit)

        k = math.sqrt(theme.FIELD_HEIGHT * theme.FIELD_HEIGHT + theme.FIELD_WIDTH * theme.FIELD_WIDTH)

        def weight_func(a, b):
            if a.distance_to(b) > ReaperStrategy._distance_limit:
                return float("inf")
            if b.cargo.fullness == 0.0:
                return float("inf")
            coef = [0.5 / k, 1.0]
            values = [float(a.distance_to(b)), b.cargo.fullness]
            return sum(map(mul, coef, values))

        self.unit.pathfind.calc_weights(func=weight_func)
        # TODO: do better choice than a fattest asteroid
        fat_source = [p for p in self.unit.pathfind.points if p != self.unit.mothership()]
        fat_source.sort(key=lambda a: a.cargo.payload / a.scene.max_elerium + self.unit.mothership().distance_to(a) / k,
                        reverse=True)
        if not fat_source:
            return None
        fat_source = fat_source[0]
        self.unit.pathfind.weights

        path = self.unit.pathfind.find_path(self.unit.mothership(), fat_source, as_objects=True, info="harv")
        if path is None:
            return None

        pos = self.data._drones.index(self.unit)
        sz = len(path)
        idx = min(sz, (pos % (sz - 1)) + 1 if sz > 1 else 0)
        # print("Team {}:{} #{},{} path[{}] target #{}: {}".format(self.unit.team, self.unit.id, pos, idx, "harv", idx, path[idx]))
        return path[idx]

    def getUnloadTarget(self):
        if len([a for a in self.unit.scene.asteroids if a.cargo.payload > 0]) == 0:
            return self.unit.mothership()

        self.unit.pathfind_unload.update_units(func=lambda u: u.cargo.fullness < 0.7)

        k = math.sqrt(theme.FIELD_HEIGHT * theme.FIELD_HEIGHT + theme.FIELD_HEIGHT * theme.FIELD_WIDTH)

        def weight_func(a, b):
            if a.distance_to(b) > ReaperStrategy._distance_limit:
                return float("inf")
            dist = a.distance_to(b)
            vdist = 0.0
            if dist != 0.0:
                vdist = float(self.unit.distance_to(self.unit.mothership())) / float(a.distance_to(b))
            coef = [1.0, 1.0]
            values = [vdist, 1.0 - b.cargo.fullness]
            return sum(map(mul, coef, values))

        uclosest = self.unit.pathfind_unload.get_closest(self.unit)
        self.unit.pathfind_unload.calc_weights(func=weight_func)

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
        self.set_fsm_state(ReaperStateIdle(self._strategy))
        self.append_strategy(self._strategy)

    def on_damage(self, victim=None, attacker=None):
        # TODO вынести в труперов
        if victim == self:
            for tm in self.teammates:
                tm.add_event(EventUnitDamage(tm, victim=victim, attacker=attacker))
        else:
            # TODO: react on damaged teammate
            print(victim, attacker)
            pass
