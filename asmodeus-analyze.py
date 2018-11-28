#!/usr/bin/env python

import sys

from core               import asmodeus, logger, exceptions
from discriminator      import magnitude, altitude, angularSpeed
from utilities          import colour as c


class AsmodeusAnalyze(asmodeus.Asmodeus):
    def __init__(self):
        self.name = 'analyze'
        super().__init__()

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-s', '--sky-plots', action = 'store_true')

    def overrideConfig(self):
        super().overrideConfig()
        if (self.args.sky_plots):
            self.overrideWarning('sky plots', self.config.plot.sky.enabled, self.args.sky_plots)
            self.config.plot.sky.enable = True

    def configure(self):
        self.loadObservers()

        try:
            self.dataset.require('sightings')
            self.dataset.reset('histograms')
            self.dataset.reset('plots')
        except FileNotFoundError as e:
            log.error("Could not load {s} -- did you run {obs}?".format(
                s   = c.path(self.dataset.path('sightings')),
                obs = c.script('asmodeus-observe'),
            ))
            raise exceptions.PrerequisiteError()

        try:
            bias = self.config.bias
            self.discriminators = [
                magnitude.MagnitudeDiscriminator.fromConfig(bias.magnitude),
                altitude.AltitudeDiscriminator.fromConfig(bias.altitude),
                angularSpeed.AngularSpeedDiscriminator.fromConfig(bias.angularSpeed),
            ]

            log.info("Discriminators loaded:")
            for disc in self.discriminators:
                disc.logInfo()

        except AttributeError as e:
            raise exceptions.ConfigurationError(e)

    def run(self):
        self.analyze()

    def analyze(self):
        self.markTime()
        for observer in self.observers:
            observer.setDiscriminators(self.discriminators)
            observer.loadSightings()
            observer.analyzeSightings()
            observer.createSkyPlot()

    def finalize(self):
        log.info("Finished in {:.6f} seconds".format(self.runTime()))


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusAnalyze()
    asmo.run()
