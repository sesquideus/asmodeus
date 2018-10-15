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
        super().createArgparser()
        self.argparser.add_argument('-c', '--count', type = int)

    def overrideConfig(self):
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

    def generate(self):
        log.info("About to generate {} meteoroids".format(c.num(self.config.meteors.count)))
        self.dataset.prepare()   
     
        self.meteors = list(filter(lambda x: x is not None, [self.createMeteor() for _ in range(0, self.config.meteors.count)]))
        log.info("{total} meteoroids survived the sin θ test ({percent}), total mass {mass:.6f} kg".format(
            total       = c.num(len(self.meteors)),
            percent     = c.num("{:5.2f}%".format(100 * len(self.meteors) / self.config.meteors.count)),
            mass        = sum(map(lambda x: x.mass, self.meteors))
        ))


    def createMeteor(self):
        timestamp           = self.temporalDistribution()
        mass                = self.massDistribution()
        density             = self.densityDistribution()
        position            = self.positionDistribution()
        velocityEquatorial  = self.velocityDistribution()

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
                ablationHeat    = self.config.meteors.material.ablationHeat,
                heatTransfer    = self.config.meteors.material.heatTransfer,
                dragCoefficient = self.config.meteors.shape.dragCoefficient,
            )
    
    def process(self):
        pool = mp.Pool(processes = self.config.mp.processes)
        results = [pool.apply_async(simulate, (meteor, self.config.integrator.fps, self.config.integrator.spf, self.dataset.name)) for meteor in self.meteors]
        return [result.get(timeout = 10) for result in results]

    def finalize(self):
        log.info("{number} meteors written to {directory}".format(
            number      = c.num(len(self.meteors)),
            directory   = c.path(self.dataset.path('meteors')),
        ))
        log.info("Finished in {:.6f} seconds ({:.3f} meteors per second)".format(self.runTime(), len(self.meteors) / self.runTime()))

def simulate(meteor, fps, spf, dataset):
    meteor.flyRK4(fps, spf)
    meteor.save(dataset)



if __name__ == "__main__":
    log = setupLog('root')
    asmo = AsmodeusGenerate()
    asmo.configure()
    asmo.generate()
    
    asmo.process()
   
    asmo.finalize()

    log.info("Finished successfully")
    log.info("---------------------")
