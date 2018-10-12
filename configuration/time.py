import math, random, numbers, logging
from utils import colour

from configuration.distribution import Distribution

log = logging.getLogger('root')

class TimeDistribution(Distribution):
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
        
    def uniform(self, **kwargs):
        return self.constant(value = 620000)
