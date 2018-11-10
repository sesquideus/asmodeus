#!/usr/bin/env python

import sys

from core               import asmodeus, logger, exceptions
from discriminator      import magnitude, altitude, angularSpeed
from utilities          import colour as c


class AsmodeusAnalyze(asmodeus.Asmodeus):
    def __init__(self):
        log.info("Initializing {}".format(c.script("asmodeus-analyze")))
        super().__init__()
        self.configure()

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

            for disc in self.discriminators:
                disc.logInfo()

        except AttributeError as e:
            raise exceptions.ConfigurationError(e)

    def analyze(self):
        self.markTime()
        for observer in self.observers:
            observer.setDiscriminators(self.discriminators)
            observer.loadSightings()
            observer.processSightings()

            observer.createSkyPlot()

        log.info("Finished in {:.6f} seconds".format(self.runTime()))


if __name__ == "__main__":
    log = logger.setupLog('root')
    try:
        asmo = AsmodeusAnalyze()
        asmo.analyze()
        log.info("---------------------")
    except exceptions.PrerequisiteError:
        log.critical("Missing prerequisites, aborting")
        sys.exit(-1)
