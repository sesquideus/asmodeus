import logging
import math

from discriminator import base

log = logging.getLogger('root')


class AltitudeDiscriminator(base.Discriminator):
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
        return lambda sighting: int(sighting.altitude > limit)

    @classmethod
    def linear(cls, *, limit: float):
        return lambda sighting: 0 if sighting.altitude < limit else (sighting.altitude - limit) / (90 - limit)

    @classmethod
    def sinexp(cls, *, exponent: float):
        return lambda sighting: math.sin(math.radians(sighting.altitude))**exponent

    def default(cls):
        return cls.all
