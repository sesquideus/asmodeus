import logging, random, math

from distribution.distribution  import Distribution
from core                       import configuration
from physics                    import coord

log = logging.getLogger('root')

class VelocityDistribution(Distribution):
    def __init__(self, name, **kwargs):
        self.quantity = 'Initial velocity'
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

        return fun

def distribution(name, **kwargs):
    return {
        'shower': shower,
    }.get(name, shower)(**kwargs)

