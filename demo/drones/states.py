import math
from astrobox.cargo import CargoTransition

from robogame_engine.geometry import Point, Vector
from robogame_engine.theme import theme

def get_point_on_way_to(target, at_distance=None):
    if at_distance is None:
        at_distance = theme.CARGO_TRANSITION_DISTANCE * 0.9
    r = at_distance
    a = math.atan2(target.x, target.y) + math.pi
    a = math.atan2(target.x, target.y) + math.pi
    x = r * math.sin(a)
    y = r * math.cos(a)
    return Point(target.x + x, target.y + y)


class DroneState(object):
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


class DroneStateIdle(DroneState):
    def __init__(self, strategy):
        super(self.__class__, self).__init__(strategy)

    def make_transition(self):
        if not self.unit.is_alive:
            return DroneStateDead
        if self.unit.have_gun:
            # raise Exception("Guns have not implemented yet")
            pass
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return DroneStateRunout
        sources = self.scene.asteroids
        sources = sources + [m for m in self.unit.scene.motherships if not m.is_alive and m.team != self.unit.team]
        sources = sources + [d for d in self.unit.scene.drones if not d.is_alive]
        has_sources = len([s for s in sources if s.cargo.payload > 0]) > 0
        if self.unit.cargo.fullness < 0.5:
            if has_sources:
                return DroneStateHarvest
        if not self.strategy.unit.cargo.is_empty:
            return DroneStateUnload
        # if not has_sources:
        #    return DroneStateUnload
        return self.__class__


class DroneStateDead(DroneState):
    def make_transition(self):
        return self.__class__


class DroneStateUnload(DroneState):
    def __init__(self, strategy):
        self._target = None
        self._target_cargo = None
        self._transition = None
        super(DroneStateUnload, self).__init__(strategy)

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return DroneStateRunout
        if self.unit.cargo.is_empty:
            return DroneStateIdle
        if self._transition and self._transition.is_finished:
            return DroneStateIdle
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


class DroneStateHarvest(DroneState):
    def __init__(self, strategy):
        self._target = None
        self._target_cargo = None
        self._transition = None
        super(DroneStateHarvest, self).__init__(strategy)

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return DroneStateRunout
        if self.unit.cargo.is_full:
            return DroneStateUnload
        if self._target_cargo and self._target_cargo.fullness == 0.0:
            return DroneStateIdle
        if self._transition and self._transition.is_finished:
            return DroneStateUnload
        sources = self.scene.asteroids
        sources = sources + [m for m in self.unit.scene.motherships if not m.is_alive and m.team != self.unit.team]
        sources = sources + [d for d in self.unit.scene.drones if not d.is_alive]
        has_sources = len([s for s in sources if s.cargo.payload > 0]) > 0
        if not has_sources:
            if self.unit.cargo.is_empty:
                return DroneStateIdle
            else:
                return DroneStateUnload
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


class DroneStateAttack(DroneState):
    def __init__(self, strategy):
        super(DroneStateAttack, self).__init__(strategy)

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return DroneStateRunout
        if len([d for d in self.unit.teammates if d.health < 1.0]) > 0:
            return self.__class__
        return DroneStateIdle


class DroneStateRunout(DroneState):
    def __init__(self, strategy):
        super(DroneStateRunout, self).__init__(strategy)
        self._target = None
        self._directions = [-25, 25]
        random.shuffle(self._directions)

    def make_transition(self):
        if self.unit.health > 0.75:
            return DroneStateIdle
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


