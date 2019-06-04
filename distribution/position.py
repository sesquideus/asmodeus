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
            'pillow':       self.__class__.pillow,
            'circle':       self.__class__.circle,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def constant(cls, *, latitude: float, longitude: float, elevation: float) -> (lambda: coord.Vector3D):
        return lambda: coord.Vector3D.fromGeodetic(latitude, longitude, elevation)

    @classmethod
    def pillow(cls, *, south: float, north: float, west: float, east: float, bottom: float, top: float) -> (lambda: coord.Vector3D):
        # log.info("This means a total area of about {:.0f} km²".format(
        #     (math.sin(math.radians(north)) - math.sin(math.radians(south))) * math.radians(east - west) * (6371 + elevation / 1000)**2)
        # )

        def fun():
            southSin = math.sin(math.radians(south))
            northSin = math.sin(math.radians(north))
            latitude = math.degrees(math.asin(random.uniform(southSin, northSin)))
            longitude = random.uniform(west, east)
            elevation = random.uniform(bottom, top)
            return coord.Vector3D.fromGeodetic(latitude, longitude, elevation)

        return fun

    @classmethod
    def circle(cls, *, latitude: float, longitude: float, radius: float, elevation: float) -> (lambda: coord.Vector3D):
        def fun():
            return coord.Vector3D.fromGeodetic(0, 0, 0)  # Put real computation here

        return fun
