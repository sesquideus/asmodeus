import math, random, sys, numbers, logging

from core import exceptions
from distribution.distribution import Distribution

log = logging.getLogger('root')

class DensityDistribution(Distribution):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.quantity           = 'density'
        self.functions          = {
            'asteroidal':       self.asteroidal,
            'iron':             self.iron,
            'constant':         self.constant,
        }
    
    @classmethod
    def asteroidal(self, **kwargs):
        return lambda: self.gauss(3300, 50) 

    def iron(self, **kwargs):
        return lambda: self.gauss(7800, 30)

    def default(self, **kwargs):
        self.warningDefault()
