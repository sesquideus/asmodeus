import logging
import math

from distribution import distribution
from physics import coord

log = logging.getLogger('root')


class VelocityDistribution(distribution.Distribution):
    def __init__(self, name, **kwargs):
        self.quantity = 'initial velocity'
        self.functions = {
            'shower':       self.shower,
        }
        super().__init__(name, **kwargs)

    def shower(cls, *, ra, dec, speed):
        return lambda: -coord.Vector3D(
            math.cos(math.radians(dec)) * math.cos(math.radians(ra)),
            math.cos(math.radians(dec)) * math.sin(math.radians(ra)),
            math.sin(math.radians(dec))
        ) * speed
