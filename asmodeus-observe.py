#!/usr/bin/env python

import multiprocessing as mp

from core               import asmodeus, logger
from utilities          import colour as c

from models.meteor import Meteor
from models.sighting import Sighting


class AsmodeusObserve(asmodeus.Asmodeus):
    def __init__(self):
        log.info("Initializing {}".format(c.script("asmodeus-observe")))
        super().__init__()
        self.configure()

    def configure(self):
        self.loadObservers()
        self.dataset.require('meteors')

        self.dataset.reset('sightings')
        for observer in self.observers:
            self.dataset.create('sightings', observer.id)

    def observe(self):
        self.markTime()
        pool        = mp.Pool(processes = self.config.mp.processes)
        meteorFiles = self.dataset.list('meteors')

        results = [
            pool.apply_async(
                observeMeteor,
                (observer, self.dataset.path('meteors', meteorFile), observer.horizon, self.dataset.path('sightings', observer.id, meteorFile))
            ) for meteorFile in meteorFiles for observer in self.observers
        ]
        out = [result.get() for result in results]
        log.info("Finished in {:.6f} seconds ({:.3f} meteors per second)".format(self.runTime(), len(out) / self.runTime()))


def observeMeteor(observer, filename, minAlt, out):
    meteor = Meteor.load(filename)

    sighting = Sighting(observer, meteor)
    if sighting.brightestFrame.altAz.latitude() >= minAlt:
        sighting.save(out)

    return True


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusObserve()
    asmo.observe()

    log.info("Finished successfully")
    log.info("---------------------")
