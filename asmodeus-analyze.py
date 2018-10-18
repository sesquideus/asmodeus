#!/usr/bin/env python

import datetime, random, pprint, os, shutil, logging, io, math

from core               import asmodeus, configuration, dataset, histogram, logger
from discriminators     import magnitude, altitude, angularSpeed
from physics            import coord
from utilities          import colour as c, utilities as ut

class AsmodeusAnalyze(asmodeus.Asmodeus):
    def __init__(self):
        log.info("Initializing {}".format(c.script("asmodeus-analyze")))
        super().__init__() 
        self.configure()

    def createArgparser(self):
        super().createArgparser()

    def overrideConfig(self):
        super().overrideConfig()

    def configure(self):
        self.loadObservers()
        self.dataset.require('sightings')

    def analyze(self):
        pool        = mp.Pool(processes = self.config.mp.processes)
        path        = self.dataset.path('meteors')
        meteorFiles = os.listdir(path)
    
        self.markTime()
        results = [ ### Refactor this more
            pool.apply_async(
                observeMeteor, (self.observers[0], os.path.join(path, meteorFile), self.observers[0].horizon, self.dataset.name)
            ) for meteorFile in meteorFiles
        ]
        out = [result.get(timeout = 5) for result in results]

        log.info("Results written to {output} ({count} meteors processed from {observers} observing sites)".format(
            output      = c.path(self.dataset.path('sightings')),
            count       = len(results),
            observers   = len(self.observers),
        ))
   
        log.info("Finished in {:.6f} seconds ({:.3f} meteors per second)".format(self.runTime(), len(results) / self.runTime()))

def observeMeteor(observer, filename, minAlt, out):
    meteor = Meteor.load(filename)

    sighting = Sighting(observer, meteor)
    if sighting.brightestFrame.altAz.latitude() >= minAlt:
        sighting.save(out) 

    return True

def main(argv):
    for observer in observers:
        observer.createSkyPlot()


if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusAnalyze()
    asmo.analyze()
    
    log.info("Finished successfully")
    log.info("---------------------")






######

def main(argv):
    log.info("Magnitude detection efficiency profile is {} ({})".format(colour(config.bias.magnitude.function, 'name'), formatParameters(config.bias.magnitude.parameters)))
    log.info("Altitude detection efficiency profile is {} ({})".format(colour(config.bias.altitude.function, 'name'), formatParameters(config.bias.altitude.parameters)))
    log.info("Angular speed detection efficiency profile is {} ({})".format(colour(config.bias.angularSpeed.function, 'name'), formatParameters(config.bias.angularSpeed.parameters)))

    for observer in observers:
        observer.loadSightings()
        observer.processSightings(magDis, altDis, aspDis)
    
    log.info("Finished in {:.6f} seconds".format(asmodeus.runTime()))

if __name__ == "__main__":
    log = setupLog('root')
    config      = asmodeus.initialize('analyze')
    observers   = asmodeus.loadObservers()
    amos        = asmodeus.createAmosHistograms('amos.tsv')

    magDis      = discriminators.magnitude.function(config.bias.magnitude.function, **config.bias.magnitude.parameters._asdict())
    altDis      = discriminators.altitude.function(config.bias.altitude.function, **config.bias.altitude.parameters._asdict())
    aspDis      = discriminators.angularSpeed.function(config.bias.angularSpeed.function, **config.bias.angularSpeed.parameters._asdict())

    main(sys.argv)
    log.info("Finished successfully")
    log.info("---------------------")
