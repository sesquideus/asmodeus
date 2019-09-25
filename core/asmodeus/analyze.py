import argparse
import dotmap
import logging

from core import exceptions, configuration
from discriminator import MagnitudeDiscriminator, AltitudeDiscriminator, AngularSpeedDiscriminator
from utilities import colour as c

from core.asmodeus import Asmodeus
from models.campaign import Campaign

log = logging.getLogger('root')


class AsmodeusAnalyze(Asmodeus):
    name = 'analyze'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-b', '--bias', type = argparse.FileType('r'), help = "bias configuration file")

    def loadConfig(self):
        super().loadConfig()
        if self.args.bias:
            self.bias = configuration.loadYAML(self.args.bias)
            configuration.makeStatic(self.bias)

    def overrideConfig(self):
        super().overrideConfig()

    def configure(self):
        self.campaign = Campaign.load(self.dataset, analyses = self.config)

        if self.args.bias:
            try:
                log.info("Setting bias function discriminators")
                discriminators = {
                    'appMag':       MagnitudeDiscriminator.fromConfig(self.bias.magnitude),
                    'altitude':     AltitudeDiscriminator.fromConfig(self.bias.altitude),
                    'angSpeed':     AngularSpeedDiscriminator.fromConfig(self.bias.angularSpeed),
                }

                log.info(f"Loaded {c.num(len(discriminators))} discriminators:")
                for discriminator in discriminators.values():
                    discriminator.logInfo()

                self.campaign.setDiscriminators(discriminators)
                
            except AttributeError as e:
                raise exceptions.ConfigurationError(e) from e
        else:
            log.debug("No bias file set")

    def runSpecific(self):
        self.campaign.filterVisible(self.args.bias is not None)
