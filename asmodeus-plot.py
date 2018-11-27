#!/usr/bin/env python
"""
    Computes apparent positions and magnitudes for all observers as defined in the configuration file,
    using generated meteors saved in dataset `meteors` directory
    Requires: meteors
    Outputs: sightings
"""

from core import asmodeus, dataset, logger
from physics import coord
from utilities import colour as c, utilities as ut


class AsmodeusPlot(asmodeus.Asmodeus):
    def __init__(self):
        self.name = 'plot'
        super().__init__() 

    def configure(self):
        self.loadObservers()
        self.dataset.require('sightings')
        #self.dataset.require('histograms')

        #self.dataset.reset('plots')
        for observer in self.observers:
            self.dataset.create('plots', observer.id, exist_ok = True)
        
    def plotSky(self):
        for observer in self.observers:
            observer.plotSkyPlot(self.config.plot.sky)

    def plotHistograms(self):
        for observer in self.observers:
            pass
            #observer.plotHistograms()


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusPlot()
    asmo.plotSky()
    asmo.plotHistograms()

    log.info("Finished successfully")
    log.info("---------------------")





def main(argv):
    plotSky(observers)
    plotHistograms(observers)

    if config.multifit.magnitude.repeat == 0:
        log.info("Skipping plot {}".format(colour('magnitude', 'name')))
    else:
        plotChiSquareMagnitude(observers, 'magnitude')
        centroid('magnitude', 100)
    
    if config.multifit.altitude.repeat == 0:
        log.info("Skipping plot {}".format(colour('altitude', 'name')))
    else:
        plotChiSquareAltitude(observers, 'altitude')

def plotSky(observers):
    context = {
        'dataset': config.dataset.name,
        'streaks': config.plot.streaks,
        'dark': config.plot.dark,
        'observers': observers,
        'pixels': config.plot.pixels,
    }

    quantities = {}
    if config.plot.sky.distance:
        quantities[6] = 'distance'

    if config.plot.sky.elevation:
        quantities[7] = 'elevation'

    if config.plot.sky.speed:
        quantities[8] = 'speed'

    if config.plot.sky.angularSpeed:
        quantities[9] = 'angularSpeed'

    if config.plot.sky.mass:
        quantities[10] = 'mass'
    
    if config.plot.sky.power:
        quantities[11] = 'power'

    if config.plot.sky.sighted:
        quantities[14] = 'sighted'

    context['quantities'] = quantities

    for observer in observers:
        fileName = os.path.join('datasets', config.dataset.name, 'plots', '{}.tsv'.format(observer))
        if not os.path.exists(fileName):
            raise FileNotFoundError("File {} not found!".format(colour(fileName, 'name')))

    asmodeus.buildGnuplotTemplate('sky.gp', config.dataset.name, context, os.path.join('datasets', config.dataset.name))
    log.info("Template {} finished, calling {}".format(colour('sky', 'name'), colour('gnuplot', 'script')))
    os.system('gnuplot datasets/{}/sky.gp'.format(config.dataset.name))


def plotHistograms(observers):
    context = {
        'dataset': config.dataset.name,
        'observers': observers,
        'histograms': config.statistics.histograms,
    }
    asmodeus.buildGnuplotTemplate('histogram.gp', config.dataset.name, context, asmodeus.datasetPath('plots'))
    log.info("Template {} finished, calling {}".format(colour('histogram', 'name'), colour('gnuplot', 'script')))
    os.system('gnuplot {}'.format(asmodeus.datasetPath('plots', 'histogram.gp')))

def plotChiSquareMagnitude(observers, quantity):
    context = {
        'dataset':      config.dataset.name,
        'observers':    observers,
        'omega':        config.multifit.magnitude.parameters.omega,
        'limmag':       config.multifit.magnitude.parameters.limit,
    }
    asmodeus.buildGnuplotTemplate('chiSquare-{}.gp'.format(quantity), config.dataset.name, context, asmodeus.datasetPath('plots'))
    log.info("Template {} finished, calling {}".format(colour('chiSquare', 'name'), colour('gnuplot', 'script')))
    os.system('gnuplot {}'.format(asmodeus.datasetPath('plots', 'chiSquare-{}.gp'.format(quantity))))

def centroid(quantity, count):
    file = open(asmodeus.datasetPath('plots', 'chiSquare-{}.tsv'.format(quantity)), 'r')
    data = []
    for line in file:
        (om, lm, cs) = map(float, line.rstrip('\n').split())
        data.append((om, lm, cs))

    data = sorted(data, key = lambda x: x[2])[0:count]
    limmag = sum([x[0] for x in data]) / count
    omega = sum([x[1] for x in data]) / count
    chisq = sum([x[2] for x in data]) / count

    log.info("Minimum for limiting magnitude {}, width {}, chi square is {}".format(
        colour("{:.3f}".format(limmag), 'num'),
        colour("{:.3f}".format(omega), 'num'),
        colour("{:.6f}".format(chisq), 'num'),
    ))
        
def plotChiSquareAltitude(observers, quantity):
    context = {
        'dataset':      config.dataset.name,
        'observers':    observers,
        'exponent':     config.multifit.altitude.parameters.exponent,
    }
    asmodeus.buildGnuplotTemplate('chiSquare-{}.gp'.format(quantity), config.dataset.name, context, asmodeus.datasetPath('plots'))
    log.info("Template {} finished, calling {}".format(colour('chiSquare', 'name'), colour('gnuplot', 'script')))
    os.system('gnuplot {}'.format(asmodeus.datasetPath('plots', 'chiSquare-{}.gp'.format(quantity))))

