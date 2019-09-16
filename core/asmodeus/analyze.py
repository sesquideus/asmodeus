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
        self.campaign.filterVisible()
