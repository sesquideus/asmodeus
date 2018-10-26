#!/usr/bin/env python

from core               import asmodeus, logger, exceptions
from discriminator      import magnitude, altitude, angularSpeed
from utilities          import colour as c


class AsmodeusAnalyze(asmodeus.Asmodeus):
    def __init__(self):
        log.info("Initializing {}".format(c.script("asmodeus-analyze")))
        super().__init__()
        self.configure()

    def configure(self):
        self.loadObservers()
        self.dataset.require('sightings')

        self.dataset.reset('histograms')
        for observer in self.observers:
            self.dataset.create('histograms', observer.id)

        try:
            bias            = self.config.bias
            self.magDis     = magnitude.MagnitudeDiscriminator.fromConfig(bias.magnitude).logInfo()
            self.altDis     = altitude.AltitudeDiscriminator.fromConfig(bias.altitude).logInfo()
            self.aspDis     = angularSpeed.AngularSpeedDiscriminator.fromConfig(bias.angularSpeed).logInfo()
        except AttributeError as e:
            raise exceptions.ConfigurationError(e)

    def analyze(self):
        self.markTime()
        for observer in self.observers:
            observer.loadSightings()
            observer.processSightings(self.magDis, self.altDis, self.aspDis)

            # observer.createSkyPlot()

        log.info("Finished in {:.6f} seconds".format(self.runTime()))


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusAnalyze()
    asmo.analyze()

    log.info("Finished successfully")
    log.info("---------------------")
