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
from flight.textbook import TextbookModel
from integrators import base

def get_wind(vector):
    return coord.Vector3D(0, 0, 0)


def main():
    position = coord.Vector3D.from_WGS84(48.746, 21.083, 380000)
#    position = coord.Vector3D.from_WGS84(90, 0, 1e9)
    meteor = Meteor(
        mass=0.0000228602,
#        mass=0.000002,
        density=3370,
        position=position,
        velocity=position.altaz_to_dxdydz(coord.Vector3D.from_spherical(-30.2, 72.6, 58000)),
#        velocity=position.altaz_to_dxdydz(coord.Vector3D.from_spherical(0, 84.5, 7460)),
     #   velocity=position.altaz_to_dxdydz(coord.Vector3D.from_spherical(45, 0, 500)),
        timestamp=datetime.datetime.now(tz=pytz.utc),
    )

    model = TextbookModel()
    integrator = base.IntegratorRungeKutta4(model, 20, 1)

    integrator.simulate(meteor)
        
    #.fly_adaptive(fps=20, method='DP', error_coarser=1e-12, error_finer=1e-4, min_spf=1, max_spf=16)
    #meteor.to_dataframe()
    #meteor.plot()

main()

