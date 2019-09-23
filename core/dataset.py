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

    def resetMeteors(self):
        self.protectedReset()
        self.protectedReset('meteors')
        self.remove('meteors.yaml')
        
        self.remove('sightings')
        self.remove('campaign.yaml')

        self.remove('analyses')

    def validateSightings(self):
        """ We will validate the sightings directory here """
        if not os.path.isdir(self.path('sightings')) or not self.exists('sightings.yaml'):
            raise exceptions.PrerequisiteError(f"Sighting files are corrupt in dataset {c.name(self.name)}")

        return True

    def resetSightings(self):
        self.protectedReset('sightings')
        self.remove('campaign.yaml')

        self.remove('analyses')

    def resetScatters(self):
        self.protectedReset('analyses', 'scatters')
    
    def resetSkyPlots(self):
        self.protectedReset('analyses', 'skyplots')

    def meteorFiles(self):
        return self.list('meteors')
        
