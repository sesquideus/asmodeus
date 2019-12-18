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

vysny_klatov = coord.Vector3D.from_WGS84(48.746, 21.083, 18000)
kosice_vel = vysny_klatov.altaz_to_dxdydz(coord.Vector3D.from_spherical(-59.8, 72.6, 2200))

kosice = Meteor(
    mass=0.0000228602,
    density=3370,
    position=vysny_klatov,
    velocity=kosice_vel,
    timestamp=datetime.datetime(2010, 2, 28, 22, 45, 0)
)

def main():
    meteor = kosice
    model = TextbookModel()
    integratorRK4 = base.IntegratorRungeKutta4(model, 5, 1)
    integratorDPA = base.IntegratorDormandPrinceAdaptive(model, 10, spf_min=1, spf_max=32, error_coarser=1e-12, error_finer=1e-2)

    integratorDPA.simulate(meteor)
        
    #.fly_adaptive(fps=20, method='DP', error_coarser=1e-12, error_finer=1e-4, min_spf=1, max_spf=16)
    #meteor.to_dataframe()
    #meteor.plot()

main()

