import logging, os, random, math
from colorama import Fore, Style

from utils import colour
from coord import Vector3D
import configuration

log = logging.getLogger('root')

def rectangle(**kwargs):
    south = kwargs['south']
    north = kwargs['north']
    west = kwargs['west']
    east = kwargs['east']  
    elevation = kwargs['elevation']
    
    log.info("This means a total area of about {:.0f} km²".format(
        (math.sin(math.radians(north)) - math.sin(math.radians(south))) * math.radians(east - west) * (6371 + elevation / 1000)**2)
    )

    def fun():
        latitude = random.uniform(south, north)
        longitude = random.uniform(west, east)
        p = random.random() 
        if p < math.cos(math.radians(latitude)):
            log.debug("Meteoroid position accepted") 
            return Vector3D.fromGeodetic(latitude, longitude, elevation)
        else:
            log.debug("Meteoroid position rejected at {}".format(latitude))
            return fun()

    return fun

def distribution(name, **kwargs):
    return {
        'rectangle': rectangle,
    }[name](**kwargs)

