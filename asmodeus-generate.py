#!/usr/bin/env python
"""
    Generates a set of meteoroids and simulates their atmospheric entry.
"""

import multiprocessing as mp
import random
import sys
import yaml
import datetime

from core           import asmodeus, logger, exceptions
from physics        import coord
from distribution   import position, velocity, mass, density, time
from utilities      import colour as c
from models.meteor  import Meteor


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
        if self.dataset.exists('meteors') and not self.config.overwrite:
            raise exceptions.OverwriteError(c.path(self.dataset.path('meteors')))
        else:
            self.dataset.reset()
            self.dataset.create('meteors')

        try:
            meteors = self.config.meteors
            self.massDistribution       = mass.MassDistribution.fromConfig(meteors.mass).logInfo()
            self.positionDistribution   = position.PositionDistribution.fromConfig(meteors.position).logInfo()
            self.velocityDistribution   = velocity.VelocityDistribution.fromConfig(meteors.velocity).logInfo()
            self.densityDistribution    = density.DensityDistribution.fromConfig(meteors.material.density).logInfo()
            self.temporalDistribution   = time.TimeDistribution.fromConfig(meteors.time).logInfo()
        except AttributeError:
            raise exceptions.ConfigurationError

        return self

    def run(self):
        self.generate()
        self.process()
        self.finalize()

    def reportStatus(self):
        log.info("{name} output to dataset {ds} ({dsdir})".format(
            name            = c.script('asmodeus-generate'),
            ds              = c.name(self.config.dataset),
            dsdir           = c.path(self.config.dataset.root),
        ))

    def generate(self):
        log.info("About to generate {} meteoroids using {} processes".format(c.num(self.config.meteors.count), c.num(self.config.mp.processes)))

        self.meteors = [meteor for meteor in [self.createMeteor() for _ in range(0, self.config.meteors.count)] if meteor is not None]
        log.info("{total} meteoroids survived the sin θ test ({percent}), total mass {mass}".format(
            total           = c.num(len(self.meteors)),
            percent         = c.num("{:5.2f}%".format(100 * len(self.meteors) / self.config.meteors.count)),
            mass            = c.num("{:6f} kg".format(sum(map(lambda x: x.mass, self.meteors)))),
        ))

    def createMeteor(self):
        timestamp           = self.temporalDistribution.sample()
        mass                = self.massDistribution.sample()
        density             = self.densityDistribution.sample()
        position            = self.positionDistribution.sample()
        velocityEquatorial  = self.velocityDistribution.sample()

        velocityECEF        = coord.Vector3D.fromNumpyVector((coord.rotMatrixZ(coord.earthRotationAngle(timestamp)) @ velocityEquatorial.toNumpyVector()))
        entryAngleSin       = -position * velocityECEF / (position.norm() * velocityECEF.norm())

        rnd                 = random.random()
        accepted            = rnd < entryAngleSin

        log.debug("Meteoroid {status}: sine of entry angle {sin:.6f}, random value {rnd:.6f}".format(
            status          = c.ok('accepted') if accepted else c.err('rejected'),
            sin             = entryAngleSin,
            rnd             = rnd,
        ))

        return Meteor(
            mass            = mass,
            density         = density,
            velocity        = velocityECEF,
            position        = position,
            timestamp       = timestamp,
            ablationHeat    = self.config.meteors.material.ablationHeat,
            heatTransfer    = self.config.meteors.material.heatTransfer,
            dragCoefficient = self.config.meteors.shape.dragCoefficient,
        ) if accepted else None

    def process(self):
        self.markTime()
        pool = mp.Pool(processes = self.config.mp.processes)
        results = [
            pool.apply_async(
                simulate, (meteor, self.config.meteors.integrator.fps, self.config.meteors.integrator.spf, self.dataset.name)
            ) for meteor in self.meteors
        ]

        for result in results:
            result.get()

    def finalize(self):
        yaml.dump({
            'count':        len(self.meteors),
            'generated':    datetime.datetime.now().isoformat(),
        }, open(self.dataset.path('meteors.yaml'), 'w'), default_flow_style = False)

        log.info("{num} meteors were generated in {time} seconds ({rate} meteors per second) and saved to {dir}".format(
            num     = c.num(len(self.meteors)),
            time    = c.num("{:.6f}".format(self.runTime())),
            rate    = c.num("{:.3f}".format(len(self.meteors) / self.runTime())),
            dir     = c.path(self.dataset.path('meteors')),
        ))


def simulate(meteor, fps, spf, dataset):
    meteor.flyRK4(fps, spf)
    meteor.save(dataset)


if __name__ == "__main__":
    log = logger.setupLog('root')
    try:
        asmo = AsmodeusGenerate()
        asmo.run()
    except exceptions.ConfigurationError as e:
        log.critical("Configuration error \"{}\", terminating".format(e))
        sys.exit(-1)
    except exceptions.OverwriteError as e:
        log.critical("Target directory {} already exists, terminating".format(e))
        sys.exit(-1)
    finally:
        log.info("---------------------")
