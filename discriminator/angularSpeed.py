import logging, os, random, math

from utilities import colour as c
from physics import coord

from discriminator.discriminator import Discriminator

log = logging.getLogger('root')

class AngularSpeedDiscriminator(Discriminator):
    def __init__(self, name, **kwargs):
        self.property   = 'angular speed'
        self.functions  = {
            'all':      self.__class__.all,
            'bracket':  self.__class__.bracket,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def bracket(cls, *, lower: float, upper: float):
        return lambda sighting: sighting.angularSpeed >= lower and sighting.angularSpeed <= upper
