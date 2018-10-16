import math, random, sys, numbers, logging

from core import exceptions
from distribution.distribution import Distribution

log = logging.getLogger('root')

class DensityDistribution(Distribution):
    def __init__(self):
        super().__init__()
        self.quantity           = 'density'
    
    def create(self, name, **kwargs):
        try:
            if isinstance(name, numbers.Number):
                return lambda: name 
        
            return {
                'asteroidal':   self.asteroidal,
                'iron':         self.iron,
                'gauss':        self.gauss,                
            }[name](**kwargs)
        except KeyError as e:
            self.errorUnknown(name)
            raise exceptions.ConfigurationError()            
 
    def asteroidal(self, **kwargs):
        return self.gauss(3300, 50) 

    def iron(self, **kwargs):
        return self.gauss(7800, 30)

    def default(self, **kwargs):
        self.warningDefault()
