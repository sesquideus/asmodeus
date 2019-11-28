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
    position = coord.Vector3D.from_geodetic(48.746, 21.083, 17380)
    meteor = Meteor(
        mass=0.5,
        density=3370,
        position=position,
        velocity=position.from_local(coord.Vector3D.from_spherical(-30.2, 72.6, 2200)),
        timestamp=datetime.datetime.now(tz=pytz.utc),
        drag_coefficient=0.5,    
    )
    meteor.fly(fps=1, spf=100, method='rk4')
    #meteor.to_dataframe()
    #meteor.plot()

main()

