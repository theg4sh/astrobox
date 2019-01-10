#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import time
import sys
from operator import mul
from robogame_engine import GameObject
from robogame_engine.theme import theme
#from robogame_engine.user_interface import Lines

from robogame_engine.geometry import Point, Vector, normalise_angle

from astrobox.units import (MotherShip, Asteroid, DroneUnit)
from astrobox.cargo import CargoTransition

from demo.drones.drone_unit_with_strategies import DroneUnitWithStrategies

from demo.strategies import Strategy, StrategyApproach, StrategySequence

from demo.events import EventUnitDamage

import pygame
from pygame.draw import line

def getPointOnWayTo(target, at_distance=None):
    if at_distance is None:
        at_distance = theme.CARGO_TRANSITION_DISTANCE * 0.9
    r = at_distance
    a = math.atan2(target.x, target.y) + math.pi
    x = r * math.sin(a)
    y = r * math.cos(a)
    return Point(target.x+x, target.y+y)

class ReaperState(object):
    def __init__(self, strategy):
        assert(strategy is not None)
        self._strategy = strategy

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
        pass

class ReaperStateIdle(ReaperState):
    def __init__(self, strategy):
        super(ReaperStateIdle, self).__init__(strategy);

    def make_transition(self):
        if len([a for a in self.scene.asteroids if a.cargo.payload>0]) > 0:
            return ReaperStateHarvest
        if self.unit.have_gun:
            raise Exception("Guns have not implemented yet")
        if len([a for a in self.scene.asteroids if a.cargo.payload>0]) == 0:
            return ReaperStateUnload
        return self.__class__

class ReaperStateUnload(ReaperState):
    def __init__(self, strategy):
        self._target = None
        self._target_cargo = None
        self._transition = None
        super(ReaperStateUnload, self).__init__(strategy);

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return ReaperStateRunout
        if self.unit.cargo.is_empty:
            return ReaperStateIdle
        if self._transition and self._transition.is_finished:
            return ReaperStateIdle
        return self.__class__

    def game_step(self):
        if self._target is None:
            target = self.strategy.getUnloadTarget()
            if target is None:
                target = self.unit.mothership()
            self._target = getPointOnWayTo(target, theme.CARGO_TRANSITION_DISTANCE * 0.9)
            self._target_cargo = target.cargo
            self.unit.move_at(self._target)
        if self._transition:
            self._transition.game_step()
            target = self.strategy.getHarvestTarget()
            if target is None:
                target = self.unit.mothership()
            self.unit.turn_to( target )
        elif self.unit.distance_to(self._target) <= 1.0:
            self._transition = CargoTransition(cargo_from=self.unit.cargo, cargo_to=self._target_cargo)

class ReaperStateHarvest(ReaperState):
    def __init__(self, strategy):
        self._target = None
        self._target_cargo = None
        self._transition = None
        super(ReaperStateHarvest, self).__init__(strategy);

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return ReaperStateRunout
        if self.unit.cargo.is_full:
            return ReaperStateUnload
        if self._target_cargo and self._target_cargo.fullness == 0.0:
            return ReaperStateIdle
        if self._transition and self._transition.is_finished:
            return ReaperStateUnload
        if len([a for a in self.scene.asteroids if a.cargo.payload>0])==0:
            if self.unit.cargo.is_empty:
                return ReaperStateIdle
            else:
                return ReaperStateUnload
        return self.__class__

    def game_step(self):
        if self._target is None:
            target = self.strategy.getHarvestTarget()
            if target is not None:
                self._target = getPointOnWayTo(target, theme.CARGO_TRANSITION_DISTANCE * 0.9)
                self._target_cargo = target.cargo
                self.unit.move_at(self._target.copy())
            elif self._transition is not None:
                return
        if self._transition:
            self._transition.game_step()
            target = self.strategy.getUnloadTarget()
            if target:
                self.unit.turn_to( target )
            else:
                self.unit.turn_to( self.unit.mothership() )
        if self._transition is None and self._target and int(self.unit.distance_to(self._target)) <= 1:
            print(u"\u001b[36;1mNew cargo transition: {} -> {}\u001b[0m".format( self._target_cargo.owner.id, self.unit.id ))
            self._transition = CargoTransition(cargo_from=self._target_cargo, cargo_to=self.unit.cargo)

