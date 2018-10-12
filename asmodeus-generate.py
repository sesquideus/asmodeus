#!/usr/bin/env python

import numpy as np, multiprocessing as mp
import datetime, argparse, yaml, sys, datetime, random, pprint, os, shutil, logging, io, math

import asmodeus, coord, configuration
import configuration.velocity, configuration.position, configuration.mass
from models.meteor import Meteor
from coord import Vector3D, rotMatrixZ

from log import setupLog
from utils import readableDir, writeableDir, colour, formatParameters

from configuration.density import DensityDistribution


def createMeteor():
    timeSpan            = (config.meteors.time.end - config.meteors.time.begin).total_seconds()
    timestamp           = config.meteors.time.begin + datetime.timedelta(seconds = random.uniform(0, timeSpan))

    mass                = massDistribution()
    density             = densityDistribution()
    position            = positionDistribution()
    velocityEquatorial  = velocityDistribution()

    velocityECEF        = Vector3D.fromNumpyVector((rotMatrixZ(coord.earthRotationAngle(timestamp)) @ velocityEquatorial.toNumpyVector()))
    entryAngleSin       = -position * velocityECEF / (position.norm() * velocityECEF.norm())
    entryAngle          = math.degrees(math.asin(entryAngleSin))

    accept              = random.random()
    if accept > entryAngleSin:
        log.debug("Meteoroid rejected: sine of entry angle {}, random value {}".format(entryAngleSin, accept))
        return None
    else:
        log.debug("Meteoroid accepted: sine of entry angle {}, random value {}".format(entryAngleSin, accept))
        return Meteor(
            mass            = mass,
            density         = density,
            velocity        = velocityECEF,
            position        = position,
            timestamp       = timestamp,
            ablationHeat    = config.meteors.material.ablationHeat,
            heatTransfer    = config.meteors.material.heatTransfer,
            dragCoefficient = config.meteors.shape.dragCoefficient,
        )
    
def process(meteors):
    pool = mp.Pool(processes = config.mp.processes)
    results = [pool.apply_async(simulate, (meteor, )) for meteor in meteors]
    return [result.get(timeout = 10) for result in results]

def simulate(meteor):
    meteor.flyRK4(config.integrator.fps, config.integrator.spf)
    meteor.save(config.dataset.path)

def main(argv):
    log.info("About to simulate {} meteoroids".format(colour(config.meteors.count, 'num')))
    asmodeus.prepareDataset()
    
    meteors = list(filter(lambda x: x is not None, [createMeteor() for _ in range(0, config.meteors.count)]))
    log.info("{total} meteoroids survived the sin θ test ({percent}), total mass {mass:.6f} kg".format(
        total       = colour(len(meteors), 'num'),
        percent     = colour("{:5.2f}%".format(100 * len(meteors) / config.meteors.count), 'num'),
        mass        = sum(map(lambda x: x.mass, meteors))
    ))
    meteors = process(meteors)

    log.info("{number} meteors written to {directory}".format(
        number      = colour(len(meteors), 'num'),
        directory   = colour(asmodeus.datasetPath('meteors'), 'dir'))
    )
    log.info("Finished in {:.6f} seconds ({:.3f} meteors per second)".format(asmodeus.runTime(), len(meteors) / asmodeus.runTime()))


if __name__ == "__main__":
    log = setupLog('root')
    config = asmodeus.initialize('generate')

    log.info("Particle mass distribution is {} ({})".format(colour(config.meteors.mass.distribution, 'name'), formatParameters(config.meteors.mass.parameters)))
    massDistribution = configuration.mass.distribution(config.meteors.mass.distribution, **config.meteors.mass.parameters._asdict())

    log.info("Initial position distribution is {} ({})".format(colour(config.meteors.position.distribution, 'name'), formatParameters(config.meteors.position.parameters)))
    positionDistribution = configuration.position.distribution(config.meteors.position.distribution, **config.meteors.position.parameters._asdict())
    
    log.info("Initial velocity distribution is {} ({})".format(colour(config.meteors.velocity.distribution, 'name'), formatParameters(config.meteors.velocity.parameters)))
    velocityDistribution = configuration.velocity.distribution(config.meteors.velocity.distribution, **config.meteors.velocity.parameters._asdict())

    log.info("Particle density distribution is {}".format(colour(config.meteors.material.density, 'name')))
    densityDistribution = DensityDistribution().create(config.meteors.material.density)


    main(sys.argv)
    log.info("Finished successfully")
    log.info("---------------------")
