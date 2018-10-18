import math, random, sys, numbers, logging

from core import exceptions
from distribution.distribution import Distribution

log = logging.getLogger('root')

class DensityDistribution(Distribution):
    def __init__(self, name, **kwargs):
        self.quantity           = 'Meteoroid density'
        self.functions          = {
            'asteroidal':       self.asteroidal,
            'iron':             self.iron,
            'constant':         self.constant,
            'gauss':            self.gauss,
        }
        super().__init__(name, **kwargs)
        
    @classmethod
    def asteroidal(cls, **kwargs):
        return lambda: cls.gauss(3300, 50) 

    @classmethod
    def iron(cls):
        return lambda: cls.gauss(7800, 30)
