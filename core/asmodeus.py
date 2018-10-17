import multiprocessing as mp
import argparse, os, sys, logging, shutil, time, namedtupled

from core import configuration, dataset
from utilities import colour as c, utilities as util

from models.observer import Observer

log = logging.getLogger('root')

class Asmodeus():
    def __init__(self):
        self.createArgparser()
        self.args = self.argparser.parse_args()

        self.loadConfig()
        self.overrideConfig()
        self.config = namedtupled.map(self.config.toDict())

        self.dataset = dataset.Dataset(self.config.dataset.name, self.config.observers)

    def createArgparser(self):
        self.argparser = argparse.ArgumentParser(description = "All-Sky Meteor Observation and Detection Efficiency Simulator")
        self.argparser.add_argument('config',               type = argparse.FileType('r'))
        self.argparser.add_argument('-d', '--debug',        action = 'store_true')
        self.argparser.add_argument('-p', '--processes',    type = int)
        self.argparser.add_argument('-s', '--dataset',      type = str)
        self.argparser.add_argument('-l', '--logfile',      type = argparse.FileType('w'))

    def loadConfig(self):
        self.config = configuration.load(self.args.config)

    def overrideConfig(self):
        log.setLevel(logging.DEBUG if self.args.debug else logging.INFO)

        if self.args.debug:
            log.warning("Debug output is {}".format(c.over('active')))

        if self.args.logfile:
            log.addHandler(logging.FileHandler(self.args.logfile.name))
            log.warning("Added log output {}".format(c.over(self.args.logfile.name)))

        if self.args.processes:
            self.overrideWarning('process count', self.config.mp.processes, self.args.processes)
            self.config.mp.processes = self.args.processes

        if self.args.dataset:
            self.overrideWarning('dataset', self.config.dataset.name, self.args.dataset)
            self.config.dataset.name = self.args.dataset
        
        self.config.dataset.path = os.path.join('datasets', self.config.dataset.name)
       
    def markTime(self):
        self.startTime = time.time()

    def runTime(self):
        return time.time() - self.startTime

    def loadObservers(self):
        self.observers = []
        for oid, obs in self.config.observers._asdict().items():
            self.observers.append(Observer(oid, **dict(obs._asdict().items())))

        log.info("Loaded {} observers:".format(len(self.observers)))
        for o in self.observers:
            log.info(o)

    def overrideWarning(self, parameter, old, new):
        log.warning("Overriding {parameter} ({old} -> {new})".format(
            parameter   = parameter,
            old         = c.over(old),
            new         = c.over(new),
        ))

    def distributionInfo(self, quantity, name, params = None):
        log.info("{quantity:<27} distribution is {name:>20}{params}".format(
            quantity    = c.param(quantity),
            name        = c.name(name),
            params      = "" if params is None else " ({})".format(util.formatParameters(params)),
        ))
        

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


### Preparation of observers


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

### Master initializer


