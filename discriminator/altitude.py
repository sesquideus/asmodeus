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

    def apply(self, sighting):
        return self.compute(sighting.altitude)

    @classmethod
    def step(cls, *, limit: float):
        return lambda altitude: 0 if altitude < limit else 1

    @classmethod
    def linear(cls, *, limit: float):
        return lambda altitude: 0 if altitude < limit else (altitude - limit) / (90 - limit)

    @classmethod
    def sinexp(cls, *, exponent: float):
        return lambda altitude: math.sin(math.radians(altitude))**exponent

    @classmethod
    def default(cls):
        return cls.all
