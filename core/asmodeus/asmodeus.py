import argparse
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
        self.startTime = time.time()
        log.info("Initializing {}".format(c.script("asmodeus-{}".format(self.name))))
        self.createArgparser()
        self.args = self.argparser.parse_args()

        try:
            self.buildConfig()
            self.dataset = dataset.Dataset(self.args.dataset)
            self.overrideConfig()
            self.prepareDataset()
            self.configure()
        except exceptions.CommandLineError as e:
            log.critical(f"Incorrect command line arguments: {e}")
            sys.exit(-1)
        except exceptions.ConfigurationError as e:
            log.critical(f"Terminating due to a configuration error: {e}")
            sys.exit(-1)
        except exceptions.OverwriteError as e:
            log.critical(f"Target directory {e} already exists (use {c.param('-O')} or {c.param('--overwrite')} to overwrite the existing dataset)")
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
            log.error("Could not load configuration file {}: {}".format(file, e))
            raise exceptions.CommandLineError()
        except yaml.composer.ComposerError as e:
            log.error("YAML composer error")
            raise exceptions.ConfigurationError(e) from e

        return dotmap.DotMap(config, _dynamic = False)

    def prepareDataset(self):
        raise NotImplementedError(f"You need to define the {c.name('prepareDataset')} method for every ASMODEUS subclass.")

    def buildConfig(self):
        raise NotImplementedError(f"You need to define the {c.name('buildConfig')} method for every ASMODEUS subclass.")

    def protectOverwrite(self, *path):
        if self.dataset.exists(*path) and not self.config.overwrite:
            raise exceptions.OverwriteError(c.path(self.dataset.path(*path)))
        else:
            self.dataset.reset(*path)

    def requireStage(self, stage, program):
        try:
            self.dataset.require(stage)
        except FileNotFoundError:
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
        self.mark = time.time()

    def stopTime(self):
        return time.time() - self.mark

    def runTime(self):
        return time.time() - self.startTime

    def run(self):
        try:
            self.runSpecific()
            self.finalize()
        except exceptions.ConfigurationError as e:
            log.critical(f"Terminating due to a configuration error: {e}")
        finally:
            if self.ok:
                log.info(f"{c.script(f'asmodeus-{self.name}')} finished successfully in {self.runTime():.6f} s")
            else:
                log.critical(f"{c.script(f'asmodeus-{self.name}')} aborted")
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

 
    def finalize(self):
        log.debug("Wrapping everything up...")
        self.ok = True
