import logging
import math

from discriminator import base

log = logging.getLogger('root')


class MagnitudeDiscriminator(base.Discriminator):
    def __init__(self, name, **kwargs):
        self.property   = 'magnitude'
        self.functions  = {
            'all':      self.__class__.all,
            'step':     self.__class__.step,
            'sigmoid':  self.__class__.sigmoid,
            'arctan':   self.__class__.arctan,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def step(cls, *, limit: float) -> (lambda float: float):
        return lambda magnitude: 0 if magnitude > limit else 1

    @classmethod
    def sigmoid(cls, *, limit: float, width: float) -> (lambda float: float):
        return lambda magnitude: 1 / (1 + math.exp((magnitude - limit) / width))

    @classmethod
    def arctan(cls, *, limit: float, width: float) -> (lambda float: float):
        return lambda magnitude: math.atan(-width * (magnitude - limit)) / math.pi + 0.5
