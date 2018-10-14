import math, random, numbers, logging
from utils import colour

log = logging.getLogger('root')

class Distribution():
    def __init__(self):
        pass

    def constant(self, *, value):
        return lambda: value

    def gauss(self, *, mu = 0, sigma = 1):  
        return lambda: random.gauss(mean, sigma)

    def default(self, **kwargs):
        raise KeyError("No default distribution defined")

