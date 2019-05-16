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

    def loadSightingsDataFrame(self):
        log.info(f"Loading sightings from {c.path(self.dataset.path('sightings'))}")

        dicts = {}
        for sf in os.listdir(self.dataset.path('sightings', self.id)):
            sighting = Sighting.load(self.dataset.path('sightings', self.id, sf))
            dicts[sighting.id] = sighting.asDict()

        log.info(f"Loaded {c.num(len(dicts))} sightings, creating a dataframe")

        self.dataframe = pd.DataFrame.from_dict(
            dicts,
            orient = 'index',
            columns = PointSighting.columns,
        )

        log.info(f"Dataframe created with {c.num(len(self.dataframe.index))} rows")

    def setDiscriminators(self, discriminators):
        self.discriminators = discriminators
        self.biasFunction = lambda row: all([disc.compute(row[prop]) for prop, disc in self.discriminators.items()])

    #def applyBias(self):
    #    for sighting in self.allSightings:
    #        sighting.applyBias(*self.discriminators)
    #        log.debug("Meteor was " + (c.ok("detected") if sighting.sighted else c.err("not detected")))

    #    self.visibleSightings = [s for s in self.allSightings if s.sighted]
    #    log.info("Selection bias applied ({dc} discriminators), {sc} sightings survived ({pct})".format(
    #        dc      = c.num(len(self.discriminators)),
    #        sc      = c.num(len(self.visibleSightings)),
    #        pct     = c.num("{:5.2f}%".format(100 * len(self.visibleSightings) / len(self.allSightings) if len(self.allSightings) > 0 else 0)),
    #    ))

    #    return self.visibleSightings

    def applyBias(self):
        self.dataframe['visible'] = self.dataframe.apply(self.biasFunction, axis = 1)
        self.visible = self.dataframe[self.dataframe.visible]
        log.info(f"Bias applied, {c.num(len(self.visible.index))} sightings marked as detected")

    def analyzeSightings(self):
        self.applyBias()
        self.renderKDEs()
        self.renderHistograms()

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

        with open(filename, 'w') as file, pd.option_context('display.max_rows', None, 'display.max_columns', 100, 'display.width', 1000):
            print(self.visible, file = file)


    def plotSkyPlot(self, config):
        log.info(f"Plotting sky for observer {c.name(self.id)}")
        self.dataset.create('plots', self.id)

        if config.observations.streaks:
            dots = [point.asDotMap() for sighting in self.visible for point in sighting.frames]
        else:
            dots = self.visible

        azimuths    = dots.azimuth
        altitudes   = 90 - dots.altitude
        colours     = np.maximum(np.log10(dots.lumPower), -12)
        sizes       = 0.01 * np.log10(dots.fluxDensity * 1e12 + 1)**4

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

    def renderKDEs(self):
        log.info(f"Creating {c.name('KDE')}s for observer {c.name(self.id)}, {c.num(len(self.visible.index))} sightings to process")
        self.dataset.create('analyses', self.id, 'kdes', exist_ok = True)

        for stat, params in self.histogramSettings.items():       
            points = 20 * (params.max - params.min) // params.bin
            space = np.linspace(params.min, params.max, points)
            pdf = self.propertyKDE(stat, params).evaluate(space)

            figure, axes = self.emptyFigure()
            axes.fill_between(space, 0, pdf, alpha = 0.5)
            figure.savefig(self.dataset.path('analyses', self.id, 'kdes', f"{stat}.png"))

            log.info(f"Created a KDE for {c.param(stat)}")

    def propertyKDE(self, stat, params):
        kernel = scipy.stats.gaussian_kde(self.visible[stat])
        return kernel

    def renderHistograms(self):
        log.info(f"Creating {c.name('histograms')} for observer {c.name(self.id)}, {c.num(len(self.visible.index))} sightings to process")
        self.dataset.create('analyses', self.id, 'histograms', exist_ok = True)

        for stat, params in self.histogramSettings.items():       
            hist, edges = self.propertyHistogram(stat, params)
            figure, axes = self.emptyFigure()

            axes.bar(edges[:-1], hist, width = params.bin, alpha = 0.5, align = 'edge', color = (0.6, 0.0, 0.7, 0.5))
            figure.savefig(self.dataset.path('analyses', self.id, 'histograms', f"{stat}.png"))

            log.info(f"Created a histogram for {c.param(stat)}")

    def propertyHistogram(self, stat, params):
        count = (params.max - params.min) // params.bin
        bins = np.linspace(params.min, params.max, count + 1)
        hist, edges = np.histogram(self.visible[stat], bins = bins, range = (params.min, params.max), density = True)
        return hist, edges

    def emptyFigure(self):
        figure, axes = pyplot.subplots()
        figure.tight_layout(rect = (0.1, 0, 1, 1))
        figure.set_size_inches(6, 4)
        figure.set_dpi(300)
        axes.grid(linewidth = 0.2, linestyle = ':')

        return figure, axes
            
        

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
            log.info(f"Using {c.param(key)} DPF function {c.name(quantity.function)}")
            for key, parameter in quantity.parameters.items():
                log.info(f"    Varying {c.param(key)} from {c.num(parameter.min)} to {c.num(parameter.max)}, step size {c.num(parameter.step)}")

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
