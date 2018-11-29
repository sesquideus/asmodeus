import logging
from distribution import base

log = logging.getLogger('root')


class DensityDistribution(base.Distribution):
    def __init__(self, name, **kwargs):
        self.quantity           = 'meteoroid density'
        self.functions          = {
            'asteroidal':       self.asteroidal,
            'iron':             self.iron,
            'constant':         self.constant,
            'gauss':            self.gauss,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def asteroidal(cls, **kwargs) -> (lambda: float):
        return lambda: cls.gauss(3300, 50)

    @classmethod
    def iron(cls, **kwargs) -> (lambda: float):
        return lambda: cls.gauss(7800, 30)
