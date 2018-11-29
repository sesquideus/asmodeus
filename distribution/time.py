import random
import logging
import datetime

from distribution import base

log = logging.getLogger('root')


class TimeDistribution(base.Distribution):
    def __init__(self, name, **kwargs):
        self.quantity = 'temporal'
        self.functions = {
            'uniform':      self.uniform,
        }
        super().__init__(name, **kwargs)

    def uniform(self, *, begin, end):
        return lambda: begin + datetime.timedelta(seconds = random.uniform(0, (end - begin).total_seconds()))
