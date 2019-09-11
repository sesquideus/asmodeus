#!/usr/bin/env python
"""
    Asmodeus, script 2: observe

    Computes apparent positions and magnitudes for all observers as defined in the configuration file,
    using generated meteors saved in specified dataset's `meteors` subdirectory
    Requires: meteors
    Outputs: sightings
"""

import argparse

from core               import asmodeus, logger
from core.parallel      import parallel
from utilities          import colour as c

from models.meteor      import Meteor
from models.sighting    import Sighting
from models.population  import Population
from models.campaign    import Campaign

log = logger.setupLog('root')


class AsmodeusObserve(asmodeus.AsmodeusMultiprocessing):
    name = 'observe'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-s', '--streaks',          action = 'store_true')
        self.argparser.add_argument('-t', '--period',           type = float)

    def overrideConfig(self):
        super().overrideConfig()

        if self.args.streaks:
            self.overrideWarning('streaks', self.config.observations.streaks, self.args.streaks)
            self.config.observations.streaks = True

        if self.args.period:
            self.overrideWarning('reporting period', 1.0, self.args.period)
            self.config.mp.report = self.args.period

    def prepareDataset(self):
        self.dataset.resetSightings()

    def configure(self):
        self.campaign = Campaign(self.dataset, self.config.campaign)

    def runSpecific(self):
        self.markTime()

        self.campaign.loadPopulation()
        self.campaign.observe(processes = self.config.mp.processes, report = self.config.mp.report)

        return

        meteorFiles = self.dataset.list('meteors')
        self.count = 0

        for observer in self.observers:
            argList = [(
                self.dataset.path('meteors', meteorFile),
                self.dataset.path('sightings', observer.id, meteorFile),
            ) for meteorFile in meteorFiles]
            total = len(argList)

            log.info(f"Calculating {c.num(total)} observations using {c.num(self.config.mp.processes)} processes")

            observer.sightings = parallel(observe, argList,
                initializer = init,
                initargs    = (observer, self.config.observations.streaks),
                action      = "Observing meteors",
                period      = self.config.mp.report
            )
            observer.sightings = [s for s in observer.sightings if s is not None]
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
        super().finalize()

def init(_queue, _observer, _streaks):
    global queue
    queue = _queue
    global observer
    observer = _observer
    global streaks
    streaks = _streaks

def observe(args):
    filename, out = args

    queue.put(1)
    meteor = Meteor.load(filename)
    sighting = Sighting(observer, meteor)
    #sighting.save(out, streak = streaks)

    if sighting.brightest.altAz.latitude() < observer.horizon:
        return None

    if streaks:
        return sighting
    else:
        return sighting.asPoint()
