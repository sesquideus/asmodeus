import logging
import os
import numpy as np

from physics                    import coord
from models.sighting            import Sighting
from utilities                  import colour as c

log = logging.getLogger('root')


class Observer():
    def __init__(self, id, parameters):
        self.id                 = id
        self.name               = parameters.name
        self.position           = coord.Vector3D.from_WGS84(parameters.latitude, parameters.longitude, parameters.altitude)
        try:
            self.horizon        = parameters.horizon
        except KeyError:
            self.horizon        = 0

        self.rotation_matrix = self.position.rotation_matrix()

    def alt_az(self, point: coord.Vector3D) -> coord.Vector3D:
        """
            Compute AltAz coordinates of a point in ECEF frame as observed by this observer
        """
        return coord.Vector3D.from_numpy_vector(self.rotation_matrix @ (point - self.position).as_numpy_vector())

    def __str__(self):
        return f"{c.name(self.name)} ({c.name(self.id)}) at {self.position.str_WGS84()}"

    def as_dict(self):
        pos = self.position.to_WGS84()
        return {
            'name':         self.name,
            'latitude':     pos.lat,
            'longitude':    pos.lon,
            'altitude':     pos.alt, 
            'horizon':      self.horizon,
        }

    def load_sightings(self):
        log.info(f"Loading sightings from {c.path(self.dataset.path('sightings'))}")

        dicts = {}
        for sf in sorted(os.listdir(self.dataset.path('sightings', self.id))):
            sighting = Sighting.load(self.dataset.path('sightings', self.id, sf))
            dicts[sighting.id] = sighting.as_dict()

        log.info(f"Loaded {c.num(len(dicts))} sightings")
        self.create_dataframe()


    """
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
    """
