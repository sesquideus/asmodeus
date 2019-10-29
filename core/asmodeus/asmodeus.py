import argparse
import sys
import multiprocessing as mp
import logging
import time

from core import dataset, exceptions, configuration
from utilities import colour as c

from models.observer import Observer

log = logging.getLogger('root')


class Asmodeus():
    def __init__(self):
        self.ok = False
        self.start_time = time.time()
        log.info(f"Initializing {c.script(f'asmodeus-{self.name}')}")
        self.create_argparser()
        self.args = self.argparser.parse_args()

        try:
            try:
                self.load_config()
                self.override_config()
                configuration.make_static(self.config)

                log.debug(f"Full configuration is")
                if log.getEffectiveLevel() == logging.DEBUG:
                    self.config.pprint()

                self.dataset = dataset.DataManager(self.args.dataset, overwrite=self.config.overwrite)
                self.prepare_dataset()
                self.configure()
            except exceptions.CommandLineError as e:
                log.critical(f"Incorrect command line arguments: {e}")
                raise exceptions.FatalError
            except exceptions.ConfigurationError as e:
                log.critical(f"Terminating due to a configuration error: {c.err(e)}")
                raise exceptions.FatalError
            except exceptions.OverwriteError as e:
                log.critical(e)
                log.critical(f"Target directory already exists (use {c.param('-O')} or {c.param('--overwrite')} to overwrite the existing dataset)")
                raise exceptions.FatalError
            except exceptions.PrerequisiteError as e:
                log.critical(f"Missing prerequisites: {e}")
                log.critical("Aborting")
                raise exceptions.FatalError
        except exceptions.FatalError:
            log.critical(f"{c.script(f'asmodeus-{self.name}')} aborting during configuration")
            sys.exit(-1)

        log.info("Initialization complete")

    def create_argparser(self):
        self.argparser = argparse.ArgumentParser(description="All-Sky Meteor Observation and Detection Efficiency Simulator")
        self.argparser.add_argument('dataset',                  type = str,                         help = "name of the dataset")
        self.argparser.add_argument('config',                   type = argparse.FileType('r'),      help = "main configuration file")
        self.argparser.add_argument('-O', '--overwrite',        action = 'store_true',              help = "overwrite the dataset if it exists")
        self.argparser.add_argument('-d', '--debug',            action = 'store_true',              help = "much more verbose logging")
        self.argparser.add_argument('-l', '--logfile',          type = argparse.FileType('w'),      help = "output log to file")

    def prepare_dataset(self):
        raise NotImplementedError(f"You need to define the {c.name('prepareDataset')} method for every ASMODEUS subclass.")

    def load_config(self):
        self.config = configuration.load_YAML(self.args.config)

    def override_config(self):
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

    def mark_time(self):
        self.mark = time.time()

    def stop_time(self):
        return time.time() - self.mark

    def run_time(self):
        return time.time() - self.start_time

    def run(self):
        try:
            self.run_specific()
            self.finalize()
        except exceptions.PrerequisiteError as e:
            log.critical(f"Terminating due to missing prerequisites")
        except exceptions.ConfigurationError as e:
            log.critical(f"Terminating due to a configuration error: {e}")
        finally:
            if self.ok:
                log.info(f"{c.script(f'asmodeus-{self.name}')} finished successfully in {self.run_time():.6f} s")
                log.info("-" * 50)
            else:
                log.critical(f"{c.script(f'asmodeus-{self.name}')} aborted during runtime")

    def override_warning(self, parameter, old, new):
        log.warning(f"Overriding {c.param(parameter)} ({c.over(old)} -> {c.over(new)})")

    def finalize(self):
        log.debug("Wrapping everything up...")
        self.ok = True
