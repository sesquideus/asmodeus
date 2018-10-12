import multiprocessing as mp
import os, sys, logging, shutil, argparse, time
from utils import colour, jinjaEnv, filterVisible

from configuration import configuration, density, mass
from models.observer import Observer
from models.sighting import Sighting
from models.sightingframe import SightingFrame
from histogram import Histogram

log = logging.getLogger('root')

def runTime():
    return time.time() - startTime



### Multiprocessing wrappers

def multiProcess(function, args, count):
    pool = mp.Pool(processes = config.mp.processes)
    results = [pool.apply_async(function, args) for _ in range(0, count)]
    return [result.get(timeout = 10) for result in results]

def blockProcess(function, args, count):
    pool = mp.Pool(processes = config.mp.processes)
    resultLists = [pool.apply_async(function, (blocksize,)) for _ in range(0, count // config.mp.blocksize)]
    resultRemainder = function(count % blocksize)

    results = [result for resultList in resultLists for result in resultList]
    output = results + resultRemainder


def buildGnuplotTemplate(template, dataset, context, outputDirectory = None):
    print(
        jinjaEnv('templates').get_template(template).render(context),
        file = sys.stdout if outputDirectory is None else open(os.path.join(outputDirectory, template), 'w')
    )

def buildConfigTemplate(template, context, outputDirectory = None):
    print(
        jinjaEnv('templates').get_template(template).render(context),
        file = sys.stdout if outputDirectory is None else open(os.path.join(outputDirectory, template), 'w')
    )



### Preparation of dataset directories

def remove(*directory):
    directory = datasetPath(*directory)

    if os.path.exists(directory):
        log.warning("Directory {} exists, removing...".format(colour(directory, 'dir')))
        shutil.rmtree(directory)

def createSightingsDirectory():
    sightingsDirectory = datasetPath('sightings')

    os.makedirs(sightingsDirectory, exist_ok = True)
    for observer in config.observers._asdict().keys():
        os.makedirs(os.path.join(sightingsDirectory, observer), exist_ok = True)
    
def prepareDataset():
    remove()        
    os.makedirs(datasetPath('meteors'), exist_ok = True)
    createSightingsDirectory()
    os.makedirs(datasetPath('plots'), exist_ok = True)
    os.makedirs(datasetPath('histograms'), exist_ok = True)

    for observer in config.observers._asdict().keys():
        os.makedirs(datasetPath('histograms', observer), exist_ok = True)

    log.info("Created directory for dataset {}".format(colour(config.dataset.name, 'dir')))

def datasetPath(*args):
    return os.path.join('datasets', config.dataset.name, *args)

### Preparation of observers

def loadObservers():
    observers = []
    for oid, obs in config.observers._asdict().items():
        observers.append(Observer(oid, config.statistics.histograms._asdict(), **dict(obs._asdict().items())))

    log.info("Loaded {} observers:".format(len(observers)))
    for o in observers:
        log.info(o)

    return observers

def createAmosHistograms(file):
    h = config.statistics.histograms
    histograms = {
        'altitude':         Histogram.load(file, 'altitude', h.altitude.min, h.altitude.max, h.altitude.bin, 1).normalize(),
        'azimuth':          Histogram.load(file, 'azimuth', h.azimuth.min, h.azimuth.max, h.azimuth.bin, 2).normalize(),
        'angularSpeed':     Histogram.load(file, 'angularSpeed', h.angularSpeed.min, h.angularSpeed.max, h.angularSpeed.bin, 3).normalize(),
        'magnitude':        Histogram.load(file, 'magnitude', h.magnitude.min, h.magnitude.max, h.magnitude.bin, 4).normalize(),
    }

    for name, histogram in histograms.items():
        histogram.tsv(open(datasetPath('histograms', 'amos-{}.tsv'.format(histogram.name)), 'w'))

    return histograms

### Parsers

class AsmodeusParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(description = "All-Sky Meteor Orbit and Detection Efficiency Simulator")
        self.add_argument('config',               type = argparse.FileType('r'))
        self.add_argument('-d', '--debug',        action = 'store_true')
        self.add_argument('-p', '--processes',    type = int)
        self.add_argument('-s', '--dataset',      type = str)
        self.add_argument('-l', '--logfile',      type = argparse.FileType('w'))

class AsmodeusParserGenerate(AsmodeusParser):
    def __init__(self):
        super().__init__()    
        self.add_argument('-c', '--count', type = int)

class AsmodeusParserObserve(AsmodeusParser):
    def __init__(self):
        super().__init__()
        self.add_argument('--plot-sky', action = 'store_true')

### Master initializer

def initialize(script):
    global config
    global startTime
    startTime = time.time()
    args = AsmodeusParserGenerate().parse_args()
    config = configuration.applyOverrides(script, args)

    log.info("Initializing {}".format(colour("asmodeus-{}".format(script), 'script')))
    return config
