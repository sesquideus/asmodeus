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
    position = coord.Vector3D.from_WGS84(48.746, 21.083, 180000)
    #position = coord.Vector3D.from_WGS84(89, 0, 0.01)
    meteor = Meteor(
        mass=0.228602,
#        mass=0.000002,
        density=3370,
        position=position,
        velocity=position.altaz_to_dxdydz(coord.Vector3D.from_spherical(-30.2, 72.6, 52000)),
        #velocity=position.altaz_to_dxdydz(coord.Vector3D.from_spherical(45, 0, 500)),
        timestamp=datetime.datetime.now(tz=pytz.utc),
    )
    meteor.fly(fps=5, spf=10, method='DP')
    #meteor.to_dataframe()
    #meteor.plot()

main()

