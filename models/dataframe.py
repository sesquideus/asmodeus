import logging
import pandas
import numpy as np

from astropy.time               import Time
from matplotlib                 import pyplot, colors
from matplotlib.ticker          import ScalarFormatter

from models.sighting            import Sighting
from utilities                  import colour as c

log = logging.getLogger('root')


class Dataframe():
    def __init__(self, dataset, observer):
        self.dataset = dataset
        self.observer = observer

    @classmethod
    def load(self, dataset, observer):
        filename = dataset.path('sightings', observer.id, 'sky.tsv')
        log.info(f"Loading a dataframe from {c.path(filename)}")

        dataframe = Dataframe(dataset, observer)
        dataframe.data = pandas.read_csv(filename, sep = '\t', low_memory = False)
        dataframe.expand()
        log.info(f"Created a dataframe with {c.num(len(dataframe.data.index))} rows")

        return dataframe

    @classmethod
    def fromObservation(cls, observation):
        log.info(f"Creating a dataframe from observation (observer {c.name(observation.observer.name)})")
        dataframe = Dataframe(observation.dataset, observation.observer)
        dataframe.data = pandas.DataFrame.from_records(
            [frame.asTuple() for sighting in observation.sightings for frame in sighting.frames],
            columns     = Sighting.columns,
        )
        log.info(f"Dataframe created with {c.num(len(dataframe.data.index))} rows")
        return dataframe

    def expand(self):
        self.data['mjd'] = Time(self.data.timestamp.to_numpy(dtype = 'datetime64[ns]')).mjd
        self.data['massFraction'] = self.data.mass / self.data.massInitial
        self.data['fpkgi'] = self.data.lumPower / self.data.massInitial
        self.data['fpkg'] = self.data.lumPower / self.data.mass

    def save(self):
        filename = self.dataset.path('sightings', self.observer.id, 'sky.tsv')
        log.info(f"Saving a TSV file for observer {c.name(self.observer.name)} {c.path(filename)}")
        self.data.to_csv(filename, sep = '\t', float_format = '%6g')

    def applyBias(self, biasFunction):
        log.info(f"Applying bias DPFs on dataframe for observer {c.name(self.observer.name)}")
        self.data.visible = self.data.apply(biasFunction, axis = 1)
        self.visible = self.data[self.data.visible]
        log.info(f"Bias applied, {c.num(len(self.visible.index))}/{c.num(len(self.data.index))} sightings marked as detected")

    def skipBias(self):
        self.visible = self.data

    def makeScatters(self, settings):
        log.info(f"Creating {c.name('scatter plots')} for observer {c.name(self.observer.name)}, {c.num(len(self.visible.index))} frames to process")
        self.dataset.create('analyses', 'scatters', self.observer.id, exist_ok = True)
    
        for scatter in settings:
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

        try:
            figure, axes = self.emptyFigure()

            axes.tick_params(axis = 'both', which = 'major', labelsize = 12)
            
            try:
                axes.set_xlim(scatter.x.min, scatter.x.max)
            except KeyError as e:
                log.debug("No x range set")

            try:
                axes.set_ylim(scatter.y.min, scatter.y.max)
            except KeyError as e:
                log.debug("No y range set")

            try:
                xlabel = f"{scatter.x.name} [{scatter.x.unit}]"
            except KeyError:
                xlabel = scatter.x.name

            try:
                ylabel = f"{scatter.y.name} [{scatter.y.unit}]"
            except KeyError:
                ylabel = scatter.y.name

            xscale = 'linear'
            try:
                if scatter.x.scale == 'log':
                    xscale = 'log'
            except KeyError:
                pass

            yscale = 'linear'
            try:
                if scatter.y.scale == 'log':
                    yscale = 'log'
            except KeyError:
                pass

            cscale = 'linear'
            norm = None
            try:
                if scatter.colour.scale == 'log':
                    norm = colors.LogNorm(vmin = self.visible[scatter.colour.id].min(), vmax = self.visible[scatter.colour.id].max())
                    cscale = 'log'
            except KeyError:
                norm = None
            
            log.debug(f"x axis: {scatter.x}")
            log.debug(f"y axis: {scatter.y}")
            log.debug(f"colour: {scatter.colour}")

            namex = f"{'log' if xscale == 'log' else ''}{scatter.x.id}"
            namey = f"{'log' if yscale == 'log' else ''}{scatter.y.id}"
            namec = f"{'log' if cscale == 'log' else ''}{scatter.colour.id}"
            filename = f"{namex}-{namey}-{namec}.png"

            log.info(f"Creating a scatter plot for {c.param(scatter.x.id):>24} × {c.param(scatter.y.id):>24} (colour {c.param(scatter.colour.id):>24}), saving as {c.path(filename)}")


            axes.set_xlabel(xlabel, fontdict = {'fontsize': 12})
            axes.set_ylabel(ylabel, fontdict = {'fontsize': 12})
            axes.set_xscale(xscale)
            axes.set_yscale(yscale)
            axes.set_title(f"{self.observer.name} – {scatter.x.name} × {scatter.y.name}", fontdict = {'fontsize': 14})

            sc = axes.scatter(
                self.visible[scatter.x.id],
                self.visible[scatter.y.id],
                c           = self.visible[scatter.colour.id],
                #s           = 30000 / np.log10(self.visible.massInitial)**4,
                s           = 0.5 * np.exp(-self.visible.absMag / 10) * (1 + self.visible.isAbsBrightest * 8),
                cmap        = scatter.get('cmap', 'viridis_r'),
                alpha       = 1,
                linewidths  = 0,
                norm        = norm,
            )

            cb = figure.colorbar(sc, extend = 'max', fraction = 0.1, pad = 0.02)
            try:
                cb.set_label(f"{scatter.colour.name} [{scatter.colour.unit}]")
            except:
                cb.set_label(scatter.colour.name)


            figure.savefig(self.dataset.path('analyses', 'scatters', self.observer.id, filename), dpi = 300)
            pyplot.close(figure)
        except KeyError as e:
            log.error(f"Invalid scatter configuration parameter {c.param(e)}")

    def makeSkyPlot(self):
        log.info(f"Creating {c.name('sky plot')} for observer {c.name(self.observer.name)}, {c.num(len(self.visible.index))} frames to process")
        self.dataset.create('analyses', 'skyplots', self.observer.id, exist_ok = True)

        path = self.dataset.path('analyses', 'skyplots', self.observer.id, 'sky.png')

        azimuths    = np.radians(self.visible.azimuth)
        altitudes   = 90 - self.visible.altitude
        colours     = -self.visible.appMag
        sizes       = 8 * np.exp(-self.visible.appMag / 2)

        figure, axes = pyplot.subplots(subplot_kw = {'projection': 'polar'})

        figure.tight_layout(rect = (0, 0, 1, 1))
        figure.set_size_inches(8, 8)

        axes.xaxis.set_ticks(np.linspace(0, 2 * np.pi, 25))
        axes.yaxis.set_ticklabels([])
        axes.yaxis.set_ticks(np.linspace(0, 90, 7))
        axes.set_ylim(0, 90.5)
        axes.set_facecolor('black')
        axes.grid(linewidth = 0.2, color = 'white')

        axes.scatter(azimuths, altitudes, c = colours, s = sizes, cmap = 'plasma', alpha = 1, linewidths = 0)

        figure.savefig(path, facecolor = 'black', dpi = 300)



    def emptyFigure(self):
        pyplot.rcParams['font.family'] = "Minion Pro"
        pyplot.rcParams['mathtext.fontset'] = "dejavuserif"
        pyplot.rcParams["axes.formatter.useoffset"] = False
        figure, axes = pyplot.subplots()
        figure.tight_layout(rect = (0.07, 0.05, 1, 0.97))
        figure.set_size_inches(8, 5)
        axes.grid(linewidth = 0.2, linestyle = ':')
        axes.xaxis.set_major_formatter(ScalarFormatter(useOffset = False))
        axes.yaxis.set_major_formatter(ScalarFormatter(useOffset = False))

        return figure, axes