class ReaperStateAttack(ReaperState):
    def __init__(self, strategy):
        super(ReaperStateAttack, self).__init__(strategy);

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return ReaperStateRunout
        if len([d for d in self.unit.teammates if d.health < 1.0]) > 0:
            return self.__class__
        return ReaperStateIdle

class ReaperStateRunout(ReaperState):
    def __init__(self, strategy):
        super(ReaperStateRunout, self).__init__(strategy);
        self._target = None

    def make_transition(self):
        if self.unit.health > 0.75:
            return ReaperStateIdle
        return self.__class__

    def game_step(self):
        if self._target is None:
            target = self.unit.mothership()
            if target is not None:
                self._target = getPointOnWayTo(target, theme.CARGO_TRANSITION_DISTANCE * 0.9)
                self.unit.move_at(self._target.copy())
            self.unit.move_at(self._target)

class Dijkstra:
    def __init__(self, unit, points):
        self._unit = unit
        self._points = points
        self._weights = [[0.0 for _ in range(len(points))] for _ in range(len(points))]

    @staticmethod
    def maxint():
        return sys.maxsize

    def get_closest(self, unit):
        uclosest = self._points[0]
        dclosest = self._points[0].distance_to(unit)
        for u in self._points:
            if u.distance_to(unit) < dclosest:
                dclosest = u.distance_to(unit)
                uclosest = u
        return uclosest

    def to_objects(self, indexes):
        return [self._points[n] for n in indexes]

    def calc_weights(self, func=None):
        if func is None:
            func = lambda a,b: float(a.distance_to(b))
        for f,a in enumerate(self._points):
            for t,b in enumerate(self._points):
                if f == t:
                    self._weights[f][t] = float(0.0)
                else:
                    d = float(func(a, b))
                    self._weights[f][t] = d
            #print("%s "%(self._unit.id) + ",".join(["%8.2f"%d for d in self._weights[k]]))
            #print("")

    def find_path(self, pt_from, pt_to, as_objects=False, info=None):
        fi = self._points.index(pt_from)
        fo = self._points.index(pt_to)
        if fi == fo:
            if as_objects:
                return self.to_objects([fi,])
            else:
                return [fi,]

        visited = []
        unvisited = list(range(len(self._points)))

        table = [dict((('cost',self.maxint()), ('prev',-1))) for p in range(len(self._points))]
        table[fi]['cost'] = 0
        root = fi
        while len(unvisited):
            visited.append(root)
            #print(root, fi, fo, root in unvisited)
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
        #for k,t in enumerate(table):
        #    print(k, t)
        path = []
        root = fo
        while table[root]['prev'] > -1:
            path.insert(0, root)
            root = table[root]['prev']
        path.insert(0, root)
        #print("Team {}:{} path[{}]: {}".format(self._unit.team, self._unit.id, info if info else "?", path))
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

    @property
    def data(self):
        if ReaperStrategy._data.get(self.unit.team) is None:
            ReaperStrategy._data[self.unit.team] = ReaperStrategy.Data()
        return ReaperStrategy._data[self.unit.team]

    def __init__(self, **kwargs):
        super(ReaperStrategy, self).__init__(**kwargs)
        self.data._drones.append(self.unit);

        # PathFinder
        units = [self.unit.mothership(),]
        units = units + self.unit.scene.asteroids
        if self.unit.pathfind is None:
            self.unit.pathfind = Dijkstra(self.unit, units[:])
        if self.unit.pathfind_unload is None:
            self.unit.pathfind_unload = Dijkstra(self.unit, units[:])

    def getHarvestTarget(self):
        uclosest = self.unit.pathfind.get_closest(self.unit)

        k = math.sqrt(theme.FIELD_HEIGHT*theme.FIELD_HEIGHT + theme.FIELD_HEIGHT*theme.FIELD_WIDTH)
        # TODO: do better choice than a fattest asteroid
        fat_ast = self.unit.scene.asteroids
        fat_ast.sort(key=lambda a: a.cargo.payload, reverse=True)
        fat_ast = fat_ast[0]

        def weight_func(a, b):
            if a.distance_to(b) > ReaperStrategy._distance_limit:
                return float("inf")
            if b.cargo.fullness == 0.0:
                return float("inf")
            coef =   [k,                       1.0]
            values = [float(a.distance_to(b)), b.cargo.fullness]
            return sum(map(mul, coef, values))
        self.unit.pathfind.calc_weights(func=weight_func)

        path = self.unit.pathfind.find_path(self.unit.mothership(), fat_ast, as_objects=True, info="harv")

        pos = self.data._drones.index(self.unit)
        sz = len(path)
        idx = (pos % (sz-1)) + 1 if sz>1 else 0
        #print("Team {}:{} #{},{} path[{}] target #{}: {}".format(self.unit.team, self.unit.id, pos, idx, "harv", idx, path[idx]))
        return path[idx]

    def getUnloadTarget(self):
        if len([a for a in self.unit.scene.asteroids if a.cargo.payload>0])==0:
            return self.unit.mothership()
        k = math.sqrt(theme.FIELD_HEIGHT*theme.FIELD_HEIGHT + theme.FIELD_HEIGHT*theme.FIELD_WIDTH)
        def weight_func(a, b):
            if a.distance_to(b) > ReaperStrategy._distance_limit:
                return float("inf")
            coef =   [1.0, 1.0]
            values = [float(self.unit.distance_to(self.unit.mothership()))/float(a.distance_to(b)), 1.0-b.cargo.fullness]
            return sum(map(mul, coef, values))
        self.unit.pathfind_unload.calc_weights(func=weight_func)

        uclosest = self.unit.pathfind_unload.get_closest(self.unit)
        path_unload = self.unit.pathfind_unload.find_path(uclosest, self.unit.mothership(), as_objects=True, info="unld")

        pos = self.data._drones.index(self.unit)
        sz = len(path_unload)
        idx = (pos % (sz-1)) + 1 if sz>1 else 0
        #print("Team {}:{} #{},{} path[{}] target #{}: {}".format(self.unit.team, self.unit.id, pos, idx, "unld", idx, path_unload[idx]))
        return path_unload[-idx]

    def _find_closest_elerium(self, unit, units):
        our_mothership = self.unit.mothership()
        enemy_motherships = [m for m in self.unit.scene.motherships if m.id != our_mothership.id]
        asteroids = []
        for a in units:
            dist_to_a = unit.distance_to(a)
            safepoints = min([dist_to_a/m.distance_to(a) for m in enemy_motherships])
            asteroids.append((safepoints, a))
        asteroids.sort(key=lambda o: o[0])
        return asteroids

    @property
    def is_finished(self):
        return False

    @property
    def fsm_state(self):
        return self.unit.fsm_state

    def game_step(self, **kwargs):
        super(ReaperStrategy, self).game_step(**kwargs)

        newState = self.fsm_state.make_transition()
        if newState != self.fsm_state.__class__:
            self.unit.set_fsm_state( newState(self) )

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
        self.set_fsm_state( ReaperStateIdle(self._strategy) )
        self.append_strategy(self._strategy)

    def on_damage(self, victim=None, attacker=None):
        if victim == self:
            for tm in self.teammates:
                tm.add_event(EventUnitDamage(tm, victim=victim, attacker=attacker))
        else:
            # TODO: react on damaged teammate
            print(victim, attacker)
            pass

