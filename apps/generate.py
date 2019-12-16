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

    def create_argparser(self):
        super().create_argparser()
        self.argparser.add_argument('-c', '--count', type=int, help="override the total number of meteoroids to generate (only with random generator)")
        self.argparser.add_argument('-s', '--streaks', action='store_true', help="Save observations as streaks (all frames will be recorded)")

    def override_config(self):
        super().override_config()

        if self.args.count:
            self.override_warning('count', self.config.generator.parameters.count, self.args.count)
            self.config.generator.parameters.count = self.args.count

        self.config.streaks = False
        if self.args.streaks:
            self.override_warning('streaks', self.config.streaks, self.args.streaks)
            self.config.streaks = True

    def prepare_dataset(self):
        self.dataset.reset_meteors()

    def configure(self):
        self.population = Population(self.config.generator, streaks = self.config.streaks)

    def run_specific(self):
        self.population.generate()

        self.mark_time()
        self.population.simulate(
            self.config.integrator.fps,
            self.config.integrator.spf,
            processes   = self.config.mp.processes,
            period      = self.config.mp.report,
        )

        log.info("Generating took {time} s ({meteor_rate} meteors/s, {frame_rate} frames/s)".format(
            time        = c.num(f"{self.stop_time():.6f}"),
            meteor_rate = c.num(f"{self.population.count / self.stop_time():.3f}"),
            frame_rate  = c.num(f"{self.population.total_frames / self.stop_time():.3f}"),
        ))

        self.mark_time()
        self.population.save(self.dataset, processes=self.config.mp.processes, period=self.config.mp.report)

        log.info("{num} meteors were saved to {dir} in {time} seconds ({rate} meteors per second)".format(
            num     = c.num(self.population.count),
            frames  = c.num(self.population.total_frames),
            time    = c.num(f"{self.stop_time():.6f}"),
            rate    = c.num(f"{self.population.count / self.stop_time():.3f}"),
            dir     = c.path(self.dataset.path('meteors')),
        ))
