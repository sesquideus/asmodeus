import argparse
import os
import sys
import multiprocessing as mp
import logging
import time

from core import configuration, dataset, exceptions
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
            self.config = configuration.load(self.args.config)
            self.overrideConfig()

            self.dataset = dataset.Dataset(os.path.splitext(os.path.basename(self.args.config.name))[0], self.config.observations.observers)
            self.configure()
        except exceptions.CommandLineError as e:
            log.critical("Incorrect command line arguments")
            sys.exit(-1)
        except exceptions.ConfigurationError as e:
            log.critical(f"Configuration error \"{e}\", terminating")
            sys.exit(-1)
        except exceptions.OverwriteError as e:
            log.critical(f"Target directory {e} already exists, terminating (use --overwrite)")
            sys.exit(-1)
        except exceptions.PrerequisiteError:
            log.critical("Missing prerequisites, aborting")
            sys.exit(-1)

    def __del__(self):
        if self.ok:
            log.info("{} finished successfully".format(c.script(f"asmodeus-{self.name}")))
        else:
            log.critical("{} aborted".format(c.script(f"asmodeus-{self.name}")))
        log.info("-" * 50)

    def createArgparser(self):
        self.argparser = argparse.ArgumentParser(description = "All-Sky Meteor Observation and Detection Efficiency Simulator")
        self.argparser.add_argument('config',                   type = argparse.FileType('r'))
        self.argparser.add_argument('-d', '--debug',            action = 'store_true')
        self.argparser.add_argument('-p', '--processes',        type = int)
        self.argparser.add_argument('-D', '--dataset',          type = str)
        self.argparser.add_argument('-O', '--overwrite',        action = 'store_true')
        self.argparser.add_argument('-l', '--logfile',          type = argparse.FileType('w'))

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

        if self.args.processes:
            self.overrideWarning('process count', self.config.mp.processes, self.args.processes)
            self.config.mp.processes = self.args.processes

        if self.args.dataset:
            self.overrideWarning('dataset', self.config.dataset.name, self.args.dataset)
            self.config.dataset.name = self.args.dataset

    def markTime(self):
        self.startTime = time.time()

    def runTime(self):
        return time.time() - self.startTime

    def loadObservers(self):
        self.observers = []
        for oid, obs in self.config.observations.observers.items():
            self.observers.append(Observer(oid, self.dataset, self.config.statistics, **obs.toDict()))

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
