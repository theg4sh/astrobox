import math
import random
from astrobox.cargo import CargoTransition

from robogame_engine.geometry import Point, Vector
from robogame_engine.theme import theme
from astrobox.guns import Projectile

# Используем менее затратный алгоритм, вместо
# использования преобразований вычислений из Vector
def is_on_straight(frame_idx, a, b, distance_limit=None):
    if not distance_limit:
        distance_limit = theme.PROJECTILE_RANGE * 0.8

    # Rotation matrix
    dx = (b.x - a.x)
    dy = (b.y - a.y)
    angle = a.direction / 180.0 * math.pi
    cosphi = math.cos(angle)
    sinphi = math.sin(angle)

    # CCW rotation
    rx = (+ dx * cosphi + dy * sinphi)
    if rx < 0.0:
        return False
    if rx > distance_limit:
        return False
    # Simple detect
    ry = (- dx * sinphi + dy * cosphi)
    if math.fabs(ry) < 0.01:
        return True

    ylimit = (b.__class__.radius + Projectile.radius)
    if a.team == b.team:
        ylimit *= 1.5
    # Triangle similarity rule
    # x1 / x2 = y1 / y2 = d1 / d2
    xk = distance_limit / rx
    # yk = ry * xk
    return math.fabs(ry * xk) < ylimit

def get_point_on_way_to(unit, target, at_distance=None):
    if at_distance is None:
        at_distance = theme.CARGO_TRANSITION_DISTANCE * 0.9
    dx = target.x - unit.x
    dy = target.y - unit.y
    dd = math.sqrt(dx * dx + dy * dy)
    if dd < at_distance:
        return Point(unit.x, unit.y)
    k = 1 - at_distance / dd
    return Point(unit.x + dx * k, unit.y + dy * k)

class DroneState(object):
    def __init__(self, strategy):
        assert (strategy is not None)
        self.__strategy = strategy
        self._ttl = 0

    @property
    def strategy(self):
        return self.__strategy

    @property
    def unit(self):
        return self.strategy.unit

    @property
    def unit_or_group(self):
        return self.unit.group or self.unit

    @property
    def scene(self):
        return self.unit.scene

    def make_transition(self):
        return None

    def game_step(self):
        self._ttl = self._ttl + 1

    def sources(self):
        _sources = self.scene.asteroids
        _sources = _sources + [m for m in self.unit.scene.motherships if not m.is_alive and m.team != self.unit.team]
        _sources = _sources + [d for d in self.unit.scene.drones if not d.is_alive]
        has_sources = len([s for s in _sources if s.cargo.payload > 0]) > 0
        return has_sources, _sources



class DroneStateNone(DroneState):
    def make_transition(self):
        return self.__class__

class DroneStateIdle(DroneState):
    def __init__(self, strategy):
        super(self.__class__, self).__init__(strategy)

    def make_transition(self):
        if not self.unit.is_alive:
            return DroneStateNone
        if self.unit.have_gun:
            # raise Exception("Guns have not implemented yet")
            pass
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return DroneStateRunout
        has_sources, sources = self.sources()
        k = 0.75 if self.unit.scene.game_frame < 250 else 0.99
        if self.unit.cargo.fullness < k:
            if has_sources:
                return DroneStateHarvest
        if not self.strategy.unit.cargo.is_empty:
            return DroneStateUnload
        elif not has_sources and self.unit.distance_to(self.unit.mothership()) < theme.CARGO_TRANSITION_DISTANCE:
            return DroneStateNone
        return self.__class__



