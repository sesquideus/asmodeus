import os
import shutil
import logging

from utilities import colour as c

log = logging.getLogger('root')


class Dataset():
    def __init__(self, name):
        self.name = name

    def path(self, *args):
        return Dataset.staticPath(self.name, *args)

    def root(self):
        return self.path()

    def exists(self, *path):
        return os.path.exists(self.path(*path))

    def isDir(self, *path):
        return os.path.isdir(self.path(*path))

    def listDir(self, *path):
        return os.listdir(self.path(*path))
    
    def remove(self, *path):
        directory = self.path(*path)

        if os.path.exists(directory):
            log.warning("Directory {} exists, removing...".format(c.path(directory)))
            shutil.rmtree(directory)
        else:
            log.debug("Directory {} did not exist".format(c.path(directory)))

    def delete(self):
        log.warning("Deleting dataset {}".format(c.name(self.name)))
        self.remove()

    def reset(self, *path):
        self.remove(*path)
        self.create(*path)

    def create(self, *path, exist_ok = False):
        log.debug("Creating new dataset subdirectory {}".format(c.path(self.path(*path))))
        os.makedirs(self.path(*path), exist_ok = exist_ok)

    def require(self, *path):
        if not os.path.isdir(self.path(*path)):
            raise FileNotFoundError()

    @staticmethod
    def staticPath(name, *args):
        return os.path.join('datasets', name, *args)

    def list(self, *path):
        return os.listdir(self.path(*path))


class DataManager():
    def __init__(self, name, root = 'dataset'):
        self.name = name
        self.root = os.path.realpath(root)

    def createRoot(self):
        os.makedirs(self.root)
        
    def path(self, *path):
        return os.path.join(self.root, *path)

    def exists(self, *path):
        return os.path.exists(self.path(*path))

    def list(self, *path):
        return os.listdir(self.path(*path))

    def checkMeteors(self):
        return os.path.isdir(self.path('meteors')) and self.exists('meteors.yaml')

    def meteorFiles(self):
        return self.list('meteors')
        
