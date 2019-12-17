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

DP_A21 = 1/5

DP_A31 = 3/40
DP_A32 = 9/40

DP_A41 = 44/45
DP_A42 = -56/15
DP_A43 = 32/9

DP_A51 = 19372/6561
DP_A52 = -25360/2187
DP_A53 = 64448/6561
DP_A54 = -212/729

DP_A61 = 9017/3168
DP_A62 = -355/33
DP_A63 = 46732/5247
DP_A64 = 49/176
DP_A65 = -5103/18656

DP_A71 = 35/384
DP_A73 = 500/1113
DP_A74 = 125/192
DP_A75 = -2187/6784
DP_A76 = 11/84

DP_B1 = 5179/57600
DP_B3 = 7571/16695
DP_B4 = 393/640
DP_B5 = -92097/339200
DP_B6 = 187/2100
DP_B7 = 1/40




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

    def fly_adaptive(self, fps, *, method='DP', wgs84=True, min_spf=1, max_spf=10000, error_coarser=1e-6, error_finer=1e-3):
        integrator = self.select_integrator_adaptive()
        spf = min_spf
        if spf > max_spf:
            spf = max_spf
        clock = 0
        self.step = 0
        last_change = 0

        while True:
            dt = 1.0 / (fps * spf)
            self.step += 1
            error, diff = integrator(State(self.position, self.velocity, self.log_mass), dt)
            #print(f"t = {self.time:12.6f} s, error = {error:.6f}, {clock}/{spf}")

            if error < error_coarser and spf > min_spf:
                log.debug(f"Step unnecessarily small (error = {error:.6f}), {clock}/{spf}")
                if clock % 2 == 0:
                    spf //= 2
                    clock //= 2
                    log.debug(f"Decreasing to {spf} steps per frame at clock {clock}")
                    last_change = +1
                    continue
                else:
                    log.debug("Waiting another step")
                    pass

            if error > error_finer and spf < max_spf and last_change != 1:
                spf *= 2
                clock *= 2
                log.debug(f"Step too long (error = {error:.6f}), increasing to {spf} steps per frame at clock {clock}")
                last_change = -1
                continue

            last_change = 0

            if clock % spf == 0:
                self.save_snapshot(diff, wgs84=wgs84)
                self.print_info(spf)
                clock = 0

            self.position += diff.drdt * dt
            self.velocity += diff.dvdt * dt
            self.log_mass += diff.dmdt * dt

            # Advance time by dt
            self.timestamp += datetime.timedelta(seconds = dt)
            self.time += dt
            clock += 1

            if self.check_terminate():
                break

        log.debug(f"Meteor generated ({len(self.frames)} frames)")

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
            f"{self.mass_initial:6.2e} kg, {self.mass:6.2e} kg, {self.mass_change:9.3e} kg/s, "
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
