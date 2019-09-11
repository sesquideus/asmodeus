import logging
import random

import time
import multiprocessing as mp

from models.observer    import Observer
from models.observation import Observation
from models.population  import Population
from utilities          import colour as c

log = logging.getLogger('root')


class Campaign():
    def __init__(self, dataset, config):
        log.debug(f"Creating a campaign with dataset {c.name(dataset.name)}")
        log.debug(config)
        self.dataset = dataset
        self.config = config
        self.loadObservers(config.observers)

    def loadObservers(self, parameters):
        self.observers = [Observer(oid, obs) for oid, obs in parameters.items()]

        log.info("Loaded {count} observer{s}:".format(
            count   = len(self.observers),
            s       = 's' if len(self.observers) > 1 else ''
        ))

        for o in self.observers:
            log.info(f"    {o}")

    def loadPopulation(self):
        self.population = Population.load(self.dataset)

    def observe(self, *, processes = 1, report = 1):
        log.info("Computing observations for campaign")
        self.observations = [Observation(self.dataset, observer, self.population, self.config.streaks) for observer in self.observers]

        for observation in self.observations:
            observation.observe(self.config, processes = processes, report = report)

    def setDiscriminators(self, discriminators):
        self.discriminators = discriminators
        self.biasFunction = lambda row: all([disc.compute(row[prop]) for prop, disc in self.discriminators.items()])

