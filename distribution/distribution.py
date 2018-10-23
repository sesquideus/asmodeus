import math, random, numbers, logging

from utilities import colour as c, utilities as util

log = logging.getLogger('root')

class Distribution():
    def __init__(self, name, **kwargs):
        self.name   = name
        self.params = kwargs
        try:
            self.sample = self.functions.get(name, self.default)(**kwargs)
        except KeyError as e:
            self.errorUnknown(name)
            raise exceptions.ConfigurationError()        
    
    @classmethod
    def fromConfig(cls, config):
        return cls(config.distribution, **config.parameters._asdict())

    @classmethod
    def constant(self, *, value):
        return lambda: value

    @classmethod
    def gauss(cls, *, mean = 0, sigma = 1):  
        return lambda: random.gauss(mean, sigma)

    @classmethod
    def default(cls, **kwargs):
        raise KeyError("No default distribution defined")

    def logInfo(self):
        log.info("{quantity:<27} distribution is {name:>20}{params}".format(
            quantity    = c.param(self.quantity),
            name        = c.name(self.name),
            params      = "" if self.params is None else " ({})".format(util.formatParameters(self.params)),
        ))
        return self

    def warningDefault(self):
        log.warning("No {} distribution defined, defaulting to {}".format(c.name(self.quantity), c.name(self.default)))

    def errorUnknown(self, name):
        log.error("Unknown {} distribution \"{}\"".format(self.quantity, name))
