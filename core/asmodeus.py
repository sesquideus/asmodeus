import argparse
import os
import sys
import dotmap
import multiprocessing as mp
import logging
import time
import yaml

from core import dataset, exceptions
from utilities import colour as c

from models.observer import Observer

log = logging.getLogger('root')


class Asmodeus():
    def __init__(self):
        self.ok = False
        log.info("Initializing {}".format(c.script("asmodeus-{}".format(self.name))))
        self.createArgparser()
        self.args = self.argparser.parse_args()

        try:    
            self.buildConfig()
            self.dataset = dataset.Dataset(self.args.dataset)
            self.overrideConfig()
            self.configure()
        except exceptions.CommandLineError as e:
            log.critical("Incorrect command line arguments")
            sys.exit(-1)
        except exceptions.ConfigurationError as e:
            log.critical(f"Terminating due to a configuration error: {e}")
            sys.exit(-1)
        except exceptions.OverwriteError as e:
            log.critical(f"Target directory {e} already exists (use --overwrite)")
            sys.exit(-1)
        except exceptions.PrerequisiteError:
            log.critical("Missing prerequisites, aborting")
            sys.exit(-1)

        log.info("Initialization complete")

    def createArgparser(self):
        self.argparser = argparse.ArgumentParser(description = "All-Sky Meteor Observation and Detection Efficiency Simulator")
        self.argparser.add_argument('dataset',                  type = str)
        self.argparser.add_argument('-d', '--debug',            action = 'store_true')
        self.argparser.add_argument('-l', '--logfile',          type = argparse.FileType('w'))

    @classmethod
    def loadConfigFile(self, file):
        try:
            config = yaml.safe_load(file)
        except FileNotFoundError as e:
            log.error("Could not load configuration file {}: {}".format(configFile, e))
            raise exceptions.CommandLineError()
        except yaml.composer.ComposerError as e:
            log.error("Undefined alias detected")
            raise exceptions.ConfigurationError(e)

        return dotmap.DotMap(config, _dynamic = False)

    def buildConfig(self):
        raise NotImplementedError("You need to define the buildConfig method for every ASMODEUS subclass.")

    def protectOverwrite(self, stage, *, fullReset = False):
        if self.dataset.exists(stage) and not self.config.overwrite:
            raise exceptions.OverwriteError(c.path(self.dataset.path(stage)))
        else:
            if fullReset:
                self.dataset.reset()
            self.dataset.reset(stage)

    def requireStage(self, stage, program):
        try:
            self.dataset.require(stage)
        except FileNotFoundError as e:
            log.error("Could not load meteors from {s} -- did you run {gen}?".format(
                s   = c.path(self.dataset.path(stage)),
                gen = c.script(program),
            ))
            raise exceptions.PrerequisiteError()

    def overrideConfig(self):
        log.setLevel(logging.DEBUG if self.args.debug else logging.INFO)
        if self.args.debug:
            log.warning(f"Debug output is {c.over('active')}")

        if self.args.overwrite:
            log.warning(f"Dataset overwrite {c.over('enabled')}")
            self.config.overwrite = True
        else:
            self.config.overwrite = False

        if self.args.logfile:
            log.addHandler(logging.FileHandler(self.args.logfile.name))
            log.warning(f"Added log output {c.over(self.args.logfile.name)}")

    def markTime(self):
        self.startTime = time.time()

    def runTime(self):
        return time.time() - self.startTime

    def run(self):
        try:
            self.runSpecific()
        except exceptions.ConfigurationError as e:
            log.critical(f"Terminating due to a configuration error: {e}")
        finally:
            if self.ok:
                log.info("{} finished successfully".format(c.script(f"asmodeus-{self.name}")))
            else:
                log.critical("{} aborted".format(c.script(f"asmodeus-{self.name}")))
            log.info("-" * 50)

    def loadObservers(self):
        self.observers = []
        for oid, obs in self.config.observations.observers.items():
            self.observers.append(Observer(oid, self.dataset, **obs.toDict()))

        log.info("Loaded {count} observer{s}:".format(
            count   = len(self.observers),
            s       = 's' if len(self.observers) > 1 else ''
        ))

        for o in self.observers:
            log.info(f"    {o}")

    def overrideWarning(self, parameter, old, new):
        log.warning(f"Overriding {c.param(parameter)} ({c.over(old)} -> {c.over(new)})")

    def parallel(self, function, args, *, action = "<default action>", period = 1):
        pool = mp.Pool(processes = self.config.mp.processes)
        manager = mp.Manager()
        queue = manager.Queue()
        total = len(args)

        results = pool.map_async(function, [(queue, *x) for x in args], 20)
        
        while not results.ready():
            log.info("{action}: {count} of {total} ({perc})".format(
                action      = action,
                count       = c.num(f"{queue.qsize():6d}"),
                total       = c.num(f"{total:6d}"),
                perc        = c.num(f"{queue.qsize() / total * 100:5.2f}%"),
            ))
            time.sleep(period)

        return results.get()


class AsmodeusMP(Asmodeus):
    def overrideConfig(self):
        super().overrideConfig()
        
        if self.args.processes:
            self.overrideWarning('process count', self.config.mp.processes, self.args.processes)
            self.config.mp.processes = self.args.processes


# Old crap below

def createAmosHistograms(file):
    h = config.statistics.histograms
    histograms = {
        'altitude':         Histogram.load(file, 'altitude', h.altitude.min, h.altitude.max, h.altitude.bin, 1).normalize(),
        'azimuth':          Histogram.load(file, 'azimuth', h.azimuth.min, h.azimuth.max, h.azimuth.bin, 2).normalize(),
        'angularSpeed':     Histogram.load(file, 'angularSpeed', h.angularSpeed.min, h.angularSpeed.max, h.angularSpeed.bin, 3).normalize(),
        'magnitude':        Histogram.load(file, 'magnitude', h.magnitude.min, h.magnitude.max, h.magnitude.bin, 4).normalize(),
    }

    for name, histogram in histograms.items():
        histogram.tsv(open(datasetPath('histograms', 'amos-{}.tsv'.format(histogram.name)), 'w'))

    return histograms
