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

    def apply(self, sighting):
        return self.compute(sighting.angular_speed)

    @classmethod
    def bracket(cls, *, lower: float, upper: float) -> (lambda float: float):
        return lambda ang_speed: 1 if ang_speed >= lower and ang_speed <= upper else 0
