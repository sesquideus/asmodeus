#!/usr/bin/env python
"""
    Asmodeus, script 2: observe

    Computes apparent positions and magnitudes for all observers as defined in the configuration file,
    using generated meteors saved in specified dataset's `meteors` subdirectory
    Requires: meteors
    Outputs: sightings
"""

from core               import asmodeus, logger
from utilities          import colour as c

from models.campaign    import Campaign

log = logger.setupLog('root')


class AsmodeusObserve(asmodeus.AsmodeusMultiprocessing):
    name = 'observe'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-s', '--streaks',          action = 'store_true')

    def overrideConfig(self):
        super().overrideConfig()

        self.config.campaign.streaks = False
        if self.args.streaks:
            self.overrideWarning('streaks', self.config.campaign.streaks, self.args.streaks)
            self.config.campaign.streaks = True

    def prepareDataset(self):
        self.dataset.resetSightings()

    def configure(self):
        self.campaign = Campaign(self.dataset, self.config.campaign)

    def runSpecific(self):
        self.markTime()

        self.campaign.loadPopulation(processes = self.config.mp.processes, period = self.config.mp.report)
        self.campaign.observe(processes = self.config.mp.processes, period = self.config.mp.report)
        self.campaign.save()

    def finalize(self):
        log.info("{num} observations were processed in {time} seconds ({rate} sightings per second)".format(
            num     = c.num(self.campaign.population.count),
            time    = c.num("{:.6f}".format(self.runTime())),
            rate    = c.num("{:.3f}".format(self.campaign.population.count / self.runTime())),
        ))
        log.info("Observations were saved as {target} to {dir}".format(
            target  = c.over('streaks' if self.config.campaign.streaks else 'points'),
            dir     = c.path(self.dataset.path('sightings')),
        ))
        super().finalize()
