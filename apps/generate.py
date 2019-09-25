#!/usr/bin/env python
"""
    Asmodeus, script 1: generate

    Generates a set of meteoroids and simulates their atmospheric entry.
    Requires: nothing
    Outputs: meteors
"""

from core                   import asmodeus, logger
from models                 import Population
from utilities              import colour as c

log = logger.setupLog('root')


class AsmodeusGenerate(asmodeus.AsmodeusMultiprocessing):
    name = 'generate'

    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-c', '--count', type = int, help = "override the total number of meteoroids to generate (only with random generator)")

    def overrideConfig(self):
        super().overrideConfig()

        self.config.parameters.generator.count = 1
        if self.args.count:
            self.overrideWarning('count', self.config.generator.parameters.count, self.args.count)
            self.config.generator.parameters.count = self.args.count

    def prepareDataset(self):
        self.dataset.resetMeteors()

    def configure(self):
        self.population = Population(self.config.generator)

    def runSpecific(self):
        self.population.generate()

        self.markTime()
        self.population.simulate(
            self.config.integrator.fps,
            self.config.integrator.spf,
            processes   = self.config.mp.processes,
            period      = self.config.mp.report,
        )

        log.info("{num} meteors were generated in {time} seconds ({rate} meteors per second)".format(
            num     = c.num(self.population.count),
            time    = c.num(f"{self.stopTime():.6f}"),
            rate    = c.num(f"{self.population.count / self.stopTime():.3f}"),
        ))

        self.markTime()
        self.population.save(self.dataset, processes = self.config.mp.processes, period = self.config.mp.report)

        log.info("{num} meteors were saved to {dir} in {time} seconds ({rate} meteors per second)".format(
            num     = c.num(self.population.count),
            time    = c.num(f"{self.stopTime():.6f}"),
            rate    = c.num(f"{self.population.count / self.stopTime():.3f}"),
            dir     = c.path(self.dataset.path('meteors')),
        ))
