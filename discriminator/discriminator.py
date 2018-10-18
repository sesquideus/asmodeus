import math, random, numbers, logging

from utilities      import colour as c, utilities as util
from core           import exceptions

log = logging.getLogger('root')

class Discriminator():
    """
    A discriminator is a function (sighting -> boolean), representing
    a stochastic process that decides whether a certain sighting will or will not be recorded by the device
    """
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
        try:
            return cls(config.discriminator, **config.parameters._asdict())
        except AttributeError as e:
            return cls(config.discriminator)
    
    @classmethod
    def all(self):
        return lambda _: True

    @classmethod
    def default(self, **kwargs):
        raise KeyError("No default discriminator defined")

    def logInfo(self):
        log.info("{quantity:<27} discriminator is {name:>20}{params}".format(
            quantity    = c.param(self.property),
            name        = c.name(self.name),
            params      = "" if self.params is None else " ({})".format(util.formatParameters(self.params)),
        ))
        return self

    def warningDefault(self, name):
        log.warning("No {} distribution defined, defaulting to {}".format(self.property, self.default)) 
        return self

    def errorUnknown(self, name):
        log.error(c.err("Unknown {} distribution \"{}\"".format(self.property, name)))
        return self
