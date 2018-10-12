#!/usr/bin/env python

import numpy as np
import multiprocessing as mp
import namedtupled as nt
import datetime, argparse, yaml, sys, datetime, random, pprint, os, shutil, logging, io

import asmodeus, configuration, models
from models.meteor import Meteor
from models.observer import Observer
from models.sighting import Sighting
from models.sightingframe import SightingFrame

from utils import colour, formatParameters

from log import setupLog

def observeMeteors():
    pool = mp.Pool(processes = config.mp.processes)
    results = [pool.apply_async(observeMeteor, (meteorFile,)) for meteorFile in os.listdir(os.path.join('datasets', config.dataset.name, 'meteors'))]
    out = [result.get(timeout = 5) for result in results]

    log.info("Results written to {output} ({count} meteors processed from {observers} observing sites)".format(
        output      = colour(os.path.join(config.dataset.path, 'sightings'), 'dir'),
        count       = len(results),
        observers   = len(observers),
    ))
   
    return len(results)

def observeMeteor(filename):
    meteor = Meteor.load(os.path.join('datasets', config.dataset.name, 'meteors', filename), 'pickle')

    for observer in observers:
        sighting = Sighting(observer, meteor)
        if sighting.brightestFrame.altAz.latitude() >= config.meteors.minAltitude:
            sighting.save(config.dataset.name) 

    return True
                
def main(argv):
    asmodeus.remove('sightings')
    asmodeus.createSightingsDirectory()
    observedCount = observeMeteors()

    for observer in observers:
        observer.createSkyPlot()

    log.info("Finished in {:.6f} seconds ({:.3f} meteors per second)".format(asmodeus.runTime(), observedCount / asmodeus.runTime()))

if __name__ == "__main__":
    log = setupLog('root')
    config = asmodeus.initialize('observe')
    observers = asmodeus.loadObservers()
    
    main(sys.argv)
    log.info("Finished successfully")
    log.info("---------------------")
