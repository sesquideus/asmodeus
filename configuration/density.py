import math, random, sys, numbers, logging
from utils import colour

from configuration.distribution import Distribution

log = logging.getLogger('root')

class DensityDistribution(Distribution):
    def __init__(self):
        super().__init__()
    
    def create(self, name, **kwargs):
        if isinstance(name, numbers.Number):
            return lambda: name 
        
        return {
            'cometary':     self.cometary,
            'asteroidal':   self.asteroidal,
            'iron':         self.iron,
        }.get(name, self.default)(**kwargs)
        
    def cometary(self, **kwargs):
        return self.constant(value = 620000)

    def asteroidal(self, **kwargs):
        return lambda: random.gauss(3300, 50) 

    def iron(self, **kwargs):
        return lambda: random.gauss(7800, 30)

