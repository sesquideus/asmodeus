import numpy as np
import logging
import itertools
import functools
import os


from core                       import histogram
from physics                    import coord
from models.sighting            import Sighting
from models.sightingframe       import SightingFrame
from utilities                  import colour as c, utilities as utils

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
        self.skyPlotDir         = self.dataset.path('plots', self.id)

    def observe(self, meteor):
        log.debug("Observer {} trying to see meteor {}".format(c.name(self.id), meteor))
        return [SightingFrame(self, frame) for frame in meteor.frames]

    def altAz(self, point: coord.Vector3D) -> coord.Vector3D:
        """
            Returns AltAz coordinates of an EarthLocation point as observed by this observer
            point: EarthLocation
        """
        diff = point - self.position
        return coord.Vector3D.fromNumpyVector(self.earthToAltAzMatrix @ diff.toNumpyVector())

    def __str__(self):
        return "Observer {id} at {position}".format(
            id          = c.name(self.id),
            position    = self.position.strGeodetic(),
        )

    def loadSightings(self):
        dir = self.dataset.path('sightings', self.id)
        log.debug("Observer {obs}: loading sightings from {dir}".format(
            obs         = c.name(self.id),
            dir         = c.path(dir)),
        )

        self.allSightings = [Sighting.load(self.dataset.path('sightings', self.id, file)) for file in os.listdir(dir)]
        log.info("Observer {}: {} sightings loaded".format(c.name(self.id), c.num(len(self.allSightings))))
        return self.allSightings

    def setDiscriminators(self, discriminators):
        self.discriminators = discriminators

    def applyBias(self):
        for sighting in self.allSightings:
            sighting.applyBias(*self.discriminators)
            log.debug("Meteor was " + (c.ok("detected") if sighting.sighted else c.err("not detected")))

        self.visibleSightings = [s for s in self.allSightings if s.sighted]
        log.info("Selection bias applied ({dc} discriminators), {sc} sightings survived ({pct})".format(
            dc      = c.num(len(self.discriminators)),
            sc      = c.num(len(self.visibleSightings)),
            pct     = c.num("{:5.2f}%".format(100 * len(self.visibleSightings) / len(self.allSightings) if len(self.allSightings) > 0 else 0)),
        ))

        return self.visibleSightings

    def processSightings(self):
        self.applyBias()
        self.createHistograms()
        self.saveHistograms()

    @classmethod
    def skyPlotHeader(cls):
        return "#                timestamp       t        s    alt       az      d      ele      v       as            m           F0           F      mag"

    def createSkyPlot(self):
        log.info("Creating a sky plot for observer {obs}".format(obs = c.name(self.id)))
        self.dataset.create('plots', self.id, exist_ok = True)

        with open(self.dataset.path('plots', self.id, 'sky.tsv'), 'a') as file:
            print(self.skyPlotHeader(), file = file)
            for sighting in self.visibleSightings:
                sighting.printToSkyPlot(file)

    def plotSkyPlot(self, config):
        log.info("Plotting sky for observer {}".format(c.name(self.id)))
        
        context = {
            'pixels':   config.pixels,
            'dark':     config.dark,
            'quantity': 'angularSpeed',
            'log':      False,
            'column':   9,
            'palette': [
                ( 0, '#0000C0'),
                (15, '#00E000'),
                (25, '#FFFF00'),
                (35, '#FFFFFF'),
            ],
            'cblow':    0,
            'cbhigh':   40,
            'observer':     self.id,
            'dataset':      self.dataset.name,
        }

        utils.renderTemplate('sky.gp', context, self.dataset.path('plots', self.id))

        log.info("Template for {name} finished, calling {script}".format(
            name    = c.name('chiSquare'),
            script  = c.script('gnuplot'),
        ))
        os.system('gnuplot {}'.format(self.dataset.path('plots', self.id, 'sky.gp')))

    def createHistograms(self):
        log.info("Creating histograms for observer {name}, {count} sightings to process".format(
            name        = c.name(self.id),
            count       = c.num(len(self.visibleSightings)),
        ))

        self.histograms = {}

        for stat, properties in self.histogramSettings.items():
            self.histograms[stat] = {
                'number':   histogram.FloatHistogram,
                'time':     histogram.TimeHistogram,
            }.get(properties.xaxis, 'number')(stat, properties.min, properties.max, properties.bin)

        for sighting in self.visibleSightings:
            for stat in self.histogramSettings:
                try:
                    self.histograms[stat].add(getattr(sighting.asPoint(), stat))
                except KeyError as e:
                    log.warning("Unknown property {prop} -- {err}".format(
                        prop    = c.param(stat),
                        err     = e,
                    ))

        return self.histograms

    def saveHistograms(self):
        # amos        = asmodeus.createAmosHistograms('amos.tsv')
        log.debug("Saving histograms for observer {name}".format(name = c.name(self.id)))
        self.dataset.create('histograms', self.id)

        for name, hist in self.histograms.items():
            hist.normalize()
            with open(self.dataset.path('histograms', self.id, '{}.tsv'.format(hist.name)), 'w') as f:
                hist.print(f)
        #    log.info("Chi-square for {} is {}".format(colour(histogram.name, 'name'), amos[name] @ histogram))

    def multifit(self, quantity, settings, *fixedDiscriminators):
        if settings.repeat == 0:
            log.info("Skipping {} multifit".format(c.name(quantity)))
            return

        log.info("Commencing {} multifit (average of {} repetitions)".format(c.name(quantity), c.num(settings.repeat)))

        amos = asmodeus.createAmosHistograms('amos.tsv')

        resultFile = asmodeus.datasetPath('plots', 'chiSquare-{}.tsv'.format(quantity))
        if os.path.exists(resultFile):
            os.remove(resultFile)

        current = 0
        space = generateParameterSpace(**settings.parameters.toDict())
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
                params      = ", ".join(["{parameter} = {value}".format(
                    parameter = parameter,
                    value = c.param("{:6.3f}".format(value))
                ) for parameter, value in sorted(parameters.items())]),
                current     = c.num("{:6d}".format(current)),
                total       = c.num("{:6d}".format(len(space))),
                chisq       = chiSquare,
            ))

            print("{params}\t{chisq:.9f}".format(
                params      = "\t".join("{:6.3f}".format(parameter) for name, parameter in sorted(parameters.items())),
                chisq       = chiSquare,
            ), file = open(resultFile, 'a'))


def observe(observer, meteor):
    observer.observe(meteor)
