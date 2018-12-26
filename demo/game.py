# -*- coding: utf-8 -*-
import random

import os
print(os.environ["PYTHONPATH"])
from robogame_engine.theme import theme
from robogame_engine.geometry import Point, Vector

#from astrobox.guns import PlasmaGun
from astrobox.space_field import SpaceField
from astrobox.units import DroneUnit #, Unit

#from demo.drones.drone_unit_with_strategies import DroneUnitWithStrategies

#from demo.drones.worker_drone import WorkerDrone
#from demo.drones.greedy_drone import GreedyDrone
#from demo.drones.hunter_drone import HunterDrone
#from demo.drones.destroyer_drone import DestroyerDrone

from demo.drones.reaper_drone import ReaperDrone

class NoobDrone(DroneUnit):
    pass

class NoobDroneFoo(DroneUnit):
    pass

if __name__ == '__main__':
    space_field = SpaceField(
        name="Space war",
        speed=1,
        field=(1600, 800),
        asteroids_count=20,
    )

    teamA = [ReaperDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamB = [NoobDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamC = [NoobDroneFoo() for _ in range(theme.TEAM_DRONES_COUNT)]
    #teamA = [WorkerDrone()    for _ in range(theme.TEAM_DRONES_COUNT)]
    #teamB = [GreedyDrone()    for _ in range(theme.TEAM_DRONES_COUNT)]
    #teamC = [HunterDrone()    for _ in range(theme.TEAM_DRONES_COUNT)]
    #teamD = [DestroyerDrone() for _ in range(theme.TEAM_DRONES_COUNT)]

    space_field.go()
