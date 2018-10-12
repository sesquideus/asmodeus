import logging, random, math
from colorama import Fore, Style

from utils import colour
import coord, configuration

log = logging.getLogger('root')

def shower(**kwargs):
    ra = kwargs.get('ra', 0)
    dec = kwargs.get('dec', 90)
    speed = kwargs.get('speed', 72000)

    def fun():
        return -coord.Vector3D(
            math.cos(math.radians(dec)) * math.cos(math.radians(ra)),
            math.cos(math.radians(dec)) * math.sin(math.radians(ra)),
            math.sin(math.radians(dec))
        ) * speed

    return fun

def distribution(name, **kwargs):
    return {
        'shower': shower,
    }.get(name, shower)(**kwargs)

