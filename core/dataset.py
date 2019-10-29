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

    def create_root(self):
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

    def protected_reset(self, *path):
        if self.overwrite or not self.exists(*path):
            self.reset(*path)
        else:
            raise exceptions.OverwriteError(f"Refusing to overwrite {c.path(self.path(*path))}")

    def reset_meteors(self):
        self.protected_reset()
        self.protected_reset('meteors')
        self.remove('meteors.yaml')
        
        self.remove('sightings')
        self.remove('campaign.yaml')

        self.remove('analyses')

    def validate_sightings(self):
        """ We will validate the sightings directory here """
        if not os.path.isdir(self.path('sightings')) or not self.exists('sightings.yaml'):
            raise exceptions.PrerequisiteError(f"Sighting files are corrupt in dataset {c.name(self.name)}")

        return True

    def reset_sightings(self):
        self.protected_reset('sightings')
        self.remove('campaign.yaml')

        self.remove('analyses')

    def reset_scatters(self):
        self.protected_reset('analyses', 'scatters')
    
    def reset_sky_plots(self):
        self.protected_reset('analyses', 'skyplots')

    def meteor_files(self):
        return self.list('meteors')
        
