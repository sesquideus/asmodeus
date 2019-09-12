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

from core                   import asmodeus, logger
from models                 import Population
from utilities              import colour as c

log = logger.setupLog('root')


class AsmodeusGenerate(asmodeus.AsmodeusMultiprocessing):
    name = 'generate'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-c', '--count',            type = int)

    def buildConfig(self):
        self.config = self.loadConfigFile(self.args.config)

    def overrideConfig(self):
        super().overrideConfig()
        if self.args.count:
            self.overrideWarning('count', self.config.meteors.count, self.args.count)
            self.config.meteors.count = self.args.count

    def prepareDataset(self):
        self.dataset.resetMeteors()

    def configure(self):
        self.root = self.dataset.path('meteors')
        self.population = Population(self.config.meteors)

    def runSpecific(self):
        self.population.generate()

        self.markTime()
        self.population.simulate(self.config.meteors.integrator.fps, self.config.meteors.integrator.spf, processes = self.config.mp.processes, period = self.config.mp.report)
        log.info("{num} meteors were generated in {time} seconds ({rate} meteors per second)".format(
            num     = c.num(self.population.parameters.count),
            time    = c.num(f"{self.stopTime():.6f}"),
            rate    = c.num(f"{self.population.parameters.count / self.stopTime():.3f}"),
        ))
        
        self.markTime()
        self.population.save(self.dataset)

        log.info("{num} meteors were saved to {dir} in {time} seconds ({rate} meteors per second)".format(
            num     = c.num(self.population.parameters.count),
            time    = c.num(f"{self.stopTime():.6f}"),
            rate    = c.num(f"{self.population.parameters.count / self.stopTime():.3f}"),
            dir     = c.path(self.dataset.path('meteors')),
        ))
