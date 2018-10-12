import logging, os, random, math
from colorama import Fore, Style

from utils import colour
from coord import Vector3D
import configuration

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

