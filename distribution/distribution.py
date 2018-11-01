import random
import logging

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
        return cls(config.distribution, **config.parameters.toDict())

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
        log.info("{quantity} distribution is {name}{params}".format(
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
