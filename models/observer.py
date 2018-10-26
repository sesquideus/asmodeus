import numpy as np, multiprocessing as mp
import datetime, yaml, sys, datetime, random, pprint, logging, os, io, dotmap
import itertools, functools


from core                       import histogram, dataset
from physics                    import coord
from models.frame               import Frame
from models.sighting            import Sighting
from models.sightingframe       import SightingFrame
from utilities                  import colour as c, utilities as utils
from discriminator.magnitude    import MagnitudeDiscriminator

log = logging.getLogger('root')

class Observer():
    def __init__(self, name, dataset, histogramSettings, **kwargs):
        self.id                 = name
        self.dataset            = dataset
        self.position           = coord.Vector3D.fromGeodetic(
                                      kwargs.get('latitude', 0),
                                      kwargs.get('longitude', 0),
                                      kwargs.get('altitude', 0)
                                  )
        self.horizon            = kwargs.get('horizon', 0)
        self.histogramSettings  = histogramSettings
        self.allSightings       = []
        self.visibleSightings   = []

        self.earthToAltAzMatrix = functools.reduce(np.dot, [np.fliplr(np.eye(3)), coord.rotMatrixY(-self.position.latitude()), coord.rotMatrixZ(-self.position.longitude())])

    def observe(self, meteor):
        log.debug("Observer {:<10} trying to see meteor {}".format(c.name(self.id), meteorFile))
        return [SightingFrame(self, frame) for frame in meteor.frames]

    # This observer's AltAz coordinates of an EarthLocation point
    # point: EarthLocation
    def altAz(self, point: coord.Vector3D) -> coord.Vector3D:
        diff = point - self.position
        return coord.Vector3D.fromNumpyVector(self.earthToAltAzMatrix @ diff.toNumpyVector())
    
    def skyChartTSV(self, filename):
        with open(filename, 'w') as output:
            print("# Timestamp                   Alt        Az           Dist       Speed          Bright    Mass     Colour", file = output)
            for sighting in self.allSightings:
                sighting.dumpTSV(output)

    def __str__(self):
        return "Observer {id:<15} at {position}".format(
            id          = c.name(self.id),
            position    = self.position.strGeodetic(),
        )
        
    def loadSightings(self):
        self.allSightings = [Sighting.load(self.dataset.path('sightings', self.id, file)) for file in os.listdir(self.dataset.path('sightings', self.id))]
        log.info("Sightings loaded ({})".format(c.num(len(self.allSightings))))
        return self.allSightings
        
    def applyBias(self, *discriminators):
        for sighting in self.allSightings:
            sighting.applyBias(*discriminators)

        self.visibleSightings = [s for s in self.allSightings if s.sighted]
        log.info("Selection bias applied ({bc} discriminators), {sc} sightings survived".format(
            bc      = c.num(len(discriminators)),
            sc      = c.num("{:6d}".format(len(self.visibleSightings))),
        ))

        return self.visibleSightings
       
    def processSightings(self, *discriminators):
        self.applyBias(*discriminators)
        
        #self.createSkyPlot()
        self.createHistograms()
        self.saveHistograms()

    def createSkyPlot(self):
        for sighting in self.visibleSightings:
            sighting.printSkyPlot(self.skyPlotFile, True)
    
    def createHistograms(self):
        log.debug("Creating histograms for observer {name}, {count} sightings to process".format(
            name        = c.name(self.id),
            count       = c.num(len(self.visibleSightings)),
        ))

        data = []
        self.histograms = {}

        for stat, properties in self.histogramSettings.items():
            self.histograms[stat] = {
                'number':   histogram.FloatHistogram,
                'time':     histogram.TimeHistogram,
            }.get(properties.xaxis, 'number')(stat, properties.min, properties.max, properties.bin)

        for sighting in self.visibleSightings:
            for stat in self.histogramSettings:
                try:
                    self.histograms[stat].add(getattr(sighting, stat))
                except KeyError as e:
                    log.warning(e)

        return self.histograms

    def saveHistograms(self):
       # amos        = asmodeus.createAmosHistograms('amos.tsv')
        for name, histogram in self.histograms.items():
            histogram.normalize()
            with open(self.dataset.path('histograms', self.id, '{}.tsv'.format(histogram.name)), 'w') as f:
                histogram.print(f)
                histogram.print()
        #    log.info("Chi-square for {} is {}".format(colour(histogram.name, 'name'), amos[name] @ histogram))

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


def observe(observer, meteor):
    observer.observe(meteor)
