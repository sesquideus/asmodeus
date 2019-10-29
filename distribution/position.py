import logging
import random
import math

from distribution import base
from physics import coord

log = logging.getLogger('root')


class PositionDistribution(base.Distribution):
    quantity = 'initial position'

    def __init__(self, name, **kwargs):
        self.functions = {
            'constant':     self.__class__.constant,
            'pillow':       self.__class__.pillow,
            'circle':       self.__class__.circle,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def constant(cls, *, latitude: float, longitude: float, elevation: float) -> (lambda: coord.Vector3D):
        return lambda: coord.Vector3D.from_geodetic(latitude, longitude, elevation)

    @classmethod
    def pillow(cls, *, south: float, north: float, west: float, east: float, bottom: float, top: float) -> (lambda: coord.Vector3D):
        def fun():
            southSin = math.sin(math.radians(south))
            northSin = math.sin(math.radians(north))
            latitude = math.degrees(math.asin(random.uniform(southSin, northSin)))
            longitude = random.uniform(west, east)
            elevation = random.uniform(bottom, top)
            return coord.Vector3D.from_geodetic(latitude, longitude, elevation)
        return fun

    @classmethod
    def circle(cls, *, latitude: float, longitude: float, radius: float, elevation: float) -> (lambda: coord.Vector3D):
        def fun():
            return coord.Vector3D.from_geodetic(0, 0, 0)  # Put real computation here
        return fun
