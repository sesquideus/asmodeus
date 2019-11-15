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

    def create_argparser(self):
        super().create_argparser()
        self.argparser.add_argument('-b', '--bias', type=argparse.FileType('r'), help="bias configuration file")

    def load_config(self):
        super().load_config()
        if self.args.bias:
            self.bias = configuration.load_YAML(self.args.bias)
            configuration.make_static(self.bias)

    def override_config(self):
        super().override_config()

    def configure(self):
        self.campaign = Campaign.load(self.dataset, analyses=self.config)

        if self.args.bias:
            try:
                log.info("Setting bias function discriminators")
                discriminators = {
                    'apparent_magnitude':   MagnitudeDiscriminator.from_config(self.bias.magnitude),
                    'altitude':             AltitudeDiscriminator.from_config(self.bias.altitude),
                    'angular_speed':        AngularSpeedDiscriminator.from_config(self.bias.angular_speed),
                }

                log.info(f"Loaded {c.num(len(discriminators))} discriminators:")
                for discriminator in discriminators.values():
                    discriminator.log_info()

                self.campaign.set_discriminators(discriminators)
                
            except AttributeError as e:
                raise exceptions.ConfigurationError(e) from e
        else:
            log.debug("No bias file set")

    def run_specific(self):
        self.campaign.filter_visible(self.args.bias is not None)
