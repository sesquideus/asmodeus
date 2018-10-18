import logging, os, random, math
from colorama import Fore, Style

from utilities import colour as c
from physics import coord

log = logging.getLogger('root')

def all(**kwargs):
    return lambda sighting: True

def step(**kwargs):
    fillFactor      = kwargs.get('fillFactor', 1)
    limit           = kwargs.get('limit', 0)

    def fun(sighting):
        if sighting.magnitude < limit:
            return random.random() < fillFactor
        else:
            return False

    return fun

def sigmoid(**kwargs):
    fillFactor      = kwargs.get('fillFactor', 1)
    limit           = kwargs['limit']
    omega           = kwargs['omega']

    def fun(sighting):
        return random.random() < fillFactor / (1 + math.exp((sighting.magnitude - limit) / omega))

    return fun

def supersigmoid(**kwargs):
    fillFactor      = kwargs.get('fillFactor', 1)
    limit           = kwargs.get('limit', 0)
    omega           = kwargs.get('omega', 1)

    def fun(mag):
        x = random.random()
        u = math.exp((mag - limit) / omega)
        if u < 1/100:
            f = 0
        elif u > 100:
            f = fillFactor
        else:
            f = fillFactor / (1 + math.exp(u - 1))

        return x < f if mag < 5 else False

    return fun


def function(name, **kwargs):
    return {
        'supersigmoid': supersigmoid,
        'sigmoid':      sigmoid,
        'step':         step,
        'all':          all,
    }[name](**kwargs)
