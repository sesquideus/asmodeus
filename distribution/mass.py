import random
import logging
import numpy as np

from distribution import base

log = logging.getLogger('root')


class MassDistribution(base.Distribution):
    def __init__(self, name, **kwargs):
        self.quantity = 'meteoroid mass'
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
    def constant(cls, *, value: float) -> (lambda: float):
        return lambda: value

    @classmethod
    def power(cls, *, shape: float, minimum: float) -> (lambda: float):
        return lambda: (minimum**(shape + 1) * random.random())**(1 / (shape + 1))

# Maybe it is a good idea to do this with mixins
"""
class MassDistributionMixin():
    self.quantity = 'meteoroid mass'


class ParetoDistribution(base.Distribution, MassDistributionMixin):
    def __init__(self, *, shape, minimum):
        self.shape = shape
        self.minimum = minimum

    def sample(self):
        return (np.random.pareto(self.shape - 1) + 1) * self.minimum
"""
