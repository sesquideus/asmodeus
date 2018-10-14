import math, random, sys, numbers, logging
import numpy as np
from utils import colour

from configuration.distribution import Distribution

log = logging.getLogger('root')

class MassDistribution(Distribution):
    def __init__(self):
        super().__init__()

    def magic(self, config):
        if (isinstance(config.distribution, numbers.Number)):
            return lambda: name
        else:
            return {
                'pareto':   lambda: (np.random.pareto(config.parameters.shape - 1) + 1) * config.parameters.minimum
            }
    
    def create(self, name, **kwargs):
        if isinstance(name, numbers.Number):
            return lambda: name 
        
        return {
            'pareto':       self.pareto,
            'exponential':  self.exponential,
            'power':        self.power,
            'constant':     self.constant,
        }.get(name, self.default)(**kwargs)
        
    def pareto(self, *, shape: float, minimum: float) -> (lambda: float):
        return lambda: (np.random.pareto(shape - 1) + 1) * minimum

    def exponential(self, *, shape: float) -> (lambda: float):
        return lambda: np.random.exponential(shape)

    def constant(self, *, mass: float) -> (lambda: float):
        return lambda: mass

    def power(self, *, shape, minimum):
        return lambda: (minimum**(shape + 1) * random.random())**(1 / (shape + 1))
