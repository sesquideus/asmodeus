import os, shutil

class Dataset():
    def __init__(self, name):
        self.name = name

    def path(self, *args):
        return os.path.join('datasets', self.name, *args)

    def remove(self, *args):
        directory = self.path(*directory)

        if os.path.exists(directory):
            log.warning("Directory {} exists, removing...".format(colour(directory, 'dir')))
            shutil.rmtree(directory)

    def prepare(self):
        self.remove()        
        os.makedirs(datasetPath('meteors'), exist_ok = True)
        createSightingsDirectory()
        os.makedirs(datasetPath('plots'), exist_ok = True)
        os.makedirs(datasetPath('histograms'), exist_ok = True)

        for observer in config.observers._asdict().keys():
            os.makedirs(datasetPath('histograms', observer), exist_ok = True)

        log.info("Created directory for dataset {}".format(colour(config.dataset.name, 'dir')))


def createSightingsDirectory():
    sightingsDirectory = datasetPath('sightings')

    os.makedirs(sightingsDirectory, exist_ok = True)
    for observer in config.observers._asdict().keys():
        os.makedirs(os.path.join(sightingsDirectory, observer), exist_ok = True)
