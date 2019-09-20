import os
import shutil
import logging

from core import exceptions, configuration
from models import Population

from utilities import colour as c

log = logging.getLogger('root')


class DataManager():
    def __init__(self, name, *, root = 'datasets', overwrite = False):
        self.name = name
        self.root = os.path.realpath(os.path.join(root, name))
        self.overwrite = overwrite

    def createRoot(self):
        os.makedirs(self.root)
        
    def path(self, *path):
        return os.path.join(self.root, *path)

    def exists(self, *path):
        return os.path.exists(self.path(*path))

    def list(self, *path):
        return os.listdir(self.path(*path))

    def remove(self, *path):
        directory = self.path(*path)
        if os.path.exists(directory):
            log.warning(f"Directory {c.path(directory)} exists, removing...")
            shutil.rmtree(directory)
        else:
            log.debug(f"Directory {c.path(directory)} did not exist")

    def create(self, *path, exist_ok = False):
        log.debug(f"Creating new dataset subdirectory {c.path(self.path(*path))}")

        path = self.path(*path)
        os.makedirs(path, exist_ok = exist_ok)
        return path

    def reset(self, *path):
        self.remove(*path)
        self.create(*path)

    def protectedReset(self, *path):
        if self.overwrite or not self.exists(*path):
            self.reset(*path)
        else:
            raise exceptions.OverwriteError(f"Refusing to overwrite {c.path(self.path(*path))}")

    def loadPopulation(self):
        try:
            filename = self.path('meteors.yaml')
            config = configuration.loadYAML(open(filename, 'r'))
            population = Population(config.distributions)
            population.load(self)
        except FileNotFoundError as e:
            log.error(f"Cannot find file {c.path(filename)}")
            raise exceptions.PrerequisiteError() from e

        log.info(f"Population loaded successfully")
        return population

    def resetMeteors(self):
        self.protectedReset()
        self.protectedReset('meteors')

    def validateSightings(self):
        """ We will validate the sightings directory here """
        if not os.path.isdir(self.path('sightings')) or not self.exists('sightings.yaml'):
            raise exceptions.PrerequisiteError(f"Sighting files are corrupt in dataset {c.name(self.name)}")

        return True

    def resetSightings(self):
        self.protectedReset('sightings')

    def resetScatters(self):
        self.protectedReset('scatters')

    def meteorFiles(self):
        return self.list('meteors')
        
