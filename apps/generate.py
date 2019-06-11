"""
    Asmodeus, script 1: generate

    Generates a set of meteoroids and simulates their atmospheric entry.
    Requires: nothing
    Outputs: meteors
"""

import argparse
import datetime
import random
import yaml

from core                   import asmodeus, logger, exceptions
from core                   import Population

from distribution           import PositionDistribution, VelocityDistribution, MassDistribution, DensityDistribution, TimeDistribution
from utilities              import colour as c

log = logger.setupLog('root')


class AsmodeusGenerate(asmodeus.AsmodeusMultiprocessing):
    name = 'generate'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('config',                   type = argparse.FileType('r'))
        self.argparser.add_argument('-O', '--overwrite',        action = 'store_true')
        self.argparser.add_argument('-c', '--count',            type = int)

    def buildConfig(self):
        self.config = self.loadConfigFile(self.args.config)

    def overrideConfig(self):
        super().overrideConfig()
        if self.args.count:
            self.overrideWarning('count', self.config.meteors.count, self.args.count)
            self.config.meteors.count = self.args.count

    def prepareDataset(self):
        self.protectOverwrite()
        self.protectOverwrite('meteors')

    def configure(self):
        self.population = Population(self.config.meteors)
        self.root = self.dataset.path('meteors')

    def runSpecific(self):
        self.population.generate()

        self.markTime()
        self.population.simulate(self.config.mp.processes, self.config.meteors.integrator.fps, self.config.meteors.integrator.spf)
        log.info("{num} meteors were generated in {time} seconds ({rate} meteors per second)".format(
            num     = c.num(self.population.parameters.count),
            time    = c.num(f"{self.stopTime():.6f}"),
            rate    = c.num(f"{self.population.parameters.count / self.stopTime():.3f}"),
        ))
        
        self.markTime()
        self.population.save(self.root)
        self.population.saveMetadata(self.dataset.path())

        log.info("{num} meteors were saved to {dir} in {time} seconds ({rate} meteors per second)".format(
            num     = c.num(self.population.parameters.count),
            time    = c.num(f"{self.stopTime():.6f}"),
            rate    = c.num(f"{self.population.parameters.count / self.stopTime():.3f}"),
            dir     = c.path(self.dataset.path('meteors')),
        ))
