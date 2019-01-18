# -*- coding: utf-8 -*-

import os

from astrobox.space_field import SpaceField
# from demo.drones.worker_drone import WorkerDrone
from demo.drones.greedy import GreedyDrone
from demo.drones.reaper import ReaperDrone
from demo.drones.runner import RunnerDrone
from demo.drones.worker import WorkerDrone
from robogame_engine.theme import theme

# from demo.drones.hunter_drone import HunterDrone
# from demo.drones.destroyer_drone import DestroyerDrone
print(os.environ["PYTHONPATH"])

if __name__ == '__main__':
    space_field = SpaceField(
        name="Space war",
        speed=5,
        field=(1600, 800),
        asteroids_count=20,
    )

    teamA = [ReaperDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamB = [GreedyDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamC = [WorkerDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamD = [RunnerDrone() for _ in range(theme.TEAM_DRONES_COUNT)]

    # teamC = [HunterDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    # teamD = [DestroyerDrone() for _ in range(theme.TEAM_DRONES_COUNT)]

    space_field.go()
