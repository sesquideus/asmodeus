import logging
import math

from distribution import base
from physics import coord

log = logging.getLogger('root')


class VelocityDistribution(base.Distribution):
    quantity = 'initial velocity'

    def __init__(self, name, **kwargs):
        self.functions = {
            'shower':       self.__class__.shower,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def shower(cls, *, ra, dec, speed):
        return lambda: -coord.Vector3D(
            math.cos(math.radians(dec)) * math.cos(math.radians(ra)),
            math.cos(math.radians(dec)) * math.sin(math.radians(ra)),
            math.sin(math.radians(dec))
        ) * speed
