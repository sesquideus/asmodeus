#!/usr/bin/env python
"""
    Asmodeus, script 1: generate

    Generates a set of meteoroids and simulates their atmospheric entry.
    Requires: nothing
    Outputs: meteors
"""

import random
import yaml
import datetime

from core                   import asmodeus, logger, exceptions
from physics                import coord

from distribution.position  import PositionDistribution
from distribution.velocity  import VelocityDistribution
from distribution.mass      import MassDistribution
from distribution.density   import DensityDistribution
from distribution.time      import TimeDistribution

from utilities              import colour as c
from models.meteor          import Meteor


class AsmodeusGenerate(asmodeus.Asmodeus):
    name = 'generate'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-c', '--count', type = int)

    def overrideConfig(self):
        super().overrideConfig()
        if self.args.count:
            self.overrideWarning('count', self.config.meteors.count, self.args.count)
            self.config.meteors.count = self.args.count

    def configure(self):
        if self.dataset.exists('meteors') and not self.config.overwrite:
            raise exceptions.OverwriteError(c.path(self.dataset.path('meteors')))
        else:
            self.dataset.reset()
            self.dataset.create('meteors')

        try:
            log.info("Configuring meteoroid property distributions")

            meteors = self.config.meteors
            self.massDistribution       = MassDistribution.fromConfig(meteors.mass).logInfo()
            self.positionDistribution   = PositionDistribution.fromConfig(meteors.position).logInfo()
            self.velocityDistribution   = VelocityDistribution.fromConfig(meteors.velocity).logInfo()
            self.densityDistribution    = DensityDistribution.fromConfig(meteors.material.density).logInfo()
            self.temporalDistribution   = TimeDistribution.fromConfig(meteors.time).logInfo()

            log.info(f"Output will be written to dataset {c.name(self.dataset.name)} ({c.path(self.dataset.root())})")

        except AttributeError as e:
            raise exceptions.ConfigurationError(e)

        return self

    def run(self):
        self.generate()
        self.process()
        self.finalize()

    def generate(self):
        log.info(f"Generating {c.num(self.config.meteors.count)} meteoroids "
                f"using {c.num(self.config.mp.processes)} processes "
                f"at {c.num(self.config.meteors.integrator.fps)} frames per second, "
                f"with {c.num(self.config.meteors.integrator.spf)} steps per frame")

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
        args = [(
            meteor,
            self.config.meteors.integrator.fps,
            self.config.meteors.integrator.spf,
            self.dataset.name
        ) for meteor in self.meteors]

        self.meteors = self.parallel(simulate, args, action = "Simulating meteors")
        self.count = len(self.meteors)

    def finalize(self):
        yaml.dump({
            'count':        len(self.meteors),
            'generated':    datetime.datetime.now().isoformat(),
        }, open(self.dataset.path('meteors.yaml'), 'w'), default_flow_style = False)

        log.info("{num} meteors were generated in {time} seconds ({rate} meteors per second) and saved to {dir}".format(
            num     = c.num(len(self.meteors)),
            time    = c.num(f"{self.runTime():.6f}"),
            rate    = c.num(f"{len(self.meteors) / self.runTime():.3f}"),
            dir     = c.path(self.dataset.path('meteors')),
        ))
        self.ok = True


def simulate(args):
    queue, meteor, fps, spf, dataset = args
    queue.put(1)
    meteor.flyRK4(fps, spf)
    meteor.save(dataset)


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusGenerate()
    asmo.run()
