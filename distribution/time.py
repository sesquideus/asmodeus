import random
import logging
import datetime

from distribution import base

log = logging.getLogger('root')


class TimeDistribution(base.Distribution):
    quantity = 'temporal'

    def __init__(self, name, **kwargs):
        self.functions = {
            'constant':     self.__class__.constant,
            'uniform':      self.__class__.uniform,
        }
        super().__init__(name, **kwargs)

    @classmethod
    def constant(cls, *, value):
        return lambda: value

    @classmethod
    def uniform(cls, *, begin, end):
        return lambda: begin + datetime.timedelta(seconds = random.uniform(0, (end - begin).total_seconds()))
