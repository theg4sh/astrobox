import math
from operator import mul

from robogame_engine.geometry import Point, Vector
from robogame_engine.theme import theme

from demo.harvesters.reaper import ReaperStrategy, ReaperDrone
from demo.drones.states import DroneStateIdle

class DrillerStrategy(ReaperStrategy):
    def getHarvestTarget(self):
        self.unit.pathfind.update_units(func=lambda u: not u.cargo.is_empty)
        center_of_scene = Point(theme.FIELD_WIDTH/2, theme.FIELD_HEIGHT/2)
        units = self.unit.pathfind.points
        units.sort(key=lambda u: u.distance_to(center_of_scene))
        # Distribute enought amount of units to harvest a source
        for u in units:
            if sum([theme.DRONE_CARGO_PAYLOAD for t in self.data._targets if self.data._targets[t] == u]) < u.cargo.payload:
                return u
        return units[0]

    def getUnloadTarget(self):
        return self.unit.mothership()

class DrillerDrone(ReaperDrone):
    _strategy_class = DrillerStrategy

