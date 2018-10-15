#!/usr/bin/env python

import numpy as np, multiprocessing as mp
import datetime, argparse, yaml, sys, datetime, random, pprint, os, shutil, logging, io, math

import asmodeus, coord, configuration, dataset
import configuration.velocity, configuration.position, configuration.mass, configuration.time
from models.meteor import Meteor
from coord import Vector3D, rotMatrixZ

from log import setupLog

import colour as c
import configuration, utils

class AsmodeusGenerate(asmodeus.Asmodeus):
    def __init__(self):
        log.info("Initializing {}".format(c.script("asmodeus-generate")))
        super().__init__() 

    def createArgparser(self):
        log.debug("Creating argparser for {}".format(c.script("asmodeus-generate")))
        super().createArgparser()
        self.argparser.add_argument('-c', '--count', type = int)

    def overrideConfig(self):
        log.debug("Overriding config for {}".format(c.script("asmodeus-generate")))
        super().overrideConfig()

        if (self.args.count):
            self.overrideWarning('count', self.config.meteors.count, self.args.count)
            self.config.meteors.count = self.args.count

    def configure(self):
        self.distributionInfo("Particle mass", self.config.meteors.mass.distribution, self.config.meteors.mass.parameters)
        self.massDistribution       = configuration.mass.MassDistribution().create(self.config.meteors.mass.distribution, **self.config.meteors.mass.parameters._asdict())

        self.distributionInfo("Initial position", self.config.meteors.position.distribution, self.config.meteors.position.parameters)
        self.positionDistribution   = configuration.position.distribution(self.config.meteors.position.distribution, **self.config.meteors.position.parameters._asdict())
        
        self.distributionInfo("Initial velocity", self.config.meteors.velocity.distribution, self.config.meteors.velocity.parameters)
        self.velocityDistribution   = configuration.velocity.distribution(self.config.meteors.velocity.distribution, **self.config.meteors.velocity.parameters._asdict())

        self.distributionInfo("Particle density", self.config.meteors.material.density)
        self.densityDistribution    = configuration.density.DensityDistribution().create(self.config.meteors.material.density)

        self.distributionInfo("Temporal", self.config.meteors.time.distribution, self.config.meteors.time.parameters)
        self.temporalDistribution   = configuration.time.TimeDistribution().create(self.config.meteors.time.distribution, **self.config.meteors.time.parameters._asdict())


def createMeteor():
    timestamp           = temporalDistribution()

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
    log.info("About to generate {} meteoroids".format(c.num(config.meteors.count)))
    dataset.prepare()   
 
    meteors = list(filter(lambda x: x is not None, [createMeteor() for _ in range(0, config.meteors.count)]))
    log.info("{total} meteoroids survived the sin θ test ({percent}), total mass {mass:.6f} kg".format(
        total       = c.num(len(meteors)),
        percent     = c.num("{:5.2f}%".format(100 * len(meteors) / config.meteors.count)),
        mass        = sum(map(lambda x: x.mass, meteors))
    ))
    meteors = process(meteors)

    log.info("{number} meteors written to {directory}".format(
        number      = c.num(len(meteors)),
        directory   = c.path(asmodeus.datasetPath('meteors')),
    ))
    log.info("Finished in {:.6f} seconds ({:.3f} meteors per second)".format(asmodeus.runTime(), len(meteors) / asmodeus.runTime()))


if __name__ == "__main__":
    log = setupLog('root')
    asmo = AsmodeusGenerate()
    asmo.configure()
    
    main(sys.argv)
    log.info("Finished successfully")
    log.info("---------------------")
