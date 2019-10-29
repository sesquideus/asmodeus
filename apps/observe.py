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

    def create_argparser(self):
        super().create_argparser()
        self.argparser.add_argument('-s', '--streaks', action='store_true', help="Save observations as streaks (all frames will be recorded)")

    def override_config(self):
        super().override_config()

        self.config.campaign.streaks = False
        if self.args.streaks:
            self.override_warning('streaks', self.config.campaign.streaks, self.args.streaks)
            self.config.campaign.streaks = True

    def prepare_dataset(self):
        self.dataset.protected_reset('sightings')
        self.dataset.remove('analyses')

    def configure(self):
        self.campaign = Campaign(self.dataset, self.config.campaign)

    def run_specific(self):
        self.mark_time()

        self.campaign.load_population(processes=self.config.mp.processes, period=self.config.mp.report)
        self.campaign.observe(processes=self.config.mp.processes, period=self.config.mp.report)
        self.campaign.save()

    def finalize(self):
        log.info("{num} observations were processed in {time} seconds ({rate} sightings per second)".format(
            num     = c.num(self.campaign.population.count),
            time    = c.num("{:.6f}".format(self.run_time())),
            rate    = c.num("{:.3f}".format(self.campaign.population.count / self.run_time())),
        ))
        log.info("Observations were saved as {target} to {dir}".format(
            target  = c.over('streaks' if self.config.campaign.streaks else 'points'),
            dir     = c.path(self.dataset.path('sightings')),
        ))
        super().finalize()
