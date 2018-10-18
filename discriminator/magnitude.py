import logging, os, random, math

from utilities import colour as c
from physics import coord
from discriminator.discriminator import Discriminator

log = logging.getLogger('root')

class MagnitudeDiscriminator(Discriminator):
    def __init__(self, name, **kwargs):
        self.property   = 'magnitude'
        self.functions  = {
            'all':      self.__class__.all,
            'step':     self.__class__.step,
            'sigmoid':  self.__class__.sigmoid
        }
        super().__init__(name, **kwargs)

    @classmethod
    def step(cls, *, limit: float, fillFactor: float) -> (lambda x: bool):
        return lambda sighting: sighting.magnitude < limit and random.random() < fillFactor

    @classmethod
    def sigmoid(cls, *, limit: float, width: float, fillFactor: float) -> (lambda x: bool):
        return lambda sighting: random.random() < fillFactor / (1 + math.exp((sighting.magnitude - limit) / width))

def supersigmoid(**kwargs):
    fillFactor      = kwargs.get('fillFactor', 1)
    limit           = kwargs.get('limit', 0)
    omega           = kwargs.get('omega', 1)

    def fun(mag):
        x = random.random()
        u = math.exp((mag - limit) / omega)
        if u < 1/100:
            f = 0
        elif u > 100:
            f = fillFactor
        else:
            f = fillFactor / (1 + math.exp(u - 1))

        return x < f if mag < 5 else False

    return fun

