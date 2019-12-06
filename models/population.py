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
        self.generator = Generator.from_config(parameters)
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
            config = configuration.load_YAML(open(filename, 'r'))

            population = Population(config.generator)
            population.count = config.generator.count
            population.iterations = config.generator.iterations
            population.meteors = parallel(
                load,
                dataset.list('meteors'),
                initializer     = init_load_save,
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

    def simulate(self, fps, spf, *, processes=1, period=1):
        log.info(f"Simulating atmospheric entry: using {c.num(processes)} processes at {c.num(fps)} frames per second, "
                 f"""with {c.num(spf)} steps per frame, saving as {c.over(f"{'streaks' if self.streaks else 'points'}")}""")
        self.meteors = parallel(
            simulate,
            self.meteors,
            initializer     = init_simulate,
            initargs        = (fps, spf, self.streaks),
            processes       = min(self.count, processes),
            period          = period,
            action          = "Simulating meteors",
        )
        self.total_frames   = sum(map(lambda x: len(x.frames), self.meteors))
        self.total_mass     = sum(map(lambda x: x.mass_initial, self.meteors))

        log.info("Generated {meteoroids} with {frames} frames, total mass {mass}".format(
            meteoroids      = c.num(len(self.meteors)),
            frames          = c.num(self.total_frames),
            mass            = c.num("{:6f} kg".format(self.total_mass)),
        ))

    def save(self, dataset, *, processes=1, period=1):
        log.info(f"Saving the population to {c.path(dataset.name)}, this might take some time...")

        for meteor in self.meteors:
            meteor.save(dataset.path('meteors'))

        self.save_metadata(dataset)

    def save_metadata(self, dataset):
        yaml.dump({
            'timestamp':        datetime.datetime.now().isoformat(),
            'generator':        self.generator.as_dict(),
            'streaks':          self.streaks,
        }, open(dataset.path('meteors.yaml'), 'w'), default_flow_style = False)


def init_load_save(_queue, _dataset):
    global queue, dataset
    queue, dataset = _queue, _dataset


def load(filename):
    queue.put(1)
    return Meteor.load(dataset.path('meteors', filename))


def save(meteor):
    """ Currently unused (it is faster to have one process do it) """
    queue.put(1)
    return meteor.save(dataset.path('meteors'))


def init_simulate(_queue, _fps, _spf, _streaks):
    global queue, fps, spf, streaks
    queue, fps, spf, streaks = _queue, _fps, _spf, _streaks


def simulate(meteor):
    meteor.fly_adaptive(fps, spf, method='DP', wgs84=True, max_spf=8)
    queue.put(1)

    if not streaks:
        meteor.reduce_to_point()

    return meteor
