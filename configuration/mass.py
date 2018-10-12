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
        
    def pareto(self, *, shape, minimum):
        return lambda: (np.random.pareto(shape - 1) + 1)

    def iron(self, **kwargs):
        return lambda: random.gauss(7800, 30)

def constant(**kwargs):
    def fun():
        return kwargs['mass']

    return fun

def pareto(**kwargs):
    shape       = kwargs['shape']
    minimum     = kwargs['minimum']

    def fun():
        return (np.random.pareto(shape - 1) + 1) * minimum

    return fun

def power(**kwargs):
    shape       = kwargs['shape']
    minimum     = kwargs['minimum']

    def fun():
        return (minimum**(shape + 1) * (1 - random.random()))**(1 / (shape + 1))

    return fun

def distribution(name, **kwargs):
    if isinstance(name, numbers.Number):
        return name

    try:
        return {
            'pareto': pareto,
            'constant': constant,
            'power': power,
        }[name](**kwargs)
    except KeyError as e:
        log.error("Unknown mass distribution function {}".format(colour(e, 'error')))
        return constant(mass = 0.001)
