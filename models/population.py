import datetime
import io
import os
import logging
import random
import yaml

import time
import multiprocessing as mp

from core.parallel      import parallel
from core               import exceptions, configuration
from core.dataset       import Dataset
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

    @classmethod
    def fromDataset(cls, dataset):
        try:
            config = configuration.loadYAML(open(dataset.path('meteors.yaml'), 'r'))

            if not dataset.isDir('meteors'):
                raise exceptions.PrerequisiteError("There is no {c.path('meteors')} directory in dataset {c.name(dataset.name)}")

            if len(dataset.listDir('meteors')) != config.count:
                raise exceptions.PrerequisiteError("YAML file does not match contents")

            

        except FileNotFoundError as e:
            log.error(f"Could not load configuration file {c.path(filename)}: {e}")
            raise exceptions.PrerequisiteError(e) from e
        except yaml.composer.ComposerError as e:
            log.error("YAML composer error")
            raise exceptions.PrerequisiteError(e) from e

    def generate(self):
        log.info(f"Generating {c.num(self.parameters.count)} meteoroids")
        self.count = 0
        self.iterations = 0
        self.meteors = []

        while (self.count < self.parameters.count):
            self.generateMeteoroid()

        log.info("Needed {iterations} candidate{s}, effective area {area}".format(
            iterations      = c.num(self.iterations),
            area            = c.num(f"{self.parameters.count / self.iterations * 100:5.2f}%"),
            s               = 's' if self.iterations > 1 else '',
        ))
            
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
        log.info("Total mass {mass}".format(
            mass            = c.num("{:6f} kg".format(sum(map(lambda x: x.initMass, self.meteors)))),
        ))

    def save(self, directory):
        log.debug(f"Saving the population to {c.path(directory)}")
        for meteor in self.meteors:
            meteor.save(directory)

    def saveMetadata(self, directory):
        yaml.dump({
            'count':            self.count,
            'iterations':       self.iterations,
            'timestamp':        datetime.datetime.now().isoformat(),
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


def simulate(meteor):
    meteor.flyRK4(fps, spf)
    queue.put(1)
    return meteor
