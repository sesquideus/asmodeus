import logging
import itertools
import functools
import os
import math
import numpy as np
import scipy.stats
import pandas as pd

from matplotlib import pyplot
from pprint import pprint as pp

from core                       import histogram
from physics                    import coord
from models.sighting            import Sighting, PointSighting
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

        self.earthToAltAzMatrix = functools.reduce(np.dot, [
                                    np.fliplr(np.eye(3)),
                                    coord.rotMatrixY(-self.position.latitude()),
                                    coord.rotMatrixZ(-self.position.longitude()),
                                ])

    def observe(self, meteor):
        log.debug("Observer {obs} trying to see meteor {} ({} recorded frames)".format(
            obs = c.name(self.id),
            met = c.name(meteor),
            nf  = c.num(len(meteor.frames))
        ))
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

    def loadSightingsPickle(self):
        dir = self.dataset.path('sightings', self.id)
        log.debug("Observer {obs}: loading sightings from {dir}".format(
            obs         = c.name(self.id),
            dir         = c.path(dir)),
        )

        self.allSightings = [Sighting.load(self.dataset.path('sightings', self.id, file)) for file in os.listdir(dir)]
        log.info("Observer {obs}: {num} sightings loaded".format(
            obs         = c.name(self.id),
            num         = c.num(len(self.allSightings))
        ))
        return self.allSightings

    def loadSightingsTSV(self):
        pass


    def loadSightingsDataFrame(self):
        log.info("Creating a pandas dataframe")

        dicts = {}
        for sf in os.listdir(self.dataset.path('sightings', self.id)):
            sighting = Sighting.load(self.dataset.path('sightings', self.id, sf))
            dicts[sighting.id] = sighting.asDict()

        log.info(f"Loaded {c.num(len(dicts))} sightings")

        self.dataframe = pd.DataFrame.from_dict(
            dicts,
            orient = 'index',
            columns = PointSighting.columns,
        )

        log.info(f"Dataframe loaded ({c.num(len(self.dataframe.index))} rows)")

    def setDiscriminators(self, discriminators):
        self.discriminators = discriminators
        self.biasFunction = lambda row: all([disc.compute(row[prop]) for prop, disc in self.discriminators.items()])

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

    def applyBiasDataframe(self):
        self.dataframe['visible'] = self.dataframe.apply(self.biasFunction, axis = 1)
        self.visible = self.dataframe[self.dataframe.visible]

    def analyzeSightings(self):
        self.applyBiasDataframe()
        self.kde()

    @classmethod
    def skyPlotHeader(cls):
        return "#                timestamp     alt       az      d      ele      v       as            m           F0           F   absmag  appmag"

    def printTSV(self):
        filename = self.dataset.path('tsv', self.id, 'sky.tsv')
        log.info("Saving a TSV file for observer {obs} ({name})".format(
            obs     = c.name(self.id),
            name    = filename,
        ))
        
        self.dataset.create('tsv', self.id, exist_ok = True)

        with open(filename, 'w') as file:
            print(self.skyPlotHeader(), file = file)
            for sighting in self.visibleSightings:
                sighting.printTSV(file)

    def plotSkyPlot(self, config):
        log.info("Plotting sky for observer {}".format(c.name(self.id)))
        self.dataset.create('plots', self.id)

        if config.observations.streaks:
            dots = [point.asDotMap() for sighting in self.visibleSightings for point in sighting.frames]
        else:
            dots = self.visibleSightings

        azimuths    = np.array([math.radians(sighting.azimuth) for sighting in dots])
        altitudes   = np.array([90 - sighting.altitude for sighting in dots])
        colours     = np.array([math.log10(sighting.luminousPower) if sighting.luminousPower > 1e-12 else -12 for sighting in dots])
        sizes       = np.array([0.01 * (math.log10(sighting.fluxDensity * 1e12 + 1))**4 for sighting in dots])

        fig = pyplot.figure(figsize = (5, 5), dpi = 300, facecolor  = 'black')
        ax = fig.add_subplot(111, projection = 'polar')
        cx = ax.scatter(azimuths, altitudes, c = colours, s = sizes, cmap = 'hot', alpha = 1, linewidths = 0)
               
        ax.set_theta_zero_location('N', offset=0)
        ax.set_ylim(0, 90.5)
        ax.set_facecolor('black')
        ax.axes.xaxis.set_ticks(np.linspace(0, 2*np.pi, 25))
        #ax.axes.xaxis.set_ticklabels([])
        ax.axes.yaxis.set_ticklabels([])
        ax.axes.yaxis.set_ticks(np.linspace(0, 90, 7))
        ax.grid(linewidth = 0.1, color = 'white')
        pyplot.savefig(
            self.dataset.path('plots', self.id, 'sky.png'),
            bbox_inches = 'tight',
            facecolor = 'black',
        )

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
            }.get(properties.xaxis, 'number')(properties.min, properties.max, properties.bin, name = stat)

        for sighting in self.visibleSightings:
            for stat in self.histogramSettings:
                try:
                    self.histograms[stat].add(getattr(sighting.asPoint(), stat))
                except KeyError as e:
                    log.warning("{prop} out of range: {err}".format(
                        prop    = c.param(stat),
                        err     = e,
                    ))

        return self.histograms

    def kde(self):
        log.info("Creating KDEs for observer {name}, {count} sightings to process".format(
            name        = c.name(self.id),
            count       = c.num(len(self.dataframe.index)),
        ))
        self.dataset.create('histograms', self.id, exist_ok = True)

        for stat, params in self.histogramSettings.items():       
            binCount = (params.max - params.min) // params.bin
            space = np.linspace(params.min, params.max, binCount * 20)
            pdf = self.propertyKDE(stat, params).evaluate(space)

            hist, edges = self.propertyHistogram(stat, params)

            figure, axes = pyplot.subplots()
            figure.tight_layout(rect = (0, 0, 1, 1))
            figure.set_size_inches(6, 4)
            figure.set_dpi(300)
            
            axes.fill_between(space, 0, pdf, alpha = 0.5)
            axes.grid(linewidth = 0.2, linestyle = ':')
            axes.bar(edges, hist, width = params.bin, alpha = 0.5, align = 'edge', color = (1, 0.2, 0, 0.5))
            figure.savefig(self.dataset.path('histograms', self.id, '{}-kde.png'.format(stat)), bbox_inches = 'tight')

            log.info(f"Created a KDE for {c.param(stat)}")

    def propertyKDE(self, stat, params):
        kernel = scipy.stats.gaussian_kde(self.visible[stat])
        return kernel        

    def propertyHistogram(self, stat, params):
        count = (params.max - params.min) // params.bin
        bins = np.linspace(params.min, params.max, count + 1)
        hist, edges = np.histogram(self.visible[stat], bins = bins, range = (params.min, params.max), density = True)
        return hist, edges[:-1]

    def saveHistograms(self):
        # amos        = asmodeus.createAmosHistograms('amos.tsv')
        log.debug("Saving histograms for observer {name}".format(name = c.name(self.id)))
        self.dataset.create('histograms', self.id)

        for name, hist in self.histograms.items():
            hist.normalize()
            with open(self.dataset.path('histograms', self.id, '{}.tsv'.format(hist.name)), 'w') as f:
                hist.print(f)
            with open(self.dataset.path('histograms', self.id, '{}.png'.format(hist.name)), 'w') as f:
                hist.render(f.name)


        #    log.info("Chi-square for {} is {}".format(colour(histogram.name, 'name'), amos[name] @ histogram))

    def minimize(self, settings):
        log.info("Employing {method} method, {rep} evaluation repetition{s}".format(
            method      = c.name(settings.method),
            rep         = c.num(settings.repeat),
            s           = '' if settings.repeat == 1 else 's',
        ))
        self.minimizeExhaustive(settings)                                                                      

    def minimizeExhaustive(self, settings):
        for key, quantity in settings.quantities.items():
            log.info("Using {qua} DPF function {fun}".format(
                qua     = c.param(key),
                fun     = c.name(quantity.function),
            ))
            for key, parameter in quantity.parameters.items():
                log.info("    Varying {param} from {min} to {max}, step size {step}".format(
                    param   = c.param(key),
                    min     = c.num(parameter.min),
                    max     = c.num(parameter.max),
                    step    = c.num(parameter.step),
                ))



    def multifit(self, quantity, settings, *fixedDiscriminators):
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
