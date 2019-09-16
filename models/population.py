import datetime
import logging
import random
import yaml

from core.parallel      import parallel
from core               import exceptions, configuration
from distribution       import PositionDistribution, VelocityDistribution, MassDistribution, DensityDistribution, TimeDistribution, DragCoefficientDistribution
from models             import Meteor
from physics            import coord
from utilities          import colour as c

log = logging.getLogger('root')


class Generator():
    pass


class GeneratorGrid(Generator):
    def __init__(self, config):
        pass


class GeneratorRealistic(Generator):
    pass


class Population():
    def __init__(self, parameters):
        log.debug(f"Initializing the population")
        self.parameters = parameters

        try:
            log.info("Configuring meteoroid property distributions")
            self.massDistribution               = MassDistribution.fromConfig(self.parameters.mass).logInfo()
            self.positionDistribution           = PositionDistribution.fromConfig(self.parameters.position).logInfo()
            self.velocityDistribution           = VelocityDistribution.fromConfig(self.parameters.velocity).logInfo()
            self.densityDistribution            = DensityDistribution.fromConfig(self.parameters.material.density).logInfo()
            self.temporalDistribution           = TimeDistribution.fromConfig(self.parameters.time).logInfo()
            self.dragCoefficientDistribution    = DragCoefficientDistribution.fromConfig(self.parameters.shape.dragCoefficient).logInfo()
        except AttributeError as e:
            raise exceptions.ConfigurationError(e) from e

    @classmethod
    def load(cls, dataset, *, processes = 1, period = 1):
        log.info(f"Loading saved meteors from dataset {c.name(dataset.name)}")
        filename = dataset.path('meteors.yaml')

        try:
            config = configuration.loadYAML(open(filename, 'r'))

            population = Population(config.distributions)
            population.count = config.count
            population.iterations = config.iterations
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
        log.info(f"Generating {c.num(self.parameters.count)} meteoroids")
        self.count = 0
        self.iterations = 0
        self.meteors = []

        while (self.count < self.parameters.count):
            self.generateMeteoroid()

        log.info("Needed {iterations} candidate{s}, effective area {area}".format(
            iterations      = c.num(self.iterations),
            area            = c.num(f"{self.parameters.count / self.iterations * 100:5.2f}%"),
            s               = 's' if self.iterations > 1 else '',
        ))

        return

        self.meteors = self.generator.generate()
 
    def generateMeteoroid(self):
        mass                = self.massDistribution.sample()
        density             = self.densityDistribution.sample()
        timestamp           = self.temporalDistribution.sample()
        position            = self.positionDistribution.sample()
        dragCoefficient     = self.dragCoefficientDistribution.sample()
        velocityEquatorial  = self.velocityDistribution.sample()

        velocityECEF        = coord.Vector3D.fromNumpyVector(
                                (coord.rotMatrixZ(coord.earthRotationAngle(timestamp)) @ velocityEquatorial.toNumpyVector())
                            )
        entryAngleSin       = -position * velocityECEF / (position.norm() * velocityECEF.norm())

        self.iterations += 1
        if entryAngleSin > random.random():
            self.meteors.append(Meteor(
                mass            = mass,
                density         = density,
                timestamp       = timestamp,
                velocity        = velocityECEF,
                position        = position,
                ablationHeat    = self.parameters.material.ablationHeat,
                heatTransfer    = self.parameters.material.heatTransfer,
                dragCoefficient = dragCoefficient,
            ))
            self.count += 1

    def simulate(self, fps, spf, *, processes = 1, period = 1):
        log.info(f"Simulating atmospheric entry: using {c.num(processes)} processes at {c.num(fps)} frames per second, \
            with {c.num(spf)} steps per frame")
        self.meteors = parallel(
            simulate,
            self.meteors,
            initializer     = initSimulate,
            initargs        = (fps, spf),
            processes       = min(self.count, processes),
            period          = period,
            action          = "Simulating meteors",
        )
        log.info("Total mass {mass}".format(
            mass            = c.num("{:6f} kg".format(sum(map(lambda x: x.initMass, self.meteors)))),
        ))

    def save(self, dataset, *, processes = 1, period = 1):
        log.info(f"Saving the population to {c.path(dataset.name)}, this might take some time...")

        for meteor in self.meteors:
            meteor.save(dataset.path('meteors'))

        self.saveMetadata(dataset)

    def saveMetadata(self, dataset):
        yaml.dump({
            'count':            self.count,
            'iterations':       self.iterations,
            'timestamp':        datetime.datetime.now().isoformat(),
            'distributions':    {
                'mass':             self.massDistribution.asDict(),
                'time':             self.temporalDistribution.asDict(),
                'position':         self.positionDistribution.asDict(),
                'velocity':         self.velocityDistribution.asDict(),
                'material':         {
                    'density':          self.densityDistribution.asDict(),
                },
                'shape':        {
                    'dragCoefficient':  self.dragCoefficientDistribution.asDict(),
                },
            },
        }, open(dataset.path('meteors.yaml'), 'w'), default_flow_style = False)


def initLoadSave(_queue, _dataset):
    global queue, dataset
    queue, dataset = _queue, _dataset


def load(filename):
    queue.put(1)
    return Meteor.load(dataset.path('meteors', filename))


""" Currently unused (it is faster to have one process do it) """
def save(meteor):
    queue.put(1)
    return meteor.save(dataset.path('meteors'))


def initSimulate(_queue, _fps, _spf):
    global queue, fps, spf
    queue, fps, spf = _queue, _fps, _spf


def simulate(meteor):
    meteor.flyRK4(fps, spf)
    queue.put(1)
    return meteor
