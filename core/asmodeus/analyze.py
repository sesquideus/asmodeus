import argparse
import dotmap
import logging

from core import exceptions
from discriminator import MagnitudeDiscriminator, AltitudeDiscriminator, AngularSpeedDiscriminator
from utilities import colour as c

from core.asmodeus import Asmodeus

log = logging.getLogger('root')


class AsmodeusAnalyze(Asmodeus):
    name = 'analyze'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('observers',                type = argparse.FileType('r'))
        self.argparser.add_argument('analyses',                 type = argparse.FileType('r'))
        self.argparser.add_argument('-O', '--overwrite',        action = 'store_true')

    def buildConfig(self):
        observerConfig = self.loadConfigFile(self.args.observers)
        analysesConfig = self.loadConfigFile(self.args.analyses)

        self.config = dotmap.DotMap({
            'observations': observerConfig.observations.toDict(),
            'analyses':  analysesConfig.toDict(),
        }, _dynamic = False)

    def prepareDataset(self):
        self.requireStage('sightings', 'asmodeus-observe')

    def configure(self):
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
        for observer in self.observers:
            self.markTime()
            self.prepareObserver(observer)
            self.runAnalysis(observer)

    def prepareObserver(self, observer):
        observer.settings = self.config.analyses.statistics
        observer.setDiscriminators(self.discriminators)
        observer.loadDataframe()
        observer.applyBias()
