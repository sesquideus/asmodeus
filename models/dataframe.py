import logging
import pandas
import numpy as np

from astropy.time               import Time
from matplotlib                 import pyplot
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
        dataframe.data = pandas.read_csv(filename, sep = '\t')
        dataframe.expand()
        log.info(f"Created a dataframe with {c.num(len(dataframe.data.index))} rows")
        return dataframe

    @classmethod
    def fromObservation(cls, observation):
        log.info(f"Creating a dataframe from observation")
        dataframe = Dataframe(observation.dataset, observation.observer)
        dataframe.data = pandas.DataFrame.from_records(
            [frame.asTuple() for sighting in observation.sightings for frame in sighting.frames],
            columns     = Sighting.columns,
        )
        log.info(f"Dataframe created with {c.num(len(dataframe.data.index))} rows")
        return dataframe

    def expand(self):
        self.data['mjd'] = Time(self.data.timestamp.to_numpy(dtype = 'datetime64[ns]')).mjd
        self.data['logInitMass'] = np.log10(self.data.initMass.to_numpy(dtype = 'float'))

    def save(self):
        filename = self.dataset.path('sightings', self.observer.id, 'sky.tsv')
        log.info(f"Saving a TSV file for observer {c.name(self.observer.id)} {c.path(filename)}")
        self.data.to_csv(filename, sep = '\t', float_format = '%6g')

    def applyBias(self, biasFunction):
        log.info(f"Applying bias DPFs")
        self.data['visible'] = self.data.apply(biasFunction, axis = 1)
        self.visible = self.data[self.data.visible]
        log.info(f"Bias applied, {c.num(len(self.visible.index))}/{c.num(len(self.data.index))} sightings marked as detected")

    def makeScatters(self):
        log.info(f"Creating {c.name('scatter plots')} for observer {c.name(self.observer.name)}, {c.num(len(self.visible.index))} frames to process")
        self.dataset.create('analyses', 'scatters', self.observer.id, exist_ok = True)

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
            axes.set_title(f"{self.observer.name} – {xparams.name} × {yparams.name}", fontdict = {'fontsize': 14})

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
            figure.savefig(self.dataset.path('analyses', 'scatters', self.observer.id, f"{scatter.x}-{scatter.y}-{scatter.colour}.png"), dpi = 300)
            pyplot.close(figure)
        except KeyError as e:
            log.error(f"Invalid scatter configuration parameter {c.param(e)}")

    def emptyFigure(self):
        pyplot.rcParams['font.family'] = "Minion Pro"
        pyplot.rcParams['mathtext.fontset'] = "dejavuserif"
        figure, axes = pyplot.subplots()
        figure.tight_layout(rect = (0.07, 0.05, 1, 0.97))
        figure.set_size_inches(8, 5)
        axes.grid(linewidth = 0.2, linestyle = ':')
        axes.xaxis.set_major_formatter(ScalarFormatter(useOffset = False))
        axes.yaxis.set_major_formatter(ScalarFormatter(useOffset = False))

        return figure, axes
