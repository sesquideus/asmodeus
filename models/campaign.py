import logging
import random
import yaml
import datetime

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
        log.debug(f"Campaign initialized")

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
        self.observations = [Observation(self.dataset, observer, self.population, self.config) for observer in self.observers]

        for observation in self.observations:
            observation.observe(processes = processes, report = report)

    def save(self):
        for observation in self.observations:
            observation.save()

        self.saveMetadata()

    def saveMetadata(self):
        yaml.dump({
            'count':            self.population.count,
            'timestamp':        datetime.datetime.now().isoformat(),
            'observers':        {observer.id: observer.asDict() for observer in self.observers},
        }, open(self.dataset.path('campaign.yaml'), 'w'), default_flow_style = False)


    def setDiscriminators(self, discriminators):
        self.discriminators = discriminators
        self.biasFunction = lambda row: all([disc.compute(row[prop]) for prop, disc in self.discriminators.items()])

