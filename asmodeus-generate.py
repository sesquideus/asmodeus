#!/usr/bin/env python

import multiprocessing as mp
import datetime, random, pprint, os, shutil, logging, io, math

from core import asmodeus, configuration, dataset, logger, exceptions
from physics import coord
from distribution import position, velocity, mass, density, time
from utilities import colour as c, utilities as ut
from models.meteor import Meteor

class AsmodeusGenerate(asmodeus.Asmodeus):
    def __init__(self):
        log.info("Initializing {}".format(c.script("asmodeus-generate")))
        super().__init__() 
        self.configure()

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-c', '--count', type = int)

    def overrideConfig(self):
        super().overrideConfig()
        if (self.args.count):
            self.overrideWarning('count', self.config.meteors.count, self.args.count)
            self.config.meteors.count = self.args.count

    def configure(self):
        self.dataset.reset()
        self.dataset.create('meteors')
        
        try:
            meteors = self.config.meteors
            self.massDistribution       = mass.MassDistribution.fromConfig(meteors.mass).logInfo()
            self.positionDistribution   = position.PositionDistribution.fromConfig(meteors.position).logInfo()
            self.velocityDistribution   = velocity.VelocityDistribution.fromConfig(meteors.velocity).logInfo()
            self.densityDistribution    = density.DensityDistribution.fromConfig(meteors.material.density).logInfo()
            self.temporalDistribution   = time.TimeDistribution.fromConfig(meteors.time).logInfo()
        except AttributeError as e:
            raise exceptions.ConfigurationError

    def generate(self):
        log.info("About to generate {} meteoroids".format(c.num(self.config.meteors.count)))
     
        self.meteors = [meteor for meteor in [self.createMeteor() for _ in range(0, self.config.meteors.count)] if meteor is not None]
        log.info("{total} meteoroids survived the sin θ test ({percent}), total mass {mass}".format(
            total       = c.num(len(self.meteors)),
            percent     = c.num("{:5.2f}%".format(100 * len(self.meteors) / self.config.meteors.count)),
            mass        = c.num("{:6f} kg".format(sum(map(lambda x: x.mass, self.meteors)))),
        ))

    def createMeteor(self):
        timestamp           = self.temporalDistribution.sample()
        mass                = self.massDistribution.sample()
        density             = self.densityDistribution.sample()
        position            = self.positionDistribution.sample()
        velocityEquatorial  = self.velocityDistribution.sample()

        velocityECEF        = coord.Vector3D.fromNumpyVector((coord.rotMatrixZ(coord.earthRotationAngle(timestamp)) @ velocityEquatorial.toNumpyVector()))
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
        self.markTime()
        pool = mp.Pool(processes = self.config.mp.processes)
        results = [pool.apply_async(simulate, (meteor, self.config.integrator.fps, self.config.integrator.spf, self.dataset.name)) for meteor in self.meteors]

        for result in results:
            result.get()

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
    log = logger.setupLog('root')

    try:
        asmo = AsmodeusGenerate()
        asmo.generate()
        asmo.process()
        asmo.finalize()

        log.info("Finished successfully")
        log.info("---------------------")
    except KeyError: #exceptions.ConfigurationError as e:
        log.critical(c.err("Terminating due to a configuration error"))
