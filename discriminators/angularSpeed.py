import logging, os, random, math

from utilities import colour as c
from physics import coord

log = logging.getLogger('root')

def flat(**kwargs):
    fillFactor      = kwargs['fillFactor']
        
    def fun(sighting):
        return random.random() < fillFactor

    return fun

def function(name, **kwargs):
    return {
        'flat': flat,
    }[name](**kwargs)

