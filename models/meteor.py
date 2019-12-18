import datetime
import logging
import math
import io
import os
import numpy as np
import pickle

import models.frame

from physics import atmosphere, coord, radiometry, constants

#log = logging.getLogger('root')
class L():
    def debug(self, p):
        print(p)
log = L()

EARTH_ROTATION = coord.Vector3D(0, 0, constants.EARTH_ANGULAR_SPEED)


class Meteor:
    def __init__(self, *, mass, density, position, velocity, timestamp, **kwargs):
        self.mass_initial       = mass
        self.mass               = mass
        self.log_mass           = math.log(mass)
        self.density            = density
        self.radius             = (3 * self.mass / (self.density * math.pi * 4))**(1 / 3)

        self.position           = position
        self.velocity           = velocity

        self.timestamp          = timestamp
        self.time               = 0.0

        self.shape_factor       = kwargs.get('shape_factor', 1.21)
        self.heat_transfer      = kwargs.get('heat_transfer', 0.5)
        self.ablation_heat      = kwargs.get('ablation_heat', 8e6)

        self.ablation_const     = 0.5 * self.heat_transfer * self.shape_factor * self.density**(-2/3) / self.ablation_heat

        self.luminous_power     = 0

        self.id                 = self.timestamp.strftime("%Y%m%d-%H%M%S-%f")
        self.frames             = []

        #log.debug(self.__str__())

    @staticmethod
    def load(filename):
        return Meteor.load_pickle(filename)

    @staticmethod
    def load_pickle(filename):
        return pickle.load(io.FileIO(filename, 'rb'))

    def __str__(self):
        return f"<Meteor {self.id} at {self.position:w.3f,.0f}, velocity {self.velocity:c.3f} | " \
            f"{self.density:4.0f} kg/m³, Q {self.ablation_heat:8.0f} J/kg, " \
            f"m {self.mass:8.6e} kg, r {self.radius * 1000:10.3f} mm, {len(self.frames)} frames>"

    def save(self, filename):
        pickle.dump(self, io.FileIO(os.path.join(filename, f"{self.id}x{datetime.datetime.now().strftime('%H%M%S%f')}.pickle"), 'wb'))

    def update_properties(self, diff, dt):
        self.acceleration = diff.dvdt
        self.mass = math.exp(self.log_mass)
        self.mass_change = self.mass * diff.dmdt

    def update_state(self, diff, dt):
        self.position += diff.drdt * dt
        self.velocity += diff.dvdt * dt
        self.log_mass += diff.dmdt * dt

        self.timestamp += datetime.timedelta(seconds = dt)
        self.time += dt


    def check_terminate(self):
        """Check if the simulation of the flight should be terminated"""
        # If all mass has been ablated away, the particle is pronounced dead
        if self.mass < 1e-10:
            log.debug("Burnt to death")
            return True

        # If the particle flew above 400 km, it will likely leave Earth altogether
        #if self.position.elevation() > 400000:
        #    log.debug("Flew away")
        #    break

        # If the velocity is very low, it is a meteorite
        if self.velocity.norm() < 0:
            log.debug(f"Survived with final mass {self.mass:12.6f} kg")
            return True

        # If the elevation is below zero, we have an impact
        if self.position.to_WGS84().alt < 0:
            log.debug("IMPACT")
            return True


    def save_snapshot(self):
        coordinates = self.position.to_WGS84()

        speed = self.velocity.norm()
        self.air_density = atmosphere.air_density(coordinates.alt)
        self.velocity_altaz = self.velocity.dxdydz_to_altaz_at(self.position)
        self.radius = ((3 * self.mass) / (4 * np.pi * self.density))**(1 / 3)

        self.reynolds_number = atmosphere.Reynolds_number(2 * self.radius, speed, self.air_density)
        self.gamma = atmosphere.drag_coefficient_smooth_sphere(self.reynolds_number)
        self.dynamic_pressure = self.air_density * speed**2

        self.luminous_power = -(radiometry.luminous_efficiency(speed) * self.mass_change * speed**2 / 2.0)
        self.absolute_magnitude = radiometry.absolute_magnitude(self.luminous_power)

        self.frames.append(models.frame.Frame(self))

    def print_info(self):
        #p = self.position.to_WGS84()
        #log.debug(f"{p.lon},{p.lat},{p.alt}")
        #return
        log.debug(
            #f"{self.step:4d} | "
            f"{self.time:8.3f} s | "
            f"{self.position:w10.6f,10.3f} | "
            f"{self.velocity_altaz:s10.6f,9.3f} m/s | "
            #f"\u03c1 {self.air_density:9.3e} kg/m³ | "
            f"{self.acceleration.norm():13.3f} m/s², "
            #f"{radiometry.luminous_efficiency(self.velocity.norm()):6.4f} "
            f"{self.reynolds_number:8.0f} | "
            f"\u0393 {self.gamma:8.2f} | "
            #f"Q {self.dynamic_pressure:8.0f} Pa | "
            #f"{self.mass_initial:6.2e} kg, {self.mass:6.2e} kg, {self.mass_change:9.3e} kg/s, "
            f"{self.radius * 1000:7.3f} mm | "
            #f"{self.luminous_power:10.3e} W, "
            #f"{self.absolute_magnitude:6.2f}m"
        )



    def reduce_to_point(self):
        max_light = np.inf

        for frame in self.frames:
            if frame.absolute_magnitude < max_light:
                max_light = frame.absolute_magnitude

        self.frames = [frame]

    def simulate(self):
        self.fly()
        self.save()
