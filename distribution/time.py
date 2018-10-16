import math, random, numbers, logging, datetime

from distribution.distribution import Distribution

log = logging.getLogger('root')

class TimeDistribution(Distribution):
    def __init__(self):
        super().__init__()
    
    def create(self, name, **kwargs):
        return {
            'uniform':      self.uniform,
        }.get(name, self.default)(**kwargs)
        
    def uniform(self, *, begin, end):
        def fun():
            timeSpan        = (end - begin).total_seconds()
            return begin + datetime.timedelta(seconds = random.uniform(0, timeSpan))

        return fun
