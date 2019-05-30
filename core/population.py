import datetime
import io
import os
import logging
import random

from core.parallel      import parallel
from distribution       import PositionDistribution, VelocityDistribution, MassDistribution, DensityDistribution, TimeDistribution
from models.meteor      import Meteor
from physics            import coord
from utilities          import colour as c

log = logging.getLogger('root')


class Population():
    def __init__(self, parameters):
        self.parameters = parameters
        
        try:
            log.info("Configuring meteoroid property distributions")
            self.massDistribution       = MassDistribution.fromConfig(self.parameters.mass).logInfo()
            self.positionDistribution   = PositionDistribution.fromConfig(self.parameters.position).logInfo()
            self.velocityDistribution   = VelocityDistribution.fromConfig(self.parameters.velocity).logInfo()
            self.densityDistribution    = DensityDistribution.fromConfig(self.parameters.material.density).logInfo()
            self.temporalDistribution   = TimeDistribution.fromConfig(self.parameters.time).logInfo()
        except AttributeError as e:
            raise exceptions.ConfigurationError(e)

    def generate(self):
        log.info(f"Generating {c.num(self.parameters.count)} meteoroids")

        self.meteors = parallel(generate, args, processes = 4, action = "Generating meteoroids")
        self.count = len(self.meteors)

    def simulate(self, processes, fps, spf):
        log.info(f"Simulating atmospheric entry: using {c.num(processes)} processes at {c.num(fps)} frames per second, with {c.num(spf)} steps per frame")
        args = [(
            self.temporalDistribution.sample(),
            self.massDistribution.sample(),
            self.densityDistribution.sample(),
            self.positionDistribution.sample(),
            self.velocityDistribution.sample(),
            self.parameters.material.ablationHeat,
            self.parameters.material.heatTransfer,
            self.parameters.shape.dragCoefficient,
            fps, spf, os.path.join('datasets', 'plys', 'meteors')
        ) for _ in range(0, self.parameters.count)]

        meteors = parallel(simulate, args, processes = processes, action = "Simulating meteors")
        self.meteors = list(filter(None.__ne__, meteors))
        self.count = len(self.meteors)
        log.info("{total} meteoroids survived the sin θ test ({percent}), total mass {mass}".format(
            total           = c.num(self.count),
            percent         = c.num(f"{100 * len(self.meteors) / self.parameters.count:5.2f}%"),
            mass            = c.num("{:6f} kg".format(sum(map(lambda x: x.initMass, self.meteors)))),
        ))

    def save(self, directory, processes = 1):
        log.info(f"Saving the population to {c.path(directory)}")
        
        for meteor in self.meteors:
            meteor.save(directory)

    def saveMetadata(self, fileName):
        yaml.dump({
            'count':        self.count,
            'timestamp':    datetime.datetime.now().isoformat(),
        }, open(self.dataset.path('meteors.yaml'), 'w'), default_flow_style = False)

        
def simulate(args):
    queue, timestamp, mass, density, position, velocityEquatorial, ablationHeat, heatTransfer, dragCoefficient, fps, spf = args
    queue.put(1)

    velocityECEF        = coord.Vector3D.fromNumpyVector((coord.rotMatrixZ(coord.earthRotationAngle(timestamp)) @ velocityEquatorial.toNumpyVector()))
    entryAngleSin       = -position * velocityECEF / (position.norm() * velocityECEF.norm())

    rnd                 = random.random()
    accepted            = rnd < entryAngleSin

    log.debug("Meteoroid {status}: sine of entry angle {sin:.6f}, random value {rnd:.6f}".format(
        status          = c.ok('accepted') if accepted else c.err('rejected'),
        sin             = entryAngleSin,
        rnd             = rnd,
    ))

    if random.random() < entryAngleSin:
        meteor = Meteor(
            mass            = mass,
            density         = density,
            velocity        = velocityECEF,
            position        = position,
            timestamp       = timestamp,
            ablationHeat    = ablationHeat,
            heatTransfer    = heatTransfer,
            dragCoefficient = dragCoefficient,
        )
        meteor.flyRK4(fps, spf)
        return meteor
    else:
        return None
