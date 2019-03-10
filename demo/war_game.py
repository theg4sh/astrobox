# -*- coding: utf-8 -*-

import os

from astrobox.space_field import SpaceField
from demo.ordinary.runner import RunnerDrone
from demo.ordinary.greedy import GreedyDrone
from demo.harvesters.reaper import ReaperDrone
#from demo.troopers.destroyer import DestroyerDrone
#from demo.troopers.hunter import HunterDrone
from demo.troopers.harrier import HarrierStrategy, HarrierDrone
from robogame_engine.theme import theme

class NoopDrone(RunnerDrone):
    def game_step(self):
        pass

if __name__ == '__main__':
    space_field = SpaceField(
        name="Space war",
        speed=5,
        field=(1600, 800),
        asteroids_count=20,
        allow_shooting=True,
    )

    #teamA = [ReaperDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamB = [GreedyDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    #teamC = [HunterDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamD = [HarrierDrone(mode=HarrierStrategy.MODE_KILL_THEM_ALL) for _ in range(theme.TEAM_DRONES_COUNT)]

    space_field.go()
