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
    def __init__(self, id, dataset, *, name, latitude, longitude, altitude, horizon, streaks):
        self.id                 = id
        self.name               = name
        self.dataset            = dataset
        self.position           = coord.Vector3D.fromGeodetic(latitude, longitude, altitude)
        self.horizon            = horizon
        self.streaks            = streaks

        self.earthToAltAzMatrix = functools.reduce(np.dot, [
                                    np.fliplr(np.eye(3)),
                                    coord.rotMatrixY(-self.position.latitude()),
                                    coord.rotMatrixZ(-self.position.longitude()),
                                ])

    def altAz(self, point: coord.Vector3D) -> coord.Vector3D:
        """
            Returns AltAz coordinates of an EarthLocation point as observed by this observer
            point: EarthLocation
        """
        return coord.Vector3D.fromNumpyVector(self.earthToAltAzMatrix @ (point - self.position).toNumpyVector())

    def __str__(self):
        return "Observer {id} at {position}".format(
            id          = c.name(self.id),
            position    = self.position.strGeodetic(),
        )

    def createDataframe(self):
        if self.streaks:
            self.dataframe = pandas.DataFrame.from_records(
                [frame.asTuple() for sighting in self.sightings for frame in sighting.frames],
                columns     = PointSighting.columns,
            )
        else:
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

        azimuths    = np.radians(self.visible.azimuth)
        altitudes   = 90 - self.visible.altitude
        colours     = -self.visible.appMag
        sizes       = 8 * np.exp(-self.visible.appMag / 2)

        figure, axes = pyplot.subplots(subplot_kw = {'projection': 'polar'})
        
        figure.tight_layout(rect = (0, 0, 1, 1))
        figure.set_size_inches(8, 8)
        figure.set_dpi(300)
        figure.set_facecolor('black')

        axes.xaxis.set_ticks(np.linspace(0, 2 * np.pi, 25))
        axes.yaxis.set_ticklabels([])
        axes.yaxis.set_ticks(np.linspace(0, 90, 7))
        axes.set_ylim(0, 90.5)
        axes.set_facecolor('black')
        axes.grid(linewidth = 0.2, color = 'white')

        axes.scatter(azimuths, altitudes, c = colours, s = sizes, cmap = 'hot', alpha = 1, linewidths = 0)

        figure.savefig(path, facecolor = 'black')


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
        axes.bar(edges[:-1], hist, width = params.bin, alpha = 0.5, align = 'edge', color = (0.1, 0.7, 0.4, 0.5), edgecolor = (0.1, 0.3, 0.2, 1))
        axes.set_xlabel(params.name)
        axes.set_ylabel('relative count')
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
        pyplot.rcParams['font.family'] = "Minion Pro"
        figure, axes = pyplot.subplots()
        figure.tight_layout(rect = (0.07, 0.05, 1, 0.97))
        figure.set_size_inches(6, 4)
        figure.set_dpi(300)
        axes.grid(linewidth = 0.2, linestyle = ':')
        axes.xaxis.set_major_formatter(ScalarFormatter(useOffset = False))
        axes.yaxis.set_major_formatter(ScalarFormatter(useOffset = False))

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
        log.info(f"Creating a scatter plot for {c.param(scatter.x):>20} × {c.param(scatter.y):>20}")

        try:
            xparams = self.settings.quantities[scatter.x]
            yparams = self.settings.quantities[scatter.y]
            figure, axes = self.emptyFigure()

            axes.tick_params(axis = 'both', which = 'major', labelsize = 10)
            axes.set_xlim(xparams.min, xparams.max)
            axes.set_ylim(yparams.min, yparams.max)
            axes.set_xlabel(xparams.name, fontdict = {'fontsize': 10})
            axes.set_ylabel(yparams.name, fontdict = {'fontsize': 10})
            axes.set_title(f"{self.name} – {xparams.name} × {yparams.name}", fontdict = {'fontsize': 12})
            
            axes.scatter(
                self.visible[scatter.x],
                self.visible[scatter.y],
                c           = self.visible[scatter.colour],
                s           = 3 * np.exp(-self.visible.appMag / 3),
                cmap        = scatter.get('cmap', 'viridis_r'),
                alpha       = 1,
                linewidths  = 0,
            )
            figure.savefig(self.dataset.path('analyses', 'scatters', self.id, f"{scatter.x}-{scatter.y}.png"))
            pyplot.close(figure)
        except KeyError as e:
            log.error(f"Invalid scatter configuration parameter {c.param(e)}") 

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
