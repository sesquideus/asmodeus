import random
import logging
import numpy as np

from distribution import base

log = logging.getLogger('root')


class DragCoefficientDistribution(base.Distribution):
    quantity = 'drag coefficient'

    def __init__(self, name, **kwargs):
        self.functions = {
            'constant':     self.__class__.constant,
            'uniform':      self.__class__.uniform,
        }
        super().__init__(name, **kwargs)
