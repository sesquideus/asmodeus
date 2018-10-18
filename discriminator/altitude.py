import logging, os, random, math

from utilities import colour as c
from physics import coord
from discriminator.discriminator import Discriminator

log = logging.getLogger('root')

class AltitudeDiscriminator(Discriminator):
    def __init__(self, name, **kwargs):
        self.property   = 'altitude'
        self.functions  = {
            'all':      self.__class__.all,
            'step':     self.__class__.step,
            'linear':   self.__class__.linear,
            'sinexp':   self.__class__.sinexp,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def step(cls, *, limit: float):
        return lambda sighting: sighting.altitude > limit

    @classmethod
    def linear(cls, *, limit: float):
        def fun(sighting):
            if sighting.altitude < limit:
                return False
            else:
                return random.random() < (sighting.altitude - limit) / (90 - limit)

    @classmethod
    def sinexp(cls, *, exponent: float):
        return lambda sighting: random.random() < math.sin(math.radians(sighting.altitude))**exponent
