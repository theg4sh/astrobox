# -*- coding: utf-8 -*-

import os

from astrobox.space_field import SpaceField
from demo.ordinary.greedy import GreedyDrone
from demo.gatherers.reaper import ReaperDrone
from demo.gatherers.runner import RunnerDrone
from demo.ordinary.worker import WorkerDrone
from robogame_engine.theme import theme

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

    space_field.go()
