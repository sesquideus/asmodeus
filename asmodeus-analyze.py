#!/usr/bin/env python

import datetime, random, pprint, os, shutil, logging, io, math

from core               import asmodeus, configuration, dataset, histogram, logger, exceptions
from discriminator      import magnitude, altitude, angularSpeed
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
    
        try:
            bias            = self.config.bias
            self.magDis     = magnitude.MagnitudeDiscriminator.fromConfig(bias.magnitude).logInfo()
            self.altDis     = altitude.AltitudeDiscriminator.fromConfig(bias.altitude).logInfo()
            self.aspDis     = angularSpeed.AngularSpeedDiscriminator.fromConfig(bias.angularSpeed).logInfo()
        except AttributeError as e:
            raise exceptions.ConfigurationError

    def analyze(self):
        for observer in self.observers:
            observer.loadSightings()
            observer.processSightings(magDis, altDis, aspDis)

            #observer.createSkyPlot()
        
        log.info("Finished in {:.6f} seconds".format(asmodeus.runTime()))
        
if __name__ == "__main__":
    log = logger.setupLog('root')
    asmo = AsmodeusAnalyze()
    asmo.analyze()
    
    log.info("Finished successfully")
    log.info("---------------------")


