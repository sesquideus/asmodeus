import random
import logging
import dotmap

from core import exceptions
from utilities import colour as c, utilities as u

log = logging.getLogger('root')


class Distribution():
    def __init__(self, name, **kwargs):
        self.name   = name
        self.params = kwargs
        try:
            self.sample = self.functions.get(name, self.default)(**kwargs)
        except KeyError:
            self.errorUnknown(name)
            raise exceptions.ConfigurationError()

    @classmethod
    def fromConfig(cls, config):
        try:
            return cls(config.distribution, **config.parameters.toDict())
        except KeyError:
            log.error("{cfg} is not a valid configuration option for {name}".format(
                cfg     = c.param(config),
                name    = c.name(cls.__name__)
            ))
            log.error("Expected distribution name \"distribution: 'string'\" and a dictionary of parameters")
            raise exceptions.ConfigurationError("Could not initialize {name}".format(
                name    = c.name(cls.__name__)
            ))

    @classmethod
    def constant(self, *, value) -> (lambda: float):
        return lambda: value

    @classmethod
    def gauss(cls, *, mean = 0, sigma = 1) -> (lambda: float):
        return lambda: random.gauss(mean, sigma)

    @classmethod
    def default(cls, **kwargs):
        raise NotImplementedError("No default distribution defined")

    def logInfo(self):
        log.info("    {quantity} distribution is {name}{params}".format(
            quantity    = c.param(self.quantity.capitalize()),
            name        = c.name(self.name),
            params      = "" if self.params is None else " ({})".format(u.formatParameters(self.params)),
        ))
        return self

    def warningDefault(self):
        log.warning("No {} distribution defined, defaulting to {}".format(c.name(self.quantity), c.name(self.default)))
        return self

    def errorUnknown(self, name):
        log.error("Unknown {} distribution \"{}\"".format(self.quantity, name))
        return self
