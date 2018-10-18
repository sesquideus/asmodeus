#!/usr/bin/env python

import multiprocessing as mp
import datetime, random, pprint, os, shutil, logging, io, math

from core               import asmodeus, configuration, dataset, logger
from distribution       import position, velocity, mass, density, time
from physics            import coord
from utilities          import colour as c, utilities as ut

from models.meteor import Meteor
from models.sighting import Sighting

class AsmodeusObserve(asmodeus.Asmodeus):
    def __init__(self):
        log.info("Initializing {}".format(c.script("asmodeus-observe")))
        super().__init__() 
        self.configure()

    def createArgparser(self):
        super().createArgparser()

    def overrideConfig(self):
        super().overrideConfig()

    def configure(self):
        self.loadObservers()
        self.dataset.require('meteors')

        self.dataset.reset('sightings')
        for observer in self.observers:
            self.dataset.create('sightings', observer.id)

    def observe(self):
        pool        = mp.Pool(processes = self.config.mp.processes)
        path        = self.dataset.path('meteors')
        meteorFiles = os.listdir(path)
    
        self.markTime()
        results = [ ### Refactor this more
            pool.apply_async(
                observeMeteor, (self.observers[0], os.path.join(path, meteorFile), self.observers[0].horizon, self.dataset.name)
            ) for meteorFile in meteorFiles
        ]
        out = [result.get(timeout = 5) for result in results]

        log.info("Results written to {output} ({count} meteors processed from {observers} observing sites)".format(
            output      = c.path(self.dataset.path('sightings')),
            count       = len(results),
            observers   = len(self.observers),
        ))
   
        log.info("Finished in {:.6f} seconds ({:.3f} meteors per second)".format(self.runTime(), len(results) / self.runTime()))

def observeMeteor(observer, filename, minAlt, out):
    meteor = Meteor.load(filename)

    sighting = Sighting(observer, meteor)
    if sighting.brightestFrame.altAz.latitude() >= minAlt:
        sighting.save(out) 

    return True

def main(argv):
    for observer in observers:
        observer.createSkyPlot()


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusObserve()
    asmo.observe()
    
    log.info("Finished successfully")
    log.info("---------------------")
