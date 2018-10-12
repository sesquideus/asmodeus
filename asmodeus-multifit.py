#!/usr/bin/env python

import numpy as np
import multiprocessing as mp
import datetime, argparse, yaml, sys, datetime, random, pprint, os, logging, itertools

import asmodeus, configuration, models, log
import discriminators.magnitude, discriminators.altitude, discriminators.angularSpeed
from models.meteor import Meteor
from models.observer import Observer
from models.sighting import Sighting
from models.sightingframe import SightingFrame

from histogram import Histogram
from utils import colour, formatParameters 
from log import setupLog

def main(argv):
    log.info("Magnitude detection efficiency profile is {} ({})".format(colour(config.bias.magnitude.function, 'name'), formatParameters(config.bias.magnitude.parameters)))
    log.info("Altitude detection efficiency profile is {} ({})".format(colour(config.bias.altitude.function, 'name'), formatParameters(config.bias.altitude.parameters)))
    log.info("Angular speed detection efficiency profile is {} ({})".format(colour(config.bias.angularSpeed.function, 'name'), formatParameters(config.bias.angularSpeed.parameters)))

    for observer in observers:
        observer.loadSightings()
        observer.multifit('magnitude', config.multifit.magnitude, altDis, aspDis)
        observer.multifit('altitude', config.multifit.altitude, magDis, aspDis)
    
    log.info("Finished in {:.6f} seconds".format(asmodeus.runTime()))

if __name__ == "__main__":
    log         = log.setupLog('root')
    config      = asmodeus.initialize('analyze')
    observers   = asmodeus.loadObservers()
    amos        = asmodeus.createAmosHistograms('amos.tsv')

    magDis      = discriminators.magnitude.function(config.bias.magnitude.function, **config.bias.magnitude.parameters._asdict())
    altDis      = discriminators.altitude.function(config.bias.altitude.function, **config.bias.altitude.parameters._asdict())
    aspDis      = discriminators.angularSpeed.function(config.bias.angularSpeed.function, **config.bias.angularSpeed.parameters._asdict())

    main(sys.argv)
    log.info("Finished successfully")
    log.info("---------------------")
