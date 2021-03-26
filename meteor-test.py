#!/usr/bin/env python3

import numpy as np
import pandas
import datetime
import pytz
import logging
import copy

from matplotlib import pyplot

from models import Meteor
from physics import atmosphere, coord, constants

def get_wind(vector):
    return coord.Vector3D(0, 0, 0)

GRAVITY_VECTOR = coord.Vector3D(0, 0, -constants.EARTH_GRAVITY)


def main():
    position = coord.Vector3D.from_WGS84(48.746, 21.083, 180000)
    #position = coord.Vector3D.from_WGS84(90, 0, 100000)
    meteor = Meteor(
        mass=1,
        density=3370,
        position=position,
        velocity=coord.Vector3D(0, 0, 0),
        timestamp=datetime.datetime.now(tz=pytz.utc),
    )
    meteor.fly_constant(fps=1, spf=1, method='RK4')

main()

