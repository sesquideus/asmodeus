import logging
import random
import dotmap
import numbers
import datetime
import numpy as np
import pandas

from core               import exceptions
from distribution       import PositionDistribution, VelocityDistribution, MassDistribution, \
    DensityDistribution, TimeDistribution, DragCoefficientDistribution
from models             import Meteor
from physics            import coord
from utilities          import colour as c, utilities

log = logging.getLogger('root')


class Generator():
    @classmethod
    def fromConfig(cls, config):
        config._dynamic = False
        return {
            'grid':     GeneratorGrid,
            'random':   GeneratorRandom,
        }[config.method](config.parameters)


class GeneratorGrid(Generator):
    method = 'grid'

    def __init__(self, parameters):
        self.parameters = parameters

    def getSpaceRange(self, *, min, max, count, spacing = 'linear', time = False):
        space = {
            'linear':   np.linspace,
            'log':      np.geomspace,
        }[spacing]

        if isinstance(min, datetime.datetime):
            return pandas.date_range(min, max, count).to_pydatetime()
        else:
            return space(min, max, count, dtype = float)
    def getSpace(self, definition):
        try:
            if isinstance(definition, dotmap.DotMap):
                return self.getSpaceRange(**definition.toDict())
            elif isinstance(definition, numbers.Number) or isinstance(definition, datetime.datetime):
                return [definition]
            else:
                raise exceptions.ConfigurationError(f"Parameter space definition must be either a number or a dictionary with min, max and count defined")
        except TypeError as e:
            raise exceptions.ConfigurationError(e)

    def generate(self):
        self.meteors = []
        space = utilities.dictProduct(
            mass                = self.getSpace(self.parameters.mass),

            density             = self.getSpace(self.parameters.material.density),
            heatTransfer        = self.getSpace(self.parameters.material.heatTransfer),
            ablationHeat        = self.getSpace(self.parameters.material.ablationHeat),

            dragCoefficient     = self.getSpace(self.parameters.shape.dragCoefficient),
            shapeFactor         = self.getSpace(self.parameters.shape.shapeFactor),

            latitude            = self.getSpace(self.parameters.position.latitude),
            longitude           = self.getSpace(self.parameters.position.longitude),
            elevation           = self.getSpace(self.parameters.position.elevation),

            ra                  = self.getSpace(self.parameters.velocity.ra),
            dec                 = self.getSpace(self.parameters.velocity.dec),
            speed               = self.getSpace(self.parameters.velocity.speed),

            time                = self.getSpace(self.parameters.time),
        )

        for raw in space:
            velocityEquatorial  = VelocityDistribution.shower(ra = raw['ra'], dec = raw['dec'], speed = raw['speed'])()
            velocity            = coord.Vector3D.fromNumpyVector(
                                    (coord.rotMatrixZ(coord.earthRotationAngle(raw['time'])) @ velocityEquatorial.toNumpyVector())
                                )

            self.meteors.append(Meteor(
                mass            = raw['mass'],
                density         = raw['density'],
                timestamp       = raw['time'],
                position        = coord.Vector3D.fromGeodetic(raw['latitude'], raw['longitude'], raw['elevation']),
                dragCoefficient = raw['dragCoefficient'],
                velocity        = velocity,
                ablationHeat    = raw['ablationHeat'],
            ))

        self.count = len(self.meteors)
        self.iterations = None

        return self.meteors

    def asDict(self):
        return {
            'method':           self.method,
            'count':            self.count,
            'iterations':       None,
            'parameters':       self.parameters.toDict(),
        }


class GeneratorRandom(Generator):
    method  = 'random'

    def __init__(self, parameters):
        self.parameters = parameters

        self.massDistribution               = MassDistribution.fromConfig(self.parameters.mass).logInfo()
        self.positionDistribution           = PositionDistribution.fromConfig(self.parameters.position).logInfo()
        self.velocityDistribution           = VelocityDistribution.fromConfig(self.parameters.velocity).logInfo()
        self.densityDistribution            = DensityDistribution.fromConfig(self.parameters.material.density).logInfo()
        self.temporalDistribution           = TimeDistribution.fromConfig(self.parameters.time).logInfo()
        self.dragCoefficientDistribution    = DragCoefficientDistribution.fromConfig(self.parameters.shape.dragCoefficient).logInfo()

    def generateOne(self):
        mass                = self.massDistribution.sample()
        density             = self.densityDistribution.sample()
        timestamp           = self.temporalDistribution.sample()
        position            = self.positionDistribution.sample()
        dragCoefficient     = self.dragCoefficientDistribution.sample()
        velocityEquatorial  = self.velocityDistribution.sample()

        velocityECEF        = coord.Vector3D.fromNumpyVector(
                                (coord.rotMatrixZ(coord.earthRotationAngle(timestamp)) @ velocityEquatorial.toNumpyVector())
                            )
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

    def generate(self):
        log.info(f"Generating {c.num(self.parameters.count)} meteoroids")
        self.count = 0
        self.iterations = 0
        self.meteors = []

        while (self.count < self.parameters.count):
            self.generateOne()

        log.info("Needed {iterations} candidate{s}, effective area {area}".format(
            iterations      = c.num(self.iterations),
            area            = c.num(f"{self.parameters.count / self.iterations * 100:5.2f}%"),
            s               = 's' if self.iterations > 1 else '',
        ))

        return self.meteors

    def asDict(self):
        return {
            'method':           self.method,
            'count':            self.count,
            'iterations':       self.iterations,
            'parameters':       {
                'mass':             self.massDistribution.asDict(),
                'time':             self.temporalDistribution.asDict(),
                'position':         self.positionDistribution.asDict(),
                'velocity':         self.velocityDistribution.asDict(),
                'material':         {
                    'density':          self.densityDistribution.asDict(),
                },
                'shape':        {
                    'dragCoefficient':  self.dragCoefficientDistribution.asDict(),
                },
            },
        }
