import logging
import random

import time
import multiprocessing as mp

from models.observer    import Observer
from models.population  import Population
from utilities          import colour as c

log = logging.getLogger('root')


class Campaign():
    def __init__(self, dataset, config):
        self.dataset = dataset
        self.loadObservers(config)

    def loadObservers(self, parameters):
        self.observers = [Observer(oid, obs) for oid, obs in parameters.items()]

        log.info("Loaded {count} observer{s}:".format(
            count   = len(self.observers),
            s       = 's' if len(self.observers) > 1 else ''
        ))

        for o in self.observers:
            log.info(f"    {o}")

    def loadPopulation(self):
        self.population = Population.fromDataset(self.dataset)

    def observe(self):
        log.info("Computing observations for campaign")

        for observer in self.observers:
            observer.observe(self.population)

    def setDiscriminators(self, discriminators):
        self.discriminators = discriminators
        self.biasFunction = lambda row: all([disc.compute(row[prop]) for prop, disc in self.discriminators.items()])

