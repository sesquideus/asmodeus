import logging
import random

from utilities      import colour as c, utilities as util
from core           import exceptions

log = logging.getLogger('root')


class Discriminator():
    """
    A discriminator is a function (sighting.<parameter> -> boolean), representing
    a stochastic process that decides whether a certain sighting will or will not be recorded by the device.
    """
    def __init__(self, name, **kwargs):
        self.name   = name
        self.params = kwargs
        try:
            self.function = self.functions[name](**kwargs)
        except KeyError as e:
            self.errorUnknown(e)
            raise exceptions.ConfigurationError()
        except TypeError as e:
            raise exceptions.ConfigurationError(e)

    def compute(self, value):
        rnd = random.random()
        prob = self.function(value)
        log.debug("{name:<25} {value}: random value {rnd}, threshold {prob} ({comment})".format(
            name    = c.param(self.property.capitalize()),
            value   = c.num(f"{value:9.6f}"),
            rnd     = c.num('{:.6f}'.format(rnd)),
            prob    = c.num('{:.6f}'.format(prob)),
            comment = c.ok('accepted') if rnd < prob else c.err('rejected'),
        ))
        return rnd < prob

    @classmethod
    def fromConfig(cls, config):
        try:
            return cls(config.discriminator, **config.parameters.toDict())
        except AttributeError:
            return cls(config.discriminator)

    @classmethod
    def all(self, **kwargs) -> (lambda float: float):
        return lambda _: 1

    @classmethod
    def default(self, **kwargs):
        raise KeyError("No default discriminator defined for {}".format(self.property))

    def logInfo(self):
        log.info("    {quantity} discriminator is {name}{params}".format(
            quantity    = c.param(self.property.capitalize()),
            name        = c.name(self.name),
            params      = f" ({util.formatParameters(self.params)})" if self.params else "",
        ))
        return self

    def warningDefault(self, name):
        log.warning(f"No {c.name(self.property)} discriminator defined, defaulting to {c.name(self.default)}")
        return self

    def errorUnknown(self, name):
        log.error(f'Unknown {c.name(self.property)} distribution "{c.param(name)}"')
        return self
