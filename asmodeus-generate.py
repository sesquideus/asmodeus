#!/usr/bin/env python

import multiprocessing as mp
import datetime, random, pprint, os, shutil, logging, io, math

from core import asmodeus, coord, configuration, dataset, logger, exceptions
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
        meteors = self.config.meteors
        
        try:
            self.massDistribution       = mass.MassDistribution().create(meteors.mass.distribution, **meteors.mass.parameters._asdict())
            self.distributionInfo("Particle mass", meteors.mass.distribution, meteors.mass.parameters)

            self.positionDistribution   = position.distribution(meteors.position.distribution, **meteors.position.parameters._asdict())
            self.distributionInfo("Initial position", meteors.position.distribution, meteors.position.parameters)
            
            self.velocityDistribution   = velocity.distribution(meteors.velocity.distribution, **meteors.velocity.parameters._asdict())
            self.distributionInfo("Initial velocity", meteors.velocity.distribution, meteors.velocity.parameters)

            self.densityDistribution    = density.DensityDistribution().create(meteors.material.density.distribution, **meteors.material.density.parameters._asdict())
            self.distributionInfo("Particle density", meteors.material.density.distribution, meteors.material.density.parameters)

            self.temporalDistribution   = time.TimeDistribution().create(meteors.time.distribution, **meteors.time.parameters._asdict())
            self.distributionInfo("Temporal", meteors.time.distribution, meteors.time.parameters)
        except AttributeError as e:
            raise exceptions.ConfigurationError

        self.dataset.reset()
        self.dataset.create('meteors')

    def generate(self):
        log.info("About to generate {} meteoroids".format(c.num(self.config.meteors.count)))
     
        self.meteors = [meteor for meteor in [self.createMeteor() for _ in range(0, self.config.meteors.count)] if meteor is not None]
        log.info("{total} meteoroids survived the sin θ test ({percent}), total mass {mass}".format(
            total       = c.num(len(self.meteors)),
            percent     = c.num("{:5.2f}%".format(100 * len(self.meteors) / self.config.meteors.count)),
            mass        = c.num("{:6f} kg".format(sum(map(lambda x: x.mass, self.meteors)))),
        ))

    def createMeteor(self):
        timestamp           = self.temporalDistribution()
        mass                = self.massDistribution()
        density             = self.densityDistribution()
        position            = self.positionDistribution()
        velocityEquatorial  = self.velocityDistribution()

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
    log = logger.setupLog('root')

    try:
        asmo = AsmodeusGenerate()
        asmo.generate()
        asmo.process()
        asmo.finalize()

        log.info("Finished successfully")
        log.info("---------------------")
    except exceptions.ConfigurationError as e:
        log.critical(c.err("Terminating due to a configuration error"))
