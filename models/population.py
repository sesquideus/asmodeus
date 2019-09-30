import datetime
import logging
import yaml

from core.parallel      import parallel
from core               import exceptions, configuration
from models             import Meteor, Generator
from utilities          import colour as c

log = logging.getLogger('root')


class Population():
    def __init__(self, parameters, streaks = True):
        log.debug(f"Initializing the population")
        self.generator = Generator.fromConfig(parameters)
        self.parameters = parameters
        self.streaks = streaks

        try:
            log.info("Configuring meteoroid property distributions")
        except AttributeError as e:
            raise exceptions.ConfigurationError(e) from e

    @classmethod
    def load(cls, dataset, *, processes = 1, period = 1):
        log.info(f"Loading saved meteors from dataset {c.name(dataset.name)}")
        filename = dataset.path('meteors.yaml')

        try:
            config = configuration.loadYAML(open(filename, 'r'))

            population = Population(config.generator)
            population.count = config.generator.count
            population.iterations = config.generator.iterations
            population.meteors = parallel(
                load,
                dataset.list('meteors'),
                initializer     = initLoadSave,
                initargs        = (dataset,),
                processes       = processes,
                period          = period,
                action          = "Loading meteor pickles",
            )

            log.info(f"Loaded the population")
            return population
        except FileNotFoundError as e:
            log.critical(f"Could not load sighting metadata for dataset {c.name(dataset.name)} (file {c.path(filename)} is missing)")
            raise exceptions.PrerequisiteError from e
        except yaml.composer.ComposerError as e:
            log.critical(f"Could not parse sighting metadata file for dataset {c.name(dataset.name)} (file {c.path(filename)} is not valid YAML)")
            raise exceptions.PrerequisiteError from e

    def generate(self):
        self.meteors = self.generator.generate()
        self.count = self.generator.count
        self.iterations = self.generator.iterations

    def simulate(self, fps, spf, *, processes = 1, period = 1):
        log.info(f"Simulating atmospheric entry: using {c.num(processes)} processes at {c.num(fps)} frames per second, "
                 f"""with {c.num(spf)} steps per frame, saving as {c.over(f"{'streaks' if self.streaks else 'points'}")}""")
        self.meteors = parallel(
            simulate,
            self.meteors,
            initializer     = initSimulate,
            initargs        = (fps, spf, self.streaks),
            processes       = min(self.count, processes),
            period          = period,
            action          = "Simulating meteors",
        )
        log.info("Generated {frames} frames, total mass {mass}".format(
            frames          = c.num(sum(map(lambda x: len(x.frames), self.meteors))),
            mass            = c.num("{:6f} kg".format(sum(map(lambda x: x.massInitial, self.meteors)))),
        ))

    def save(self, dataset, *, processes = 1, period = 1):
        log.info(f"Saving the population to {c.path(dataset.name)}, this might take some time...")

        for meteor in self.meteors:
            meteor.save(dataset.path('meteors'))

        self.saveMetadata(dataset)

    def saveMetadata(self, dataset):
        yaml.dump({
            'timestamp':        datetime.datetime.now().isoformat(),
            'generator':        self.generator.asDict(),
            'streaks':          self.streaks,
        }, open(dataset.path('meteors.yaml'), 'w'), default_flow_style = False)


def initLoadSave(_queue, _dataset):
    global queue, dataset
    queue, dataset = _queue, _dataset


def load(filename):
    queue.put(1)
    return Meteor.load(dataset.path('meteors', filename))


def save(meteor):
    """ Currently unused (it is faster to have one process do it) """
    queue.put(1)
    return meteor.save(dataset.path('meteors'))


def initSimulate(_queue, _fps, _spf, _streaks):
    global queue, fps, spf, streaks
    queue, fps, spf, streaks = _queue, _fps, _spf, _streaks


def simulate(meteor):
    meteor.flyRK4(fps, spf)
    queue.put(1)

    if not streaks:
        meteor.reduceToPoint()

    return meteor
