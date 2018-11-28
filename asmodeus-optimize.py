#!/usr/bin/env python
"""
    Asmodeus, script 4: multiparametric fitting procedure

    Computes apparent positions and magnitudes for all observers as defined in the configuration file,
    using generated meteors saved in dataset `meteors` directory
    Requires: sightings
    Outputs: multiparametric fits
"""

import sys
import argparse
import multiprocessing as mp

from core               import asmodeus, logger, exceptions
from utilities          import colour as c

from models.meteor import Meteor
from models.sighting import Sighting


class AsmodeusOptimize(asmodeus.Asmodeus):
    def __init__(self):
        self.name = 'optimize'
        super().__init__()
    
    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-c', '--compare', type = argparse.FileType('r'))

    def overrideConfig(self):
        super().overrideConfig()
        if (self.args.compare):
            self.overrideWarning('compare', self.config.optimize.compare, self.args.compare)
            self.config.optimize.compare = True

    def configure(self):
        self.loadObservers()

        try:
            self.dataset.require('sightings')
        except FileNotFoundError as e:
            log.error("Could not load {s} -- did you run {obs}?".format(
                s   = c.path(self.dataset.path('sightings')),
                obs = c.script('asmodeus-observe'),
            ))
            raise exceptions.PrerequisiteError('Could not load sightings')
 
    def optimize(self):
        self.markTime()
        for observer in self.observers:
            observer.loadSightings()
            observer.minimize(self.config.optimize)


if __name__ == "__main__":
    log         = logger.setupLog('root')
    try:
        asmo = AsmodeusOptimize()
        asmo.optimize()
    except exceptions.ConfigurationError as e:
        log.critical("Configuration error \"{}\", terminating".format(e))
        sys.exit(-1)
    except exceptions.OverwriteError as e:
        log.critical("Target directory {} already exists, terminating".format(e))
        sys.exit(-1)
    except exceptions.PrerequisiteError:
        log.critical("Missing prerequisites, aborting")
        sys.exit(-1)
