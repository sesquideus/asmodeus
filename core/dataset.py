import os
import shutil
import logging

from utilities import colour as c

log = logging.getLogger('root')


class Dataset():
    def __init__(self, name, observers):
        self.name = name
        self.observers = observers

    def path(self, *args):
        return Dataset.staticPath(self.name, *args)

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
