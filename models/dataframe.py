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
    def from_observation(cls, observation):
        log.info(f"Creating a dataframe from observation (observer {c.name(observation.observer.name)})")
        dataframe = Dataframe(observation.dataset, observation.observer)
        dataframe.data = pandas.DataFrame.from_records(
            [frame.as_tuple() for sighting in observation.sightings for frame in sighting.frames],
            columns     = Sighting.columns,
        )
        log.info(f"Dataframe created with {c.num(len(dataframe.data.index))} rows")
        return dataframe

    def expand(self):
        self.data['mjd'] = Time(self.data.timestamp.to_numpy(dtype = 'datetime64[ns]')).mjd
        self.data['mass_fraction'] = self.data.mass / self.data.mass_initial
        self.data['fpkgi'] = self.data.luminous_power / self.data.mass_initial
        self.data['fpkg'] = self.data.luminous_power / self.data.mass

    def save(self):
        filename = self.dataset.path('sightings', self.observer.id, 'sky.tsv')
        self.data.to_csv(filename, sep = '\t', float_format = '%6g')

        log.info(f"Saved a TSV file for observer {c.name(self.observer.name)} {c.path(filename)}")

    def apply_bias(self, bias_function):
        log.info(f"Applying bias DPFs on dataframe for observer {c.name(self.observer.name)}")

        self.data['visible'] = self.data.apply(bias_function, axis = 1)
        self.visible = self.data[(self.data.visible) & (self.data.altitude > self.observer.horizon)]

        log.info(f"Bias applied, {c.num(len(self.visible.index))}/{c.num(len(self.data.index))} sightings marked as detected")

    def skip_bias(self):
        self.visible = self.data#[self.data.altitude > self.observer.horizon]

    def make_scatters(self, settings):
        log.info(f"Creating {c.name('scatter plots')} for observer {c.name(self.observer.name)}, {c.num(len(self.visible.index))} frames to process")

        self.dataset.create('analyses', 'scatters', self.observer.id, exist_ok = True)

        for scatter in settings:
            self.cross_scatter(scatter)

    def cross_scatter(self, scatter):
        """
            Render a cross-scatter plot of four variables using a scatter dotmap
            scatter: dotmap in shape
            -   x:          <property to plot on x axis>
                y:          <property to plot on y axis>
                colour:     <property to use for colouring the dots>
                size:       <property to determine dot size>
        """

        try:
            figure, axes = self.empty_figure()

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

            norm = None
            try:
                if scatter.colour.scale == 'log':
                    norm = colors.LogNorm(vmin = self.visible[scatter.colour.id].min(), vmax = self.visible[scatter.colour.id].max())
            except KeyError:
                norm = None

            filename = f"{scatter.x.id}-{scatter.y.id}-{scatter.colour.id}.png"
            log.info(f"Creating a scatter plot for {c.param(scatter.x.id):>24} × {c.param(scatter.y.id):>24} "
                f"(colour {c.param(scatter.colour.id):>24}), "
                f"saving as {c.path(filename)}")

            axes.set_xlabel(xlabel, fontdict = {'fontsize': 12})
            axes.set_ylabel(ylabel, fontdict = {'fontsize': 12})
            axes.set_xscale(xscale)
            axes.set_yscale(yscale)
            axes.set_title(f"{self.observer.name} – {scatter.x.name} × {scatter.y.name}", fontdict = {'fontsize': 14})

            sc = axes.scatter(
                self.visible[scatter.x.id],
                self.visible[scatter.y.id],
                c           = self.visible[scatter.colour.id],
                #s           = 30000 / np.log10(self.visible.mass_initial)**4,
                s           = 0.5 * np.exp(-self.visible.absolute_magnitude / 10) * (1 + self.visible.is_abs_brightest * 8),
                cmap        = scatter.get('cmap', 'viridis_r'),
                alpha       = 1,
                linewidths  = 0,
                norm        = norm,
            )

            cb = figure.colorbar(sc, extend = 'max', fraction = 0.1, pad = 0.02)
            try:
                cb.set_label(f"{scatter.colour.name} [{scatter.colour.unit}]")
            except KeyError:
                cb.set_label(scatter.colour.name)

            figure.savefig(self.dataset.path('analyses', 'scatters', self.observer.id, filename), dpi = 300)
            pyplot.close(figure)
        except KeyError as e:
            log.error(f"Invalid scatter configuration parameter {c.param(e)}")

    def make_sky_plot(self, *, dark = True):
        log.info(f"Creating {c.name('sky plot')} for observer {c.name(self.observer.name)}, {c.num(len(self.visible.index))} frames to process")

        if dark:
            background, line_colour = 'black', 'white'
        else:
            background, line_colour = 'white', 'grey'

        self.dataset.create('analyses', 'skyplots', self.observer.id, exist_ok = True)

        pyplot.rcParams['font.family'] = "Minion Pro"
        pyplot.rcParams['mathtext.fontset'] = "dejavuserif"

        path = self.dataset.path('analyses', 'skyplots', self.observer.id, 'sky.png')

        size_formatter = lambda x: 20 * np.exp(-x / 2)

        azimuths    = np.radians(90 + self.visible.azimuth)
        altitudes   = 90 - self.visible.altitude
        colours     = self.visible.angular_speed
        sizes       = size_formatter(self.visible.apparent_magnitude)

        figure, axes = pyplot.subplots(subplot_kw = {'projection': 'polar'})

        figure.tight_layout(rect = (0.0, 0.0, 1.0, 1.0))
        figure.set_size_inches(9, 8)

        axes.tick_params(axis='x', which='major', labelsize=20)
        axes.tick_params(axis='x', which='minor', labelsize=0)
        axes.xaxis.set_ticks([0, np.pi / 2.0, np.pi, np.pi * 3 / 2.0])
        axes.xaxis.set_ticks(np.linspace(0, 2 * np.pi, 25), minor=True)
        axes.xaxis.set_ticklabels(['W', 'N', 'E', 'S'])
        axes.yaxis.set_ticklabels([])
        axes.yaxis.set_ticks(np.linspace(0, 90, 7))
        axes.set_ylim(0, 90)
        axes.set_facecolor(background)
        axes.grid(linewidth = 0.2, color = line_colour)

        scatter = axes.scatter(azimuths, altitudes, c = colours, s = sizes, cmap = 'viridis', alpha = 1, linewidths = 0)

        cb = figure.colorbar(scatter, extend = 'max', fraction = 0.1, pad = 0.06)
        cb.set_label(f"angular speed [°/s]", fontsize=16)
        cb.ax.tick_params(labelsize=15)

        for magnitude in [-6, -3, 0, 3, 6]:
            sign = '+' if magnitude >= 0 else '\u2212'
            axes.scatter([], [], c='k', alpha=0.6, s=size_formatter(magnitude), label=f'{sign}{abs(magnitude)}$^\\mathrm{{m}}$')
        axes.legend(scatterpoints=1, frameon=False, labelspacing=0.8, title='Apparent magnitude', loc=(-0.06, 0.8))
        
        print("f")

        figure.savefig(path, facecolor = background, dpi = 300)

    def empty_figure(self):
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
