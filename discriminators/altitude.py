import logging, os, random, math

from utilities import colour as c
from physics import coord

log = logging.getLogger('root')

def all(**kwargs):
    return lambda x: True

def step(**kwargs):
    limit           = kwargs['limit']
    return lambda sighting: sighting.altitude > limit

def linear(**kwargs):
    limit           = kwargs['limit']

    def fun(sighting):
        if sighting.altitude < limit:
            return False
        else:
            return random.random() < ((sighting.altitude - limit) / (90 - limit))

    return fun

def powersine(**kwargs):
    exponent        = kwargs['exponent']

    return lambda sighting: random.random() < math.sin(math.radians(sighting.altitude))**exponent

def function(name, **kwargs):
    return {
        'step':         step,
        'linear':       linear,
        'powersine':    powersine,
        'all':          all,
    }[name](**kwargs)
