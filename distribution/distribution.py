import math, random, numbers, logging

from utilities import colour as c

log = logging.getLogger('root')

class Distribution():
    def __init__(self, name, **kwargs):
        try:
            self.sample = self.allowedFunctions[name](**kwargs)
        except KeyError as e:
            self.errorUnknown(name)
            raise exceptions.ConfigurationError()        

    def constant(self, *, value):
        return lambda: value

    def gauss(self, *, mean = 0, sigma = 1):  
        return lambda: random.gauss(mean, sigma)

    def default(self, **kwargs):
        raise KeyError("No default distribution defined")

    def warningDefault(self, name):
        log.warning("No {} distribution defined, defaulting to {}".format(self.quantity, self.default)) 

    def errorUnknown(self, name):
        log.error(c.err("Unknown {} distribution \"{}\"".format(self.quantity, name)))