class DroneStateUnload(DroneState):
    def __init__(self, strategy):
        self._target = None
        self._target_cargo = None
        self._transition = None
        super(DroneStateUnload, self).__init__(strategy)
        if self.unit.group:
            self.unit.group.separate()

    def has_any_enemy_going_harvest(self):
        if not self._target_point:
            return False
        enemy_drones = [d for d in self.unit.scene.drones if d.team != self.unit.team and d.is_alive and
                d.distance_to(self._target) < theme.CARGO_TRANSITION_DISTANCE * 4.0 and
                math.fabs(d.direction - Vector.from_points(d.coord, self._target.coord.copy()).direction)<(math.pi/180.0)] # 1 degree
        return len(enemy_drones) > 0

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return DroneStateRunout
        if self.unit.cargo.is_empty:
            return DroneStateIdle
        if self._transition:
            if self.has_any_enemy_going_harvest():
                return DroneStateHarvest
            if self._transition.is_finished:
                return DroneStateIdle
        return self.__class__

    def game_step(self):
        super(self.__class__, self).game_step()
        if self._target is None:
            target = self.strategy.getUnloadTarget()
            if target is None:
                target = self.unit.mothership()
            self._target = target
            self._target_point = get_point_on_way_to(self.unit, target, theme.CARGO_TRANSITION_DISTANCE * 0.9)
            self._target_cargo = target.cargo
            self.strategy.data._targets[self.unit.id] = self._target_point
            self.unit.move_at(self._target_point)
        if self._transition:
            self._transition.game_step()
            target = self.strategy.getHarvestTarget()
            if target is None:
                target = self.unit.mothership()
            self.unit.turn_to(target)
        elif self.unit.is_arrived():
            self._transition = CargoTransition(cargo_from=self.unit.cargo, cargo_to=self._target_cargo)


class DroneStateHarvest(DroneState):
    def __init__(self, strategy):
        super(DroneStateHarvest, self).__init__(strategy)
        self._target = None
        self._target_cargo = None
        self._transition = None

    def make_transition(self):
        if self.unit.health < 0.6 and self.unit.distance_to(self.unit.mothership()) > theme.MOTHERSHIP_HEALING_DISTANCE:
            return DroneStateRunout
        if self.unit.cargo.is_full:
            return DroneStateUnload
        if self._target:
            hglob = [self.strategy.data._drones[t] for t in self.strategy.data._targets if self.strategy.data._targets[t] == self._target]
            if len(hglob) > 1:
                hglob.sort(key=lambda u: u.fullness)
                reqsz = self._target_cargo.payload
                for n, h in enumerate(hglob):
                    reqsz = reqsz - self.unit.cargo.free_space
                    if reqsz < 0:
                        return DroneStateIdle
        #    #if sum([d.cargo.fullnesshglob) > self._target_cargo.payload:
        #    #    return u
        if self._target_cargo and self._target_cargo.fullness == 0.0:
            return DroneStateIdle
        if self._transition and self._transition.is_finished:
            return DroneStateUnload
        has_sources, sources = self.sources()
        if not has_sources:
            if self.unit.cargo.is_empty:
                return DroneStateIdle
            else:
                return DroneStateUnload
        return self.__class__

    def game_step(self):
        super(DroneStateHarvest, self).game_step()
        # TODO: harvest any possible targets on the way to self._target
        if self._transition:
            self._transition.game_step()
            target = self.strategy.getUnloadTarget()
            if target:
                self.unit.turn_to(target)
            else:
                self.unit.turn_to(self.unit.mothership())
        if self._target is None:
            target = self.strategy.getHarvestTarget()
            if target is not None:
                self._target = get_point_on_way_to(self.unit, target, theme.CARGO_TRANSITION_DISTANCE * 0.9)
                self._target_cargo = target.cargo
                self.unit_or_group.move_at(self._target.copy(), turn_to=self.unit.mothership())
                self.strategy.data._targets[self.unit.id] = target
            elif self._transition is not None:
                return
        uclosest = self.unit.closest_in_path
        if self._transition is None and self._target_cargo and self.unit.is_arrived():
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
        if self.unit.group:
            self.unit.group.separate()
        self._target = None
        self._directions = [-25, 25]
        random.shuffle(self._directions)

    def make_transition(self):
        if self.unit.health > 0.75:
            return DroneStateIdle
        return self.__class__

    def game_step(self):
        if self._target is None:
            v = Vector.from_points(self.unit.coord, self.unit.mothership().coord)
            nextdir = self._directions.pop(0)
            self._directions.append(nextdir)
            v = v.from_direction(v.direction + nextdir, max(125, min(225, v.module * 0.50)))
            target = self.unit.coord + v
            target.x = max(self.unit.__class__.radius, min(theme.FIELD_WIDTH-self.unit.__class__.radius, target.x))
            target.y = max(self.unit.__class__.radius, min(theme.FIELD_HEIGHT-self.unit.__class__.radius, target.y))
            # target = self.unit.mothership()
            if target is not None:
                self._target = get_point_on_way_to(self.unit, target, theme.CARGO_TRANSITION_DISTANCE * 0.9)
                self.unit_or_group.move_at(self._target.copy())
            self.unit_or_group.move_at(self._target)
        elif self.unit.distance_to(self._target) <= 1.0:
            self._target = None



