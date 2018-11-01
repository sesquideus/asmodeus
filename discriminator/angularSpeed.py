import logging

from discriminator import base

log = logging.getLogger('root')


class AngularSpeedDiscriminator(base.Discriminator):
    def __init__(self, name, **kwargs):
        self.property   = 'angular speed'
        self.functions  = {
            'all':      self.__class__.all,
            'bracket':  self.__class__.bracket,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def bracket(cls, *, lower: float, upper: float) -> (lambda float: float):
        return lambda sighting: int(sighting.angularSpeed >= lower and sighting.angularSpeed <= upper)
