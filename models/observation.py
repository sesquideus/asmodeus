import datetime
import io
import os
import logging
import random

import time
import multiprocessing as mp
import pandas

from core.parallel      import parallel
from models.observer    import Observer
from models.meteor      import Meteor
from models.sighting    import Sighting, PointSighting
from physics            import coord
from utilities          import colour as c

log = logging.getLogger('root')


class Observation():
    def __init__(self, dataset, observer, population, config):
        log.debug(f"Creating a new observation for dataset {c.name(dataset.name)} with observer {c.name(observer.name)}")
        self.dataset        = dataset
        self.observer       = observer
        self.population     = population
        self.config         = config

    def observe(self, *, processes = 1, period = 1):
        log.info(f"Calculating {c.num(self.population.count)} observations "
            f"using {c.num(processes)} processes, "
            f"""meteors saved as {c.over(f"{'streaks' if self.config.streaks else 'points'}")}"""
        )

        meteorFiles = self.dataset.list('meteors')
        self.count = 0

        argList = [(
            self.dataset.path('meteors', meteorFile),
            self.dataset.path('sightings', self.observer.id, meteorFile),
        ) for meteorFile in meteorFiles]
        total = len(argList)

        self.sightings = parallel(
            observe,
            argList,
            initializer = initObserve,
            initargs    = (self.observer, self.config.streaks),
            processes   = processes,
            action      = "Observing meteors",
            period      = period,
        )
        self.createDataframe()

    def save(self):
        log.debug(f"""Saving the observed population as {c.over(f"{'streaks' if self.config.streaks else 'points'}")} to {c.path(self.dataset.name)}""")
        directory = self.dataset.create('sightings', self.observer.id)

        self.saveDataframe()

     #   for sighting in self.sightings:
     #       sighting.save(directory, streak = self.config.streaks)
        
    def createDataframe(self):
        log.info(f"Creating a dataframe...")
        self.dataframe = pandas.DataFrame.from_records(
            [frame.asTuple() for sighting in self.sightings for frame in sighting.frames],
            columns     = Sighting.columns,
        )
        log.info(f"Dataframe created with {c.num(len(self.dataframe.index))} rows")

    def loadDataframe(self):
        filename = self.dataset.path('sightings', self.id, 'sky.tsv')
        log.info(f"Loading a dataframe from {c.path(filename)}")
        
        self.dataframe = pandas.read_csv(filename, sep = '\t') 
        self.dataframe['mjd'] = Time(self.dataframe.timestamp.to_numpy(dtype = 'datetime64[ns]')).mjd
        self.dataframe['logInitMass'] = np.log10(self.dataframe.initMass.to_numpy(dtype = 'float'))

        log.info(f"Created a dataframe with {c.num(len(self.dataframe.index))} rows")

    def saveDataframe(self):
        filename = self.dataset.path('sightings', self.observer.id, 'sky.tsv')
        log.info(f"Saving a TSV file for observer {c.name(self.observer.id)} {c.path(filename)}")
        self.dataframe.to_csv(filename, sep = '\t', float_format = '%6g')

    def saveMetadata(self, directory):
        pass
        
    def makeKDEs(self):
        log.info(f"Creating KDEs for observer {c.name(self.id)}, {c.num(len(self.visible.index))} sightings to process")
        self.dataset.create('analyses', 'kdes', self.id, exist_ok = True)

        for stat, params in self.settings.kdes.quantities.items():       
            self.makeKDE(stat, **params)

    def applyBias(self):
        log.info(f"Applying bias DPFs")
        self.dataframe['visible'] = self.dataframe.apply(self.biasFunction, axis = 1)
        self.visible = self.dataframe[self.dataframe.visible]
        log.info(f"Bias applied, {c.num(len(self.visible.index))}/{c.num(len(self.dataframe.index))} sightings marked as detected")

    def computeKDE(self, stat):
        return scipy.stats.gaussian_kde(self.visible[stat])

    def renderKDE(self, stat, *, min, max, bin, **kwargs):
        log.info(f"Creating a KDE for {c.param(stat)}")
        points = 20 * (max - min) // bin
        space = np.linspace(min, max, points)
        pdf = self.computeKDE(stat).evaluate(space)

        figure, axes = self.emptyFigure()
        axes.fill_between(space, 0, pdf, alpha = 0.5)
        figure.savefig(self.dataset.path('analyses', 'kdes', self.id, f"{stat}.png"))
        pyplot.close(figure)

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
        pyplot.rcParams['mathtext.fontset'] = "dejavuserif"
        figure, axes = pyplot.subplots()
        figure.tight_layout(rect = (0.07, 0.05, 1, 0.97))
        figure.set_size_inches(8, 5)
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
        log.info(f"Creating a scatter plot for {c.param(scatter.x):>20} × {c.param(scatter.y):>20} (colour {c.param(scatter.colour):>20})")

        try:
            xparams = self.settings.quantities[scatter.x]
            yparams = self.settings.quantities[scatter.y]
            cparams = self.settings.quantities[scatter.colour]
            figure, axes = self.emptyFigure()

            axes.tick_params(axis = 'both', which = 'major', labelsize = 12)
            axes.set_xlim(xparams.min, xparams.max)
            axes.set_ylim(yparams.min, yparams.max)
            axes.set_xlabel(xparams.name, fontdict = {'fontsize': 12})
            axes.set_ylabel(yparams.name, fontdict = {'fontsize': 12})
            axes.set_title(f"{self.name} – {xparams.name} × {yparams.name}", fontdict = {'fontsize': 14})
            
            sc = axes.scatter(
                self.visible[scatter.x],
                self.visible[scatter.y],
                c           = self.visible[scatter.colour],
                s           = 3 * np.exp(-self.visible.appMag / 3),
                cmap        = scatter.get('cmap', 'viridis_r'),
                alpha       = 1,
                linewidths  = 0,
            )
            axes.legend([sc], [cparams.name])
            figure.savefig(self.dataset.path('analyses', 'scatters', self.id, f"{scatter.x}-{scatter.y}-{scatter.colour}.png"))
            pyplot.close(figure)
        except KeyError as e:
            log.error(f"Invalid scatter configuration parameter {c.param(e)}") 

    def __str__(self):
        return f"Observation by observer {c.name(self.observer)}"


def initObserve(_queue, _observer, _streaks):
    global queue, observer, streaks
    queue, observer, streaks = _queue, _observer, _streaks

def observe(args):
    filename, out = args

    queue.put(1)
    meteor = Meteor.load(filename)
    sighting = Sighting(observer, meteor)

    if not streaks:
        sighting.reduceToPoint()

    return sighting
