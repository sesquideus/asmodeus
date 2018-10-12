import numpy as np, multiprocessing as mp
import datetime, yaml, sys, datetime, random, pprint, logging, os
import itertools, functools

import asmodeus
import discriminators.magnitude, discriminators.altitude, discriminators.angularSpeed

from models.frame           import Frame
from models.sighting        import Sighting
from models.sightingframe   import SightingFrame
from coord                  import rotMatrixX, rotMatrixY, rotMatrixZ, Vector3D
from utils                  import colour, linSpace, generateParameterSpace
from histogram              import Histogram

log = logging.getLogger('root')

class Observer():
    def __init__(self, name, histogramSettings, **kwargs):
        self.id                 = name
        self.position           = Vector3D.fromGeodetic(
                                      kwargs.get('latitude', 48),
                                      kwargs.get('longitude', 17),
                                      kwargs.get('altitude', 0)
                                  )
        self.histogramSettings  = histogramSettings
        self.allSightings       = []
        self.visibleSightings   = []

        self.earthToAltAzMatrix = functools.reduce(np.dot, [np.fliplr(np.eye(3)), rotMatrixY(-self.position.latitude()), rotMatrixZ(-self.position.longitude())])
        self.skyPlotFile        = asmodeus.datasetPath('plots', "{}.tsv".format(self.id))
       
    def observe(self, meteor):
        log.debug("Observer {:<10} trying to see meteor {}".format(colour(self.id, 'name'), meteor)) 
        return [SightingFrame(self, frame) for frame in meteor.frames]

    # This observer's AltAz coordinates of an EarthLocation point
    # point: EarthLocation
    def altAz(self, point):        
        diff = point - self.position
        return Vector3D.fromNumpyVector(self.earthToAltAzMatrix @ diff.toNumpyVector())
    
    def skyChartTSV(self, filename):
        output = open(filename, 'w')
        print("# Timestamp                   Alt        Az           Dist       Speed          Bright    Mass     Colour", file = output)

        for sighting in self.allSightings:
            sighting.dumpTSV(output)

    def __str__(self):
        return "Observer {id:<15} at {position}".format(
            id          = colour(self.id, 'name'),
            position    = self.position.strGeodetic(),
        )
        
    def loadSightings(self):
        self.allSightings = [Sighting.load(asmodeus.datasetPath('sightings', self.id, file)) for file in os.listdir(asmodeus.datasetPath('sightings', self.id))]
        log.info("Sightings loaded ({})".format(colour(len(self.allSightings), 'num')))
        return self.allSightings
        
    def applyBias(self, *discriminators):
        for sighting in self.allSightings:
            sighting.applyBias(*discriminators)

        self.visibleSightings = [s for s in self.allSightings if s.sighted]
        log.info("Selection bias applied ({bc} discriminators), {sc} sightings survived".format(
            bc      = colour(len(discriminators), 'num'),
            sc      = colour("{:6d}".format(len(self.visibleSightings)), 'num'),
        ))

        return self.visibleSightings
       
    def processSightings(self, *discriminators):
        asmodeus.remove(asmodeus.datasetPath('sightings', self.id))
        self.applyBias(*discriminators)
        
        self.createSkyPlot()
        self.createHistograms()
        self.saveHistograms()

    def createSkyPlot(self):
        for sighting in self.visibleSightings:
            sighting.printSkyPlot(self.skyPlotFile, True)
    
    def createHistograms(self):
        log.debug("Creating histograms for observer {name}, {count} sightings to process".format(
            name        = colour(self.id, 'name'),
            count       = colour(len(self.visibleSightings), 'num'),
        ))

        data = []
        histograms = {}

        for stat, properties in self.histogramSettings.items():
            histograms[stat] = Histogram(stat, properties.min, properties.max, properties.bin)

        for sighting in self.visibleSightings:
            for stat in self.histogramSettings:
                histograms[stat].add(getattr(sighting, stat))

        self.histograms = histograms
        return self.histograms

    def saveHistograms(self):
        amos        = asmodeus.createAmosHistograms('amos.tsv')
        for name, histogram in self.histograms.items():
            histogram.normalize()
            histogram.tsv(open(asmodeus.datasetPath('histograms', self.id, '{}.tsv'.format(histogram.name)), 'w'))
            log.info("Chi-square for {} is {}".format(colour(histogram.name, 'name'), amos[name] @ histogram))

    def multifit(self, quantity, settings, *fixedDiscriminators):
        if settings.repeat == 0:
            log.info("Skipping {} multifit".format(colour(quantity, 'name')))
            return

        log.info("Commencing {} multifit (average of {} repetitions)".format(colour(quantity, 'name'), colour(settings.repeat, 'num')))
        
        amos = asmodeus.createAmosHistograms('amos.tsv')
        
        resultFile = asmodeus.datasetPath('plots', 'chiSquare-{}.tsv'.format(quantity))
        if os.path.exists(resultFile):
            os.remove(resultFile)

        current = 0
        space = generateParameterSpace(**settings.parameters._asdict())
        for parameters in space:
            current += 1
            
            chiSquare = 0
            for _ in itertools.repeat(None, settings.repeat):
                testMagDis = discriminators.__getattribute__(quantity).function(settings.function, **parameters)
                self.applyBias(testMagDis, *fixedDiscriminators)
                self.createHistograms()
                chiSquare += amos[quantity] @ self.histograms[quantity]

            chiSquare /= settings.repeat

            log.info("{current} / {total}: {params} | chi-square {chisq:8.6f}".format(
                params      = ", ".join(["{parameter} = {value}".format(parameter = parameter, value = colour("{:6.3f}".format(value), 'param')) for parameter, value in sorted(parameters.items())]),
                current     = colour("{:6d}".format(current), 'num'),
                total       = colour("{:6d}".format(len(space)), 'num'),
                chisq       = chiSquare,
            ))

            print("{params}\t{chisq:.9f}".format(
                params      = "\t".join("{:6.3f}".format(parameter) for name, parameter in sorted(parameters.items())),
                chisq       = chiSquare,
            ), file = open(resultFile, 'a'))

