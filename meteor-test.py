#!/usr/bin/env python3

import numpy as np
import pandas
import datetime
import pytz
import logging

from matplotlib import pyplot

from models import Meteor
from physics import atmosphere, coord, constants

def get_wind(vector):
    return coord.Vector3D(0, 0, 0)

GRAVITY_VECTOR = coord.Vector3D(0, 0, -constants.EARTH_GRAVITY)


def main():
    meteor = Meteor(
        mass=2.4,
        density=3370,
        position=coord.Vector3D.from_geodetic(48.717, 20.945, 36000),
        velocity=coord.Vector3D(-100, 200, 100),
        timestamp=datetime.datetime.now(tz=pytz.utc),
        drag_coefficient=0.5,    
    )
    meteor.fly(fps=1, spf=10, method='rk4')
    #meteor.to_dataframe()
    #meteor.plot()

main()

