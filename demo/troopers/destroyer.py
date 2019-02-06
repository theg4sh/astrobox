# -*- coding: utf-8 -*-

from demo.harvesters.strategies import StrategyHarvesting, StrategyDestroyer, DroneUnitWithStrategies
# TODO вынести в труперов
from demo.troopers.events import EventUnitDamage


# from robogame_engine.user_interface import Lines
def is_on_straight(a, b):
    v = Vector.from_points(a.coord, b.coord)
    v.rotate(-a.direction)
    if math.fabs(v.direction) < 90.0:
        a = v.direction / 180.0 * math.pi
        limit = (b.__class__.radius + Projectile.radius)
        if a.team == b.team:
            limit *= 1.5
        return math.fabs(a.distance_to(b) * math.sin(a)) < limit
    return False

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

        self.gun_fire()

        if self.have_gun:
            if self.is_strategy_finished():
                self.append_strategy(StrategyHarvesting(unit=self))

    def gun_fire(self):
        if not self.unit.have_gun:
            return

        def target_drones():
            for d in self.unit.scene.drones:
                if not d.is_alive or d.id == self.unit.id:
                    continue
                if self.unit.distance_to(d) > theme.PROJECTILE_TTL * theme.PROJECTILE_SPEED * 0.8:
                    continue
                if is_on_straight(self.unit, d):
                    yield d

        targets = list(target_drones())
        if targets:
            if is_on_straight(self.unit, self.unit.mothership()):
                targets.append(self.unit.mothership())
            targets.sort(key=lambda t: self.unit.distance_to(t))

            # print("Team {}:{}\t{} {}".format(self.unit.team, self.unit.id, len(targets), len(teammates)))
            # print("Team {}:{}\t{}".format(self.unit.team, self.unit.id, targets))
            if self.unit.team != targets[0].team:
                # print("Team {}:{} {}".format(self.unit.team, self.unit.id, targets))
                self.unit.gun.shot([d for d in targets if d.team != self.unit.team][0])

    def on_damage(self, victim=None, attacker=None):
        # TODO вынести в труперов
        if victim == self:
            for tm in self.teammates:
                tm.add_event(EventUnitDamage(tm, victim=victim, attacker=attacker))
        else:
            # TODO: react on damaged teammate
            print(victim, attacker)
            pass
