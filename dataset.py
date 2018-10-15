import os, shutil, logging
import colour as c

log = logging.getLogger('root')

class Dataset():
    def __init__(self, name, observers):
        self.name = name
        self.observers = observers._asdict().keys()
        self.prepare()

    def path(self, *args):
        return os.path.join('datasets', self.name, *args)

    def remove(self, *directory):
        directory = self.path(*directory)

        if os.path.exists(directory):
            log.warning("Directory {} exists, removing...".format(c.path(directory)))
            shutil.rmtree(directory)

    def prepare(self):
        self.remove()        
        os.makedirs(self.path('meteors'), exist_ok = True)
        #createSightingsDirectory()
        os.makedirs(self.path('plots'), exist_ok = True)
        os.makedirs(self.path('histograms'), exist_ok = True)

        for observer in self.observers:
            os.makedirs(self.path('histograms', observer), exist_ok = True)

        log.info("Created directory for dataset {}".format(c.path(self.name)))


def createSightingsDirectory():
    sightingsDirectory = datasetPath('sightings')

    os.makedirs(sightingsDirectory, exist_ok = True)
    for observer in config.observers._asdict().keys():
        os.makedirs(os.path.join(sightingsDirectory, observer), exist_ok = True)
