import math
import logging
import copy
import pickle
import dotmap

from physics import atmosphere, radiometry

log = logging.getLogger('root')


class SightingFrame():
    def __init__(self, observer, frame):
        self.observer           = observer
        self.frame              = copy.copy(frame)

        self.alt_az             = observer.alt_az(frame.position)
        self.relative_position  = self.frame.position - self.observer.position

        dot                     = self.relative_position * self.frame.velocity
        projection              = dot / (self.relative_position.norm() ** 2) * self.relative_position
        rejection               = self.frame.velocity - projection
        self.angular_speed      = math.degrees(rejection.norm() / self.relative_position.norm())

        air_mass                = atmosphere.air_mass(self.alt_az.to_spherical().lat, self.observer.position.to_WGS84().alt)
        attenuated_power        = atmosphere.attenuate(self.frame.luminous_power, air_mass)
        self.flux_density       = radiometry.flux_density(attenuated_power, self.alt_az.norm())

        self.apparent_magnitude = radiometry.apparent_magnitude(self.flux_density)
        self.absolute_magnitude = self.frame.absolute_magnitude

        self.is_brightest       = 0
        self.is_abs_brightest   = 0

    def __str__(self):
        return "{timestamp} | {truePos}, \
            {true_speed:7.0f} m/s | {alt_az}, \
            {angular_speed:6.3f}°/s | {mass:6.4e} kg, \
            {flux_density:8.3e} W/m2, {magnitude:6.2f} m".format(
            timestamp           = self.frame.timestamp.strftime("%Y-%m-%dT%H:%M:%S:%f"),
            mass                = self.frame.mass,
            angular_speed       = self.angular_speed,
            flux_density        = self.flux_density,
            magnitude           = self.apparent_magnitude,
            alt_az              = self.alt_az.str_spherical(),
            true_position       = self.frame.position.str_geodetic(),
            true_speed          = self.frame.velocity.norm(),
        )

    def as_tuple(self):
        relative_position = self.alt_az.to_spherical()
        return (
            self.frame.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            self.frame.time,
            relative_position.lat,
            relative_position.lon,
            relative_position.alt,
            self.frame.position.elevation_WGS84(),
            self.frame.velocity_altaz.to_spherical().lat,
            self.frame.speed,
            self.angular_speed,
            self.frame.mass_initial,
            self.frame.mass,
            self.frame.density,
            self.frame.ablation_heat,
            self.frame.luminous_power,
            self.flux_density,
            self.apparent_magnitude,
            self.absolute_magnitude,
            self.is_brightest,
            self.is_abs_brightest,
        )

    def save(self):
        return pickle.dumps(self)
