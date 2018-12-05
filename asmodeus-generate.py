#!/usr/bin/env python
"""
    Asmodeus, script 1: generate
    Generates a set of meteoroids and simulates their atmospheric entry.
    Requires: nothing
    Outputs: meteors
"""

import multiprocessing as mp
import time
import random
import sys
import yaml
import datetime

from core           import asmodeus, logger, exceptions
from physics        import coord

from distribution.position  import PositionDistribution
from distribution.velocity  import VelocityDistribution
from distribution.mass      import MassDistribution
from distribution.density   import DensityDistribution
from distribution.time      import TimeDistribution

from utilities      import colour as c
from models.meteor  import Meteor


class AsmodeusGenerate(asmodeus.Asmodeus):
    def __init__(self):
        self.name = 'generate'
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
        
            log.info("Output will be written to dataset {ds} ({dsdir})".format(
                ds              = c.name(self.dataset.name),
                dsdir           = c.path(self.dataset.root()),
            ))

        except AttributeError:
            raise exceptions.ConfigurationError()

        return self

    def run(self):
        self.generate()
        self.process()
        self.finalize()

    def generate(self):
        log.info("Generating {num} meteoroids using {proc} processes at {fps} frames per second, with {spf} steps per frame".format(
            num             = c.num(self.config.meteors.count),
            proc            = c.num(self.config.mp.processes),
            fps             = c.num(self.config.meteors.integrator.fps),
            spf             = c.num(self.config.meteors.integrator.spf),
        ))

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
        manager     = mp.Manager()
        queue       = manager.Queue()

        args = [(
            queue,
            meteor,
            self.config.meteors.integrator.fps,
            self.config.meteors.integrator.spf,
            self.dataset.name
        ) for meteor in self.meteors]
        total = len(args)

        results = pool.map_async(simulate, args, 20)
        
        while True:
            if results.ready():
                break
            else:
                log.info("Simulating meteors: {count} of {total} ({perc})".format(
                    count       = c.num("{:6d}".format(queue.qsize())),
                    total       = c.num("{:6d}".format(total)),
                    perc        = c.num("{:5.2f}%".format(queue.qsize() / total * 100)),
                ))
                time.sleep(0.25)

        out = results.get()
        self.count = len(out)

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


def simulate(args):
    queue, meteor, fps, spf, dataset = args
    queue.put(1)
    meteor.flyRK4(fps, spf)
    meteor.save(dataset)


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusGenerate()
    asmo.run()
