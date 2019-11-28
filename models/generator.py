import logging
import random
import dotmap
import numbers
import datetime
import numpy as np
import pandas

from core               import exceptions
from distribution       import PositionDistribution, VelocityDistribution, MassDistribution, \
    DensityDistribution, TimeDistribution, DragCoefficientDistribution
from models             import Meteor
from physics            import coord
from utilities          import colour as c, utilities

log = logging.getLogger('root')


class Generator():
    @classmethod
    def from_config(cls, config):
        config._dynamic = False
        return {
            'grid':     GeneratorGrid,
            'random':   GeneratorRandom,
        }[config.method](config.parameters)


class GeneratorGrid(Generator):
    method = 'grid'

    def __init__(self, parameters):
        self.parameters = parameters

    def get_space_range(self, *, min, max, count, spacing = 'linear', time = False):
        space = {
            'linear':   np.linspace,
            'log':      np.geomspace,
        }[spacing]

        if isinstance(min, datetime.datetime):
            return pandas.date_range(min, max, count).to_pydatetime()
        else:
            return space(min, max, count, dtype = float)

    def get_space(self, definition):
        try:
            if isinstance(definition, dotmap.DotMap):
                return self.get_space_range(**definition.toDict())
            elif isinstance(definition, numbers.Number) or isinstance(definition, datetime.datetime):
                return [definition]
            else:
                raise exceptions.ConfigurationError(
                    f"Parameter space definition must be either a number or a dictionary with min, max and count defined"
                )
        except TypeError as e:
            raise exceptions.ConfigurationError(e)

    def generate(self):
        self.meteors = []
        space = utilities.dict_product(
            mass                = self.get_space(self.parameters.mass),

            density             = self.get_space(self.parameters.material.density),
            heat_transfer       = self.get_space(self.parameters.material.heat_transfer),
            ablation_heat       = self.get_space(self.parameters.material.ablation_heat),

            drag_coefficient    = self.get_space(self.parameters.shape.drag_coefficient),
            shape_factor        = self.get_space(self.parameters.shape.shape_factor),

            latitude            = self.get_space(self.parameters.position.latitude),
            longitude           = self.get_space(self.parameters.position.longitude),
            elevation           = self.get_space(self.parameters.position.elevation),

            ra                  = self.get_space(self.parameters.velocity.ra),
            dec                 = self.get_space(self.parameters.velocity.dec),
            speed               = self.get_space(self.parameters.velocity.speed),

            time                = self.get_space(self.parameters.time),
        )

        for raw in space:
            velocity_equatorial = VelocityDistribution.shower(ra = raw['ra'], dec = raw['dec'], speed = raw['speed'])()
            velocity = coord.Vector3D.from_numpy_vector(
                (coord.rot_matrix_z(coord.earth_rotation_angle(raw['time'])) @ velocity_equatorial.as_numpy_vector())
            )

            self.meteors.append(Meteor(
                mass            = raw['mass'],
                density         = raw['density'],
                timestamp       = raw['time'],
                position        = coord.Vector3D.from_geodetic(raw['latitude'], raw['longitude'], raw['elevation']),
                drag_coefficient= raw['drag_coefficient'],
                velocity        = velocity,
                ablation_heat   = raw['ablation_heat'],
            ))

        self.count = len(self.meteors)
        self.iterations = None

        return self.meteors

    def as_dict(self):
        return {
            'method':           self.method,
            'count':            self.count,
            'iterations':       None,
            'parameters':       self.parameters.toDict(),
        }


class GeneratorRandom(Generator):
    method  = 'random'

    def __init__(self, parameters):
        self.parameters = parameters

        self.mass_distribution              = MassDistribution.from_config(self.parameters.mass).log_info()
        self.position_distribution          = PositionDistribution.from_config(self.parameters.position).log_info()
        self.velocity_distribution          = VelocityDistribution.from_config(self.parameters.velocity).log_info()
        self.density_distribution           = DensityDistribution.from_config(self.parameters.material.density).log_info()
        self.temporal_distribution          = TimeDistribution.from_config(self.parameters.time).log_info()
        self.drag_coefficient_distribution  = DragCoefficientDistribution.from_config(self.parameters.shape.drag_coefficient).log_info()

    def generate_one(self):
        mass                    = self.mass_distribution.sample()
        density                 = self.density_distribution.sample()
        timestamp               = self.temporal_distribution.sample()
        position                = self.position_distribution.sample()
        drag_coefficient        = self.drag_coefficient_distribution.sample()
        velocity_equatorial     = self.velocity_distribution.sample()

        velocity_ECEF           = coord.Vector3D.from_numpy_vector(
            (coord.rot_matrix_z(coord.earth_rotation_angle(timestamp)) @ velocity_equatorial.as_numpy_vector())
        )
        entry_angle_sin         = -position * velocity_ECEF / (position.norm() * velocity_ECEF.norm())

        self.iterations += 1
        if entry_angle_sin > random.random():
            self.meteors.append(Meteor(
                mass                = mass,
                density             = density,
                timestamp           = timestamp,
                velocity            = velocity_ECEF,
                position            = position,
                ablation_heat       = self.parameters.material.ablation_heat,
                heat_transfer       = self.parameters.material.heat_transfer,
                drag_coefficient    = drag_coefficient,
            ))
            self.count += 1

    def generate(self):
        log.info(f"Generating {c.num(self.parameters.count)} meteoroids")
        self.count = 0
        self.iterations = 0
        self.meteors = []

        while (self.count < self.parameters.count):
            self.generate_one()

        log.info("Needed {iterations} candidate{s}, effective area {area}".format(
            iterations      = c.num(self.iterations),
            area            = c.num(f"{self.parameters.count / self.iterations * 100:5.2f}%"),
            s               = 's' if self.iterations > 1 else '',
        ))

        return self.meteors

    def as_dict(self):
        return {
            'method': self.method,
            'count': self.count,
            'iterations': self.iterations,
            'parameters': {
                'mass': self.mass_distribution.as_dict(),
                'time': self.temporal_distribution.as_dict(),
                'position': self.position_distribution.as_dict(),
                'velocity': self.velocity_distribution.as_dict(),
                'material': {
                    'density': self.density_distribution.as_dict(),
                },
                'shape': {
                    'drag_coefficient': self.drag_coefficient_distribution.as_dict(),
                },
            },
        }
