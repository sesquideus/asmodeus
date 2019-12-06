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
    #position = coord.Vector3D.from_WGS84(89, 0, 0.01)
    meteor = Meteor(
        mass=0.228602,
#        mass=0.000002,
        density=3370,
        position=position,
        velocity=position.altaz_to_dxdydz(coord.Vector3D.from_spherical(-30.2, 72.6, 58000)),
        #velocity=position.altaz_to_dxdydz(coord.Vector3D.from_spherical(45, 0, 500)),
        timestamp=datetime.datetime.now(tz=pytz.utc),
    )
    #meteor.fly_constant(fps=0.1, spf=1, method='euler')

    meteor1 = copy.deepcopy(meteor)
    meteor2 = copy.deepcopy(meteor)
    meteor3 = copy.deepcopy(meteor)
    meteor4 = copy.deepcopy(meteor)
    meteor5 = copy.deepcopy(meteor)

    #meteor1.fly_constant(fps=8, spf=4, method='Euler')
    #meteor2.fly_constant(fps=8, spf=4, method='RK4')
    #meteor3.fly_constant(fps=8, spf=4, method='DP')
    #meteor4.fly_adaptive(fps=8, spf=4, method='DP', error_coarser=1e-6)

    for i in range(0, 1):
        meteor5 = copy.deepcopy(meteor)
        #meteor5.fly_constant(fps=8, spf=4, method='Euler')
        meteor5.fly_adaptive(fps=20, spf=1, method='DP', error_coarser=1e-6, error_finer=1e-2, max_spf=16)
    #meteor.to_dataframe()
    #meteor.plot()

main()

