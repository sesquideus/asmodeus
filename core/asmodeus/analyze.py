import argparse
import dotmap
import logging

from core import exceptions
from discriminator import MagnitudeDiscriminator, AltitudeDiscriminator, AngularSpeedDiscriminator
from utilities import colour as c

from core.asmodeus import Asmodeus
from models.campaign import Campaign

log = logging.getLogger('root')


class AsmodeusAnalyze(Asmodeus):
    name = 'analyze'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-b', '--skip-bias',          action = 'store_true')

    def overrideConfig(self):
        super().overrideConfig()

        self.config.bias.do = True
        if self.args.skip_bias:
            self.overrideWarning('bias effects', self.config.bias.do, not self.args.skip_bias)
            self.config.bias.do = False

    def configure(self):
        self.campaign = Campaign.load(self.dataset, statistics = self.config.statistics)

        try:
            bias = self.config.bias
            discriminators = {
                'appMag':       MagnitudeDiscriminator.fromConfig(bias.magnitude),
                'altitude':     AltitudeDiscriminator.fromConfig(bias.altitude),
                'angSpeed':     AngularSpeedDiscriminator.fromConfig(bias.angularSpeed),
            }

            log.info(f"Loaded {c.num(len(discriminators))} discriminators:")
            for discriminator in discriminators.values():
                discriminator.logInfo()

            self.campaign.setDiscriminators(discriminators)
            
        except AttributeError as e:
            raise exceptions.ConfigurationError(e) from e

    def runSpecific(self):
        self.campaign.filterVisible(bias = self.config.bias.do)
