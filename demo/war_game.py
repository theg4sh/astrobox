# -*- coding: utf-8 -*-

import os

from astrobox.space_field import SpaceField
from demo.ordinary.greedy import GreedyDrone
from demo.gatherers.reaper import ReaperDrone
from demo.troopers.destroyer import DestroyerDrone
from demo.troopers.hunter import HunterDrone
from robogame_engine.theme import theme

if __name__ == '__main__':
    space_field = SpaceField(
        name="Space war",
        speed=5,
        field=(1600, 800),
        asteroids_count=20,
    )

    teamA = [ReaperDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamB = [GreedyDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamC = [HunterDrone() for _ in range(theme.TEAM_DRONES_COUNT)]
    teamD = [DestroyerDrone() for _ in range(theme.TEAM_DRONES_COUNT)]

    space_field.go()
