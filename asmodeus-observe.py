#!/usr/bin/env python
"""
    Asmodeus, script 2: observe

    Computes apparent positions and magnitudes for all observers as defined in the configuration file,
    using generated meteors saved in specified dataset's `meteors` subdirectory
    Requires: meteors
    Outputs: sightings
"""

import time
import sys
import multiprocessing as mp

from core               import asmodeus, logger, exceptions
from utilities          import colour as c

from models.meteor import Meteor
from models.sighting import Sighting


class AsmodeusObserve(asmodeus.AsmodeusMP):
    name = 'observe'
    
    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-O', '--overwrite',        action = 'store_true')
        self.argparser.add_argument('-p', '--processes',        type = int)
        self.argparser.add_argument('-c', '--count',            type = int)
        self.argparser.add_argument('-s', '--streaks',          action = 'store_true')

    def overrideConfig(self):
        super().overrideConfig()
        if self.args.streaks:
            self.overrideWarning('streaks', self.config.observations.streaks, self.args.streaks)
            self.config.observations.streaks = True

    def configure(self):
        self.requireStage('meteors', 'asmodeus-generate')
        self.protectOverwrite('sightings')

        self.loadObservers()
        for observer in self.observers:
            self.dataset.create('sightings', observer.id)

    def run(self):
        self.observe()
        self.finalize()

    def observe(self):
        self.markTime()
        meteorFiles = self.dataset.list('meteors')
        self.count = 0

        for observer in self.observers:
            argList = [(
                observer,
                self.dataset.path('meteors', meteorFile),
                self.dataset.path('sightings', observer.id, meteorFile),
                self.config.observations.streaks,
            ) for meteorFile in meteorFiles]
            total = len(argList)

            log.info(f"Calculating {c.num(total)} observations using {c.num(self.config.mp.processes)} processes")

            observer.sightings = self.parallel(observe, argList, action = "Observing meteors", period = self.config.mp.report)
            observer.createDataframe()
            observer.saveDataframe()

            self.count += len(observer.sightings)

    def finalize(self):
        log.info("{num} observations were processed in {time} seconds ({rate} sightings per second)".format(
            num     = c.num(self.count),
            time    = c.num("{:.6f}".format(self.runTime())),
            rate    = c.num("{:.3f}".format(self.count / self.runTime())),
        ))
        log.info("Observations were saved as {target} to {dir}".format(
            target  = c.over('streaks' if self.config.observations.streaks else 'points'),
            dir     = c.path(self.dataset.path('sightings')),
        ))
        self.ok = True
        

def observe(args):
    queue, observer, filename, out, streaks = args

    queue.put(1)
    meteor = Meteor.load(filename)
    sighting = Sighting(observer, meteor)
    sighting.save(out, streak = streaks)
    return sighting.asPoint()

if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusObserve()
    asmo.run()

