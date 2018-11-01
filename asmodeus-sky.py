#!/usr/bin/env python
"""
    Produces a sky plot
    Requires: sightings
    Outputs: rendered gnuplot template for sky plot
"""

from core               import asmodeus, logger
from utilities          import colour as c

from models.meteor import Meteor
from models.sighting import Sighting


class AsmodeusSky(asmodeus.Asmodeus):
    def __init__(self):
        log.info("Initializing {}".format(c.script("asmodeus-sky")))
        super().__init__()
        self.configure()

    def configure(self):
        self.loadObservers()
        self.dataset.require('meteors')

        self.dataset.reset('sightings')
        for observer in self.observers:
            self.dataset.create('sightings', observer.id)


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusSky()
    asmo.render()

    log.info("Finished successfully")
    log.info("---------------------")
