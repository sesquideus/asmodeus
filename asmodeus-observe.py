#!/usr/bin/env python
"""
    Asmodeus, script 2: observe

    Computes apparent positions and magnitudes for all observers as defined in the configuration file,
    using generated meteors saved in specified dataset's `meteors` subdirectory
    Requires: meteors
    Outputs: sightings
"""

import sys
import multiprocessing as mp

from core               import asmodeus, logger, exceptions
from utilities          import colour as c

from models.meteor import Meteor
from models.sighting import Sighting


class AsmodeusObserve(asmodeus.Asmodeus):
    def __init__(self):
        self.name = 'observe'
        super().__init__()
    
    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-s', '--streaks', action = 'store_true')

    def overrideConfig(self):
        super().overrideConfig()
        if (self.args.streaks):
            self.overrideWarning('streaks', self.config.observations.streaks, self.args.streaks)
            self.config.observations.streaks = True

    def configure(self):
        self.loadObservers()

        try:
            self.dataset.require('meteors')
        except FileNotFoundError as e:
            log.error("Could not load {s} -- did you run {gen}?".format(
                s   = c.path(self.dataset.path('meteors')),
                gen = c.script('asmodeus-generate'),
            ))
            raise exceptions.PrerequisiteError()

        if self.dataset.exists('sightings') and not self.config.overwrite:
            raise exceptions.OverwriteError(c.path(self.dataset.path('sightings')))
        else:
            self.dataset.reset('sightings')

        for observer in self.observers:
            self.dataset.create('sightings', observer.id)

    def run(self):
        self.observe()
        self.finalize()

    def observe(self):
        self.markTime()
        log.info("Calculating observations...")
        pool        = mp.Pool(processes = self.config.mp.processes)
        meteorFiles = self.dataset.list('meteors')

        results = [
            pool.apply_async(
                observeMeteor, (
                    observer,
                    self.dataset.path('meteors', meteorFile),
                    self.config.observations.minAltitude,
                    self.dataset.path('sightings', observer.id, meteorFile),
                    self.config.observations.streaks,
                )
            ) for meteorFile in meteorFiles for observer in self.observers
        ]

        #while not results._number_left > 0:
        #    print(results._number_left)
        #    time.sleep(10)

        out = [result.get() for result in results]
        self.count = len(out)

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
        

def observeMeteor(observer, filename, minAlt, out, streaks):
    meteor = Meteor.load(filename)

    sighting = Sighting(observer, meteor)
    if sighting.brightestFrame.altAz.latitude() >= minAlt:
        sighting.save(out, streak = streaks)
        return True
    else:
        return False


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusObserve()
    asmo.run()

