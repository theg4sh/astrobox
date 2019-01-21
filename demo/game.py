# -*- coding: utf-8 -*-

import os

from astrobox.space_field import SpaceField
from demo.drones.reaper import ReaperDrone
#from demo.drones.driller import DrillerDrone
# from demo.drones.runner import RunnerDrone
# from demo.drones.worker import WorkerDrone
from demo.drones.greedy import GreedyDrone
from demo.drones.worker import WorkerDrone
# from demo.drones.hunter import HunterDrone
# from demo.drones.destroyer import DestroyerDrone
from robogame_engine.theme import theme

if __name__ == '__main__':
    space_field = SpaceField(
        name="Space war",
        speed=2,
        field=(1600, 800),
        asteroids_count=20,
    )

    teamA = [ReaperDrone()  for _ in range(theme.TEAM_DRONES_COUNT)]
    teamB = [GreedyDrone()  for _ in range(theme.TEAM_DRONES_COUNT)]
    #teamC = [WorkerDrone()  for _ in range(theme.TEAM_DRONES_COUNT)]
    #teamD = [DrillerDrone() for _ in range(theme.TEAM_DRONES_COUNT)]

    # teamC = [HunterDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    # teamD = [DestroyerDrone() for _ in range(theme.TEAM_DRONES_COUNT)]

    space_field.go()
