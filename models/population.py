import datetime
import io
import os
import logging
import random
import yaml

import time
import multiprocessing as mp

from core.parallel      import parallel
from core               import exceptions
from distribution       import PositionDistribution, VelocityDistribution, MassDistribution, DensityDistribution, TimeDistribution, DragCoefficientDistribution
from models.meteor      import Meteor
from physics            import coord
from utilities          import colour as c

log = logging.getLogger('root')


class Population():
    def __init__(self, parameters):
        self.parameters = parameters
        
        try:
            log.info("Configuring meteoroid property distributions")
            self.massDistribution               = MassDistribution.fromConfig(self.parameters.mass).logInfo()
            self.positionDistribution           = PositionDistribution.fromConfig(self.parameters.position).logInfo()
            self.velocityDistribution           = VelocityDistribution.fromConfig(self.parameters.velocity).logInfo()
            self.densityDistribution            = DensityDistribution.fromConfig(self.parameters.material.density).logInfo()
            self.temporalDistribution           = TimeDistribution.fromConfig(self.parameters.time).logInfo()
            self.dragCoefficientDistribution    = DragCoefficientDistribution.fromConfig(self.parameters.shape.dragCoefficient).logInfo()
        except AttributeError as e:
            raise exceptions.ConfigurationError(e) from e

    def generate(self):
        log.info(f"Generating {c.num(self.parameters.count)} meteoroids")
        self.count = 0
        self.iterations = 0
        self.meteors = []

        while (self.count < self.parameters.count):
            self.generateMeteoroid()
            
    def generateMeteoroid(self):
        mass                = self.massDistribution.sample()
        density             = self.densityDistribution.sample()
        timestamp           = self.temporalDistribution.sample()
        position            = self.positionDistribution.sample()
        dragCoefficient     = self.dragCoefficientDistribution.sample()
        velocityEquatorial  = self.velocityDistribution.sample()

        velocityECEF        = coord.Vector3D.fromNumpyVector((coord.rotMatrixZ(coord.earthRotationAngle(timestamp)) @ velocityEquatorial.toNumpyVector()))
        entryAngleSin       = -position * velocityECEF / (position.norm() * velocityECEF.norm())

        self.iterations += 1
        if entryAngleSin > random.random():
            self.meteors.append(Meteor(
                mass            = mass,
                density         = density,
                timestamp       = timestamp,
                velocity        = velocityECEF,
                position        = position,
                ablationHeat    = self.parameters.material.ablationHeat,
                heatTransfer    = self.parameters.material.heatTransfer,
                dragCoefficient = dragCoefficient,
            ))
            self.count += 1

    def simulate(self, processes, fps, spf):
        log.info(f"Simulating atmospheric entry: using {c.num(processes)} processes at {c.num(fps)} frames per second, with {c.num(spf)} steps per frame")
        self.meteors = parallel(
            simulate,
            self.meteors,
            initializer     = initialize,
            initargs        = (fps, spf),
            processes       = min(self.count, processes),
            action          = "Simulating meteors",
        )
        log.info("Total mass {mass}, effective area {area}".format(
            area            = c.num(f"{self.parameters.count / self.iterations * 100:5.2f}%"),
            mass            = c.num("{:6f} kg".format(sum(map(lambda x: x.initMass, self.meteors)))),
        ))

    def save(self, directory):
        log.debug(f"Saving the population to {c.path(directory)}")
        for meteor in self.meteors:
            meteor.save(directory)

    def saveMetadata(self, directory):
        yaml.dump({
            'count':            self.count,
            'generated':        datetime.datetime.now().isoformat(),
            'distributions':    {
                'mass':             self.massDistribution.asDict(),
                'density':          self.densityDistribution.asDict(),
                'timestamp':        self.temporalDistribution.asDict(),
                'position':         self.positionDistribution.asDict(),
                'dragCoefficient':  self.dragCoefficientDistribution.asDict(),
                'velocity':         self.velocityDistribution.asDict(),
            },
        }, open(os.path.join(directory, 'meteors.yaml'), 'w'), default_flow_style = False)

def initialize(queuex, fpsx, spfx):
    global fps, spf, queue
    fps, spf, queue = fpsx, spfx, queuex

def worker(args):
    queue, = args
    position            = pd.sample()
    velocity            = vd.sample()
    timestamp           = td.sample()
    velocityECEF        = coord.Vector3D.fromNumpyVector((coord.rotMatrixZ(coord.earthRotationAngle(timestamp)) @ velocity.toNumpyVector()))
    entryAngleSin       = -position * velocityECEF / (position.norm() * velocityECEF.norm())
    queue.put(1)

    if random.random() < entryAngleSin:
        meteor = Meteor(
            timestamp       = timestamp,
            mass            = md.sample(),
            density         = dd.sample(),
            velocity        = velocityECEF,
            position        = position,
            ablationHeat    = ah,
            heatTransfer    = ht,
            dragCoefficient = dc,
        )
        meteor.flyRK4(fps, spf)
        return meteor
    else:
        return None

def simulate(meteor):
    meteor.flyRK4(fps, spf)
    queue.put(1)
    return meteor
