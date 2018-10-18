import math, random, sys, numbers, logging
import numpy as np

from distribution.distribution  import Distribution
from core                       import configuration
from physics                    import coord

log = logging.getLogger('root')

class MassDistribution(Distribution):
    def __init__(self, name, **kwargs):
        self.quantity = 'Meteoroid mass'
        self.functions = {
            'pareto':       self.pareto, 
            'exponential':  self.exponential,
            'constant':     self.constant,
        }
        super().__init__(name, **kwargs)
    
    @classmethod
    def pareto(cls, *, shape: float, minimum: float) -> (lambda: float):
        return lambda: (np.random.pareto(shape - 1) + 1) * minimum

    @classmethod
    def exponential(cls, *, shape: float) -> (lambda: float):
        return lambda: np.random.exponential(shape)

    @classmethod
    def constant(cls, *, mass: float) -> (lambda: float):
        return lambda: mass

    @classmethod
    def power(cls, *, shape: float, minimum: float) -> (lambda: float):
        return lambda: (minimum**(shape + 1) * random.random())**(1 / (shape + 1))
