import logging, os, random, math

from distribution.distribution  import Distribution
from core                       import configuration
from physics                    import coord

log = logging.getLogger('root')

class PositionDistribution(Distribution):
    def __init__(self, name, **kwargs):
        self.quantity = 'initial position'
        self.functions = {
            'rectangle':    self.rectangle, 
            'circle':       self.circle,
        }
        super().__init__(name, **kwargs)
    
    @classmethod
    def constant(self, *, latitude: float, longitude: float, elevation: float) -> (lambda: float):
        return lambda: coord.Vector3D.fromGeodetic(latitude, longitude, elevation)

    def rectangle(self, *, south: float, north: float, west: float, east: float, elevation: float) -> (lambda: coord.Vector3D):
        #log.info("This means a total area of about {:.0f} km²".format(
        #    (math.sin(math.radians(north)) - math.sin(math.radians(south))) * math.radians(east - west) * (6371 + elevation / 1000)**2)
        #)

        def fun():
            latitude = random.uniform(south, north)
            longitude = random.uniform(west, east)
            p = random.random() 
            if p < math.cos(math.radians(latitude)):
                log.debug("Meteoroid position accepted") 
                return coord.Vector3D.fromGeodetic(latitude, longitude, elevation)
            else:
                log.debug("Meteoroid position rejected at {}".format(latitude))
                return fun()

        return fun

    def circle(self, *, latitude: float, longitude: float, radius: float, elevation: float) -> (lambda: coord.Vector3D):
        def fun():
            return coord.Vector3D.fromGeodetic(0, 0, 0) ### Put real computation here

        return fun
