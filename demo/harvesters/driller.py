from demo.harvesters.reaper import ReaperStrategy, ReaperDrone
from robogame_engine.geometry import Point
from robogame_engine.theme import theme


class DrillerStrategy(ReaperStrategy):
    def distributeHarvestSources(self, units):
        # Distribute enought amount of units to harvest a source
        for u in units:
            if u == self.unit.mothership():
                continue
            if u in self.data._targets.values():
                continue
            if sum([theme.DRONE_CARGO_PAYLOAD for t in self.data._targets if
                    self.data._targets[t] == u]) < u.cargo.payload:
                return u
        return None

    def getHarvestTarget(self):
        self.unit.pathfind.update_units(func=lambda u: not u.cargo.is_empty)
        #center_of_scene = Point(theme.FIELD_WIDTH / 2, theme.FIELD_HEIGHT / 2)
        center_of_scene = self.unit.mothership().coord.copy()
        units = self.unit.pathfind.points
        if not units:
            return None
        units.sort(key=lambda u: u.distance_to(self.unit))

        u = self.distributeHarvestSources(units)
        return u
        #return u if u else units[0]

    def getUnloadTarget(self):
        return self.unit.mothership()


class DrillerDrone(ReaperDrone):
    _strategy_class = DrillerStrategy
