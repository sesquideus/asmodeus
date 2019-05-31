import logging
import itertools
import functools
import os
import math
import numpy as np
import scipy.stats
import pandas

from matplotlib import pyplot
from matplotlib.ticker import ScalarFormatter
from pprint import pprint as pp
from astropy.time import Time

from core                       import exceptions
from physics                    import coord
from models.sighting            import Sighting, PointSighting
from models.sightingframe       import SightingFrame
from utilities                  import colour as c, utilities as utils

log = logging.getLogger('root')


class Observer():
    def __init__(self, name, dataset, **kwargs):
        self.id                 = name
        self.dataset            = dataset
        self.position           = coord.Vector3D.fromGeodetic(
                                      kwargs.get('latitude', 0),
                                      kwargs.get('longitude', 0),
                                      kwargs.get('altitude', 0)
                                  )
        self.horizon            = kwargs.get('horizon', 0)

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
        frames = [SightingFrame(self, frame) for frame in meteor.frames]
        return [frame for frame in frames if frame.altitude >= self.horizon]

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

    def createDataframe(self):
        self.dataframe = pandas.DataFrame.from_records(
            [sighting.asTuple() for sighting in self.sightings],
            columns     = PointSighting.columns,
        )
        log.info(f"Dataframe created with {c.num(len(self.dataframe.index))} rows")
    
    def loadSightings(self):
        log.info(f"Loading sightings from {c.path(self.dataset.path('sightings'))}")

        dicts = {}
        for sf in os.listdir(self.dataset.path('sightings', self.id)):
            sighting = Sighting.load(self.dataset.path('sightings', self.id, sf))
            dicts[sighting.id] = sighting.asDict()

        log.info(f"Loaded {c.num(len(dicts))} sightings")
        self.createDataframe()

    def loadDataframe(self):
        filename = self.dataset.path('sightings', self.id, 'sky.tsv')
        log.info(f"Loading a dataframe from {c.path(filename)}")
        
        self.dataframe = pandas.read_csv(filename, sep = '\t') 
        self.dataframe['mjd'] = Time(self.dataframe.timestamp.to_numpy(dtype = 'datetime64[ns]')).mjd
        self.dataframe['logInitMass'] = np.log10(self.dataframe.initMass.to_numpy(dtype = 'float'))

        print(self.dataframe)
        log.info(f"Dataframe created with {c.num(len(self.dataframe.index))} rows")

    def saveDataframe(self):
        filename = self.dataset.path('sightings', self.id, 'sky.tsv')
        log.info(f"Saving a TSV file for observer {c.name(self.id)} {c.path(filename)}")
        self.dataframe.to_csv(filename, sep = '\t')

    def setDiscriminators(self, discriminators):
        self.discriminators = discriminators
        self.biasFunction = lambda row: all([disc.compute(row[prop]) for prop, disc in self.discriminators.items()])

    def applyBias(self):
        log.info(f"Applying bias DPFs")
        self.dataframe['visible'] = self.dataframe.apply(self.biasFunction, axis = 1)
        self.visible = self.dataframe[self.dataframe.visible]
        log.info(f"Bias applied, {c.num(len(self.visible.index))}/{c.num(len(self.dataframe.index))} sightings marked as detected")

    def plotSky(self):
        path = self.dataset.path('plots', self.id, 'sky.png')
        log.info(f"Plotting sky for observer {c.name(self.id)} ({c.path(path)})")
        self.dataset.create('plots', self.id)

        azimuths    = self.visible.azimuth
        altitudes   = 90 - self.visible.altitude
        colours     = np.maximum(np.log10(self.visible.lumPower), -12)
        sizes       = 0.01 * np.log10(self.visible.fluxDensity * 1e12 + 1)**4

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
            path,
            bbox_inches = 'tight',
            facecolor = 'black',
        )

    def makeKDEs(self):
        log.info(f"Creating KDEs for observer {c.name(self.id)}, {c.num(len(self.visible.index))} sightings to process")
        self.dataset.create('analyses', 'kdes', self.id, exist_ok = True)

        for stat, params in self.settings.kdes.quantities.items():       
            self.makeKDE(stat, **params)

    def makeKDE(self, stat, *, min, max, bin, **kwargs):
        log.info(f"Creating a KDE for {c.param(stat)}")
        points = 20 * (max - min) // bin
        space = np.linspace(min, max, points)
        pdf = self.computeKDE(stat).evaluate(space)

        figure, axes = self.emptyFigure()
        axes.fill_between(space, 0, pdf, alpha = 0.5)
        figure.savefig(self.dataset.path('analyses', 'kdes', self.id, f"{stat}.png"))
        pyplot.close(figure)

    def computeKDE(self, stat):
        return scipy.stats.gaussian_kde(self.visible[stat])

    def makeHistograms(self):
        log.info(f"Creating histograms for observer {c.name(self.id)}, {c.num(len(self.visible.index))} sightings to process")
        self.dataset.create('analyses', 'histograms', self.id, exist_ok = True)

        for stat, params in self.settings.histograms.quantities.items():       
            self.makeHistogram(stat, params)

    def makeHistogram(self, stat, params):
        log.info(f"Creating a histogram for {c.param(stat)}")
        hist, edges = self.computeHistogram(stat, params)

        figure, axes = self.emptyFigure()
        axes.bar(edges[:-1], hist, width = params.bin, alpha = 0.5, align = 'edge', color = (0.3, 0.0, 0.7, 0.5))
        figure.savefig(self.dataset.path('analyses', 'histograms', self.id, f"{stat}.png"))
        pyplot.close(figure)

        np.savetxt(
            self.dataset.path('analyses', 'histograms', self.id, f"{stat}.tsv"),
            np.vstack((edges[:-1], hist)).T,
            delimiter       = '\t',
            fmt             = ('%.10f', '%.10f'),
        )

    def computeHistogram(self, stat, params):
        count = int(np.ceil((params.max - params.min) / params.bin))
        bins = np.linspace(params.min, params.max, count + 1)
        hist, edges = np.histogram(self.visible[stat], bins = bins, range = (params.min, params.max), density = True)
        return hist, edges

    def emptyFigure(self):
        figure, axes = pyplot.subplots()
        figure.tight_layout(rect = (0.05, 0, 1, 1))
        figure.set_size_inches(6, 4)
        figure.set_dpi(300)
        axes.grid(linewidth = 0.2, linestyle = ':')

        return figure, axes

    def makeScatters(self):
        log.info(f"Creating {c.name('scatter plots')} for observer {c.name(self.id)}, {c.num(len(self.visible.index))} sightings to process")
        self.dataset.create('analyses', 'scatters', self.id, exist_ok = True)

        for scatter in self.settings.scatters:
            self.crossScatter(scatter)

    def crossScatter(self, scatter):
        """
            Render a cross-scatter plot of four variables using a scatter dotmap
            scatter: dotmap in shape
            -   x:          <property to plot on x axis>
                y:          <property to plot on y axis>
                colour:     <property to use for colouring the dots>
                size:       <property to determine dot size>
        """
        log.info(f"Creating a scatter plot for {c.param(scatter.x)} × {c.param(scatter.y)}")

        try:
            xparams = self.settings.quantities[scatter.x]
            yparams = self.settings.quantities[scatter.y]
            figure, axes = self.emptyFigure()

            axes.set_xlim(xparams.min, xparams.max)
            axes.set_ylim(yparams.min, yparams.max)
            axes.xaxis.set_major_formatter(ScalarFormatter(useOffset = False))
            
            axes.scatter(
                self.visible[scatter.x],
                self.visible[scatter.y],
                c           = self.visible[scatter.colour],
                s           = 4 * np.exp(-self.visible.appMag / 5),
                cmap        = scatter.get('cmap', 'viridis_r'),
                alpha       = 1,
                linewidths  = 0,
            )
            figure.savefig(self.dataset.path('analyses', 'scatters', self.id, f"{scatter.x}-{scatter.y}.png"))
            pyplot.close(figure)
        except KeyError as e:
            raise exceptions.ConfigurationError(f"Invalid scatter configuration parameter {e}") from e

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
