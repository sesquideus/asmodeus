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
from models.sighting    import Sighting
from models.dataframe   import Dataframe
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
        log.info(f"{c.num(self.population.count)} observations were calculated")

    def save(self):
        directory = self.dataset.create('sightings', self.observer.id)
        self.asDataframe().save()
        #log.debug(f"""Saving the observed population as {c.over(f"{'streaks' if self.config.streaks else 'points'}")} to {c.path(self.dataset.name)}""")

        #for sighting in self.sightings:
        #sighting.save(directory, streak = self.config.streaks)
        
    def asDataframe(self):
        return Dataframe.fromObservation(self)

    def saveMetadata(self, directory):
        pass
        
    def asDict(self):
        return {
            'observer':     self.observer.id,
        }




    def makeKDEs(self):
        log.info(f"Creating KDEs for observer {c.name(self.id)}, {c.num(len(self.visible.index))} sightings to process")
        self.dataset.create('analyses', 'kdes', self.id, exist_ok = True)

        for stat, params in self.settings.kdes.quantities.items():       
            self.makeKDE(stat, **params)

   
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
