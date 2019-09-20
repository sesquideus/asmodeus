import logging
from distribution import base

log = logging.getLogger('root')


class DensityDistribution(base.Distribution):
    quantity           = 'meteoroid density'

    def __init__(self, name, **kwargs):
        self.functions          = {
            'asteroidal':       self.__class__.asteroidal,
            'iron':             self.__class__.iron,
            'constant':         self.__class__.constant,
            'gauss':            self.__class__.gauss,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def asteroidal(cls, **kwargs) -> (lambda: float):
        return lambda: cls.gauss(3300, 50)

    @classmethod
    def iron(cls, **kwargs) -> (lambda: float):
        return lambda: cls.gauss(7800, 30)
