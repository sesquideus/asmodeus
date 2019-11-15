import logging
import yaml
import datetime

from core               import configuration, exceptions

from models.observer    import Observer
from models.observation import Observation
from models.population  import Population
from models.dataframe   import Dataframe
from utilities          import colour as c

log = logging.getLogger('root')


class Campaign():
    def __init__(self, dataset, config):
        log.debug(f"Creating a campaign with dataset {c.name(dataset.name)}, full config is")
        if log.getEffectiveLevel() == logging.DEBUG:
            config.pprint()

        self.dataset = dataset
        self.config = config
        self.load_observers(config.observers)
        log.debug(f"Campaign initialized")

    @classmethod
    def load(cls, dataset, *, analyses = None):
        log.info(f"Loading a campaign from dataset {c.name(dataset.name)}")
        filename = dataset.path('campaign.yaml')

        try:
            config = configuration.load_YAML(open(filename, 'r'))
            campaign = Campaign(dataset, config)
            campaign.analyses = analyses
            campaign.load_dataframes()
            return campaign
        except FileNotFoundError as e:
            log.critical(f"Could not load campaign metadata for dataset {c.name(dataset.name)} (file {c.path(filename)} is missing)")
            raise exceptions.PrerequisiteError from e
        except yaml.composer.ComposerError as e:
            log.critical(f"Could not parse campaign metadata file for dataset {c.name(dataset.name)} (file {c.path(filename)} is not valid YAML)")
            raise exceptions.PrerequisiteError from e

    def load_observers(self, parameters):
        log.debug("Loading observers")
        self.observers = [Observer(oid, obs) for oid, obs in parameters.items()]

        log.info("Loaded {count} observer{s}:".format(
            count   = c.num(len(self.observers)),
            s       = 's' if len(self.observers) > 1 else ''
        ))

        for o in self.observers:
            log.info(f"    {o}")

    def load_population(self, *, processes=1, period=1):
        self.population = Population.load(self.dataset, processes = processes, period = period)

    def load_dataframes(self):
        self.dataframes = [Dataframe.load(self.dataset, observer) for observer in self.observers]

        for dataframe in self.dataframes:
            dataframe.quantities = self.analyses.quantities

    def observe(self, *, processes = 1, period = 1):
        log.info("Computing observations for campaign")
        self.observations = [Observation(self.dataset, observer, self.population, self.config) for observer in self.observers]

        for observation in self.observations:
            observation.observe(processes=processes, period=period)

    def save(self):
        for observation in self.observations:
            observation.save()

        self.save_metadata()

    def save_metadata(self):
        yaml.dump({
            'count':            self.population.count,
            'timestamp':        datetime.datetime.now().isoformat(),
            'observers':        {observer.id: observer.as_dict() for observer in self.observers},
            'observations':     {observation.observer.id: observation.as_dict() for observation in self.observations},
        }, open(self.dataset.path('campaign.yaml'), 'w'), default_flow_style = False)

    def set_discriminators(self, discriminators):
        self.discriminators = discriminators
        self.bias_function = lambda row: all([disc.compute(row[prop]) for prop, disc in self.discriminators.items()])

    def filter_visible(self, bias = True):
        if bias:
            log.warning(f"Applying bias effects")
            for dataframe in self.dataframes:
                dataframe.apply_bias(self.bias_function)
        else:
            log.warning(f"No bias effects active, all meteors will be visible")
            for dataframe in self.dataframes:
                dataframe.skip_bias()

    def make_scatters(self):
        for dataframe in self.dataframes:
            dataframe.make_scatters(self.analyses.scatters)

    def make_sky_plots(self, *, dark = True):
        for dataframe in self.dataframes:
            dataframe.make_sky_plot(dark = dark)
