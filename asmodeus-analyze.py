#!/usr/bin/env python

import sys
import argparse
import dotmap

from core               import asmodeus, logger, exceptions
from discriminator      import MagnitudeDiscriminator, AltitudeDiscriminator, AngularSpeedDiscriminator
from utilities          import colour as c


class AsmodeusAnalyze(asmodeus.Asmodeus):
    name = 'analyze'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('observers',                type = argparse.FileType('r'))
        self.argparser.add_argument('analyses',                 type = argparse.FileType('r'))
        self.argparser.add_argument('-s', '--sky-plots',        action = 'store_true')
        self.argparser.add_argument('-O', '--overwrite',        action = 'store_true')

    def buildConfig(self):
        observerConfig = self.loadConfigFile(self.args.observers)
        analysesConfig = self.loadConfigFile(self.args.analyses)

        self.config = dotmap.DotMap({
            'observations': observerConfig.observations.toDict(),
            'analyses':  analysesConfig.toDict(),
        }, _dynamic = False)

    def overrideConfig(self):
        super().overrideConfig()
        if self.args.sky_plots:
            self.overrideWarning('sky plots', self.config.plot.sky.enabled, self.args.sky_plots)
            self.config.plot.sky.enable = True

    def configure(self):
        self.requireStage('sightings', 'asmodeus-observe')
        self.protectOverwrite('analyses')
        self.protectOverwrite('plots')
        self.protectOverwrite('histograms')
        self.loadObservers()

        try:
            bias = self.config.analyses.bias
            self.discriminators = {
                'appMag':       MagnitudeDiscriminator.fromConfig(bias.magnitude),
                'altitude':     AltitudeDiscriminator.fromConfig(bias.altitude),
                'angSpeed':     AngularSpeedDiscriminator.fromConfig(bias.angularSpeed),
            }

            log.info(f"Loaded {c.num(len(self.discriminators))} discriminators:")
            for disc in self.discriminators.values():
                disc.logInfo()

        except AttributeError as e:
            raise exceptions.ConfigurationError(e)

    def runSpecific(self):
        self.analyze()
        self.plotSky()
        self.finalize()

    def analyze(self):
        self.markTime()
        for observer in self.observers:
            observer.settings = self.config.analyses.statistics
            observer.setDiscriminators(self.discriminators)
            observer.loadDataframe()
            observer.analyzeSightings()

    def plotSky(self):
        for observer in self.observers:
            observer.plotSkyPlot(self.config)

    def finalize(self):
        log.info(f"Finished in {self.runTime():.6f} seconds")
        self.ok = True


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusAnalyze()
    asmo.run()
