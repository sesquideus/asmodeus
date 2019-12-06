import datetime
import logging
import math
import io
import os
import numpy as np
import pickle

import models.frame

from physics import atmosphere, coord, radiometry, constants

log = logging.getLogger('root')
EARTH_ROTATION = coord.Vector3D(0, 0, constants.EARTH_ANGULAR_SPEED)


class State:
    def __init__(self, position, velocity, mass):
        self.position = position
        self.velocity = velocity
        self.mass = mass

    def __str__(self):
        return f"{self.position} {self.velocity} {self.mass}"


class Diff:
    def __init__(self, drdt, dvdt, dmdt):
        self.drdt = drdt
        self.dvdt = dvdt
        self.dmdt = dmdt

    ### Diff arithmetics
    def __add__(self, other):
        return Diff(
            self.drdt + other.drdt,
            self.dvdt + other.dvdt,
            self.dmdt + other.dmdt,
        )

    def __sub__(self, other):
        return Diff(
            self.drdt - other.drdt,
            self.dvdt - other.dvdt,
            self.dmdt - other.dmdt,
        )

    def __mul__(self, number):
        return Diff(
            number * self.drdt,
            number * self.dvdt,
            number * self.dmdt,
        )

    __rmul__ = __mul__

    def __truediv__(self, number):
        return Diff(
            self.drdt / number,
            self.dvdt / number,
            self.dmdt / number,
        )

    ### Class methods
    @classmethod
    def zero(cls):
        return Diff(coord.Vector3D(0, 0, 0), coord.Vector3D(0, 0, 0), 0)

    ### Representations
    def __str__(self):
        return f"{self.drdt} {self.dvdt} {self.dmdt}"

    ### Logic
    def norm(self):
        return self.drdt.norm(), self.dvdt.norm(), self.dmdt**2

class Meteor:
    def __init__(self, *, mass, density, position, velocity, timestamp, **kwargs):
        self.mass               = mass
        self.density            = density
        self.radius             = (3 * self.mass / (self.density * math.pi * 4))**(1 / 3)

        self.position           = position
        self.velocity           = velocity

        self.timestamp          = timestamp
        self.time               = 0.0

        self.shape_factor       = kwargs.get('shape_factor', 1.21)
        self.heat_transfer      = kwargs.get('heat_transfer', 0.5)
        self.ablation_heat      = kwargs.get('ablation_heat', 8e6)

        self.luminous_power     = 0

        self.id                 = self.timestamp.strftime("%Y%m%d-%H%M%S-%f")
        self.frames             = []
        self.mass_initial       = self.mass

        log.debug(self.__str__())

    @staticmethod
    def load(filename):
        return Meteor.load_pickle(filename)

    @staticmethod
    def load_pickle(filename):
        return pickle.load(io.FileIO(filename, 'rb'))

    def __str__(self):
        return f"<Meteor {self.id} at {self.position}, velocity {self.velocity} | " \
            f"{self.density:4.0f} kg/m³, Q {self.ablation_heat:8.0f} J/kg, " \
            f"m {self.mass:8.6e} kg, r {self.radius * 1000:10.3f} mm, {len(self.frames)} frames>"

    def save(self, filename):
        pickle.dump(self, io.FileIO(os.path.join(filename, f"{self.id}x{datetime.datetime.now().strftime('%H%M%S%f')}.pickle"), 'wb'))

    def evaluate(self, state, diff, dt):
        new_state = State(
            state.position + diff.drdt * dt,
            state.velocity + diff.dvdt * dt,
            max(state.mass + diff.dmdt * dt, 1e-10)
        )
        coordinates = new_state.position.to_WGS84()
        air_density = atmosphere.air_density(coordinates.alt)
        speed = new_state.velocity.norm()
        reynolds = atmosphere.Reynolds_number(self.radius, new_state.velocity.norm(), air_density / constants.AIR_VISCOSITY)
        gamma = atmosphere.drag_coefficient_smooth_sphere(reynolds)

        drag_vector = -(gamma * self.shape_factor * air_density * speed / (new_state.mass**(1 / 3) * self.density**(2 / 3))) * new_state.velocity
        gravity_vector = -constants.GRAVITATIONAL_CONSTANT * constants.EARTH_MASS / new_state.position.norm()**3 * new_state.position
        coriolis_vector = -2 * EARTH_ROTATION ^ new_state.velocity
        huygens_vector = -EARTH_ROTATION ^ (EARTH_ROTATION ^ new_state.position)

        return Diff(
            new_state.velocity,
            drag_vector + gravity_vector + coriolis_vector + huygens_vector,
            0#-(self.heat_transfer * self.shape_factor * air_density * speed**3 * (new_state.mass / self.density)**(2 / 3) / (2 * self.ablation_heat)),
        )

    def step_euler(self, state, dt):
        return self.evaluate(state, Diff.zero(), dt)

    def step_RK4(self, state, dt):
        d1 = self.evaluate(state, Diff.zero(), dt)
        d2 = self.evaluate(state, d1 * 0.5, dt)
        d3 = self.evaluate(state, d2 * 0.5, dt)
        d4 = self.evaluate(state, d3, dt)
        return (d1 + 2 * d2 + 2 * d3 + d4) / 6

    def step_DP_constant(self, state, dt):
        d0 = Diff.zero()
        d1 = self.evaluate(state, d0, dt)
        d2 = self.evaluate(state, d1 * 0.2, dt)
        d3 = self.evaluate(state, sum([dx * x for (dx, x) in zip([d1, d2], [3/40, 9/40])], d0), dt)
        d4 = self.evaluate(state, sum([dx * x for (dx, x) in zip([d1, d2, d3], [44/45, -56/15, 32/9])], d0), dt)
        d5 = self.evaluate(state, sum([dx * x for (dx, x) in zip([d1, d2, d3, d4], [19372/6561, -25360/2187, 64448/6561, -212/729])], d0), dt)
        d6 = self.evaluate(state, sum([dx * x for (dx, x) in zip([d1, d2, d3, d4, d5], [9017/3168, -355/33, 46732/5247, 49/176, -5103/18656])], d0), dt)
        return d1 * 35/384 + d3 * 500/1113 + d4 * 125/192 - d5 * 2187/6784 + d6 * 11/84

    def step_DP_adaptive(self, state, dt):
        d0 = Diff.zero()
        d1 = self.evaluate(state, d0, dt)
        d2 = self.evaluate(state, d1 * 0.2, dt)
        d3 = self.evaluate(state, sum([dx * x for (dx, x) in zip([d1, d2], [3/40, 9/40])], d0), dt)
        d4 = self.evaluate(state, sum([dx * x for (dx, x) in zip([d1, d2, d3], [44/45, -56/15, 32/9])], d0), dt)
        d5 = self.evaluate(state, sum([dx * x for (dx, x) in zip([d1, d2, d3, d4], [19372/6561, -25360/2187, 64448/6561, -212/729])], d0), dt)
        d6 = self.evaluate(state, sum([dx * x for (dx, x) in zip([d1, d2, d3, d4, d5], [9017/3168, -355/33, 46732/5247, 49/176, -5103/18656])], d0), dt)
        solution = (d1 * 35/384 + d3 * 500/1113 + d4 * 125/192 - d5 * 2187/6784 + d6 * 11/84)
        d7 = self.evaluate(state, solution, dt)
        alternative = (d1 * 5179/57600 + d3 * 7571/16695 + d4 * 393/640 - d5 * 92097/339200 + d6 * 187/2100 + d7 * 1/40)
        error_estimate = solution - alternative

        error_velocity = error_estimate.dvdt.norm() / state.velocity.norm()
        error_mass = abs(error_estimate.dmdt / state.mass)

        return max(error_velocity, error_mass), solution

    def select_integrator_constant(self, method='euler'):
        print(f"Selected constant-step integrator {method}")
        return {
            'euler': self.step_euler,
            'RK4': self.step_RK4,
            'DP': self.step_DP_constant,
        }.get(method, self.step_euler)

    def select_integrator_adaptive(self, method='DP'):
        print(f"Selected adaptive-step integrator {method}")
        return {
            'DP': self.step_DP_adaptive,
        }.get(method, self.step_euler)

    def fly_constant(self, fps, spf, *, method='euler', wgs84=True):
        integrator = self.select_integrator_constant(method)
        dt = 1.0 / (fps * spf)
        clock = 0

        while True:
            state = integrator(State(self.position, self.velocity, self.mass), dt)

            if clock % spf == 0:
                self.save_snapshot(state, wgs84=wgs84)
                self.print_info(spf)
            clock += 1

            self.position += state.drdt * dt
            self.velocity += state.dvdt * dt
            self.mass     += state.dmdt * dt

            # Advance time by dt
            self.timestamp += datetime.timedelta(seconds = dt)
            self.time += dt

            if self.check_terminate():
                break


    def fly_adaptive(self, fps, spf, *, method='DP', wgs84=True, min_spf=1, max_spf=10000, error_coarser=1e-6, error_finer=1e-3):
        integrator = self.select_integrator_adaptive()
        if spf < min_spf:
            spf = min_spf
        if spf > max_spf:
            spf = max_spf
        clock = 0

        while True:
            dt = 1.0 / (fps * spf)
            error, state = integrator(State(self.position, self.velocity, self.mass), dt)
            print(f"t = {self.time:12.6f} s, error = {error:.6f}, {clock}/{spf}")

            if error < error_coarser and spf > min_spf:
                print(f"Step unnecessarily big (error = {error:.6f}), {clock}/{spf}")
                if clock == 0 or clock % 2 == 0:
                    spf //= 2
                    clock //= 2
                    print(f"Decreasing to {spf} steps per frame at clock {clock}")
                    continue
                else:
                    print("Waiting another step")

            if error > error_finer and spf < max_spf:
                spf *= 2
                clock *= 2
                print(f"Step too small (error = {error:.6f}), increasing to {spf} steps per frame at clock {clock}")
                dt = 1.0 / (fps * spf)
                continue

            if (clock % spf == 0):
                self.save_snapshot(state, wgs84=wgs84)
                self.print_info(spf)
                clock = 0

            self.position += state.drdt * dt
            self.velocity += state.dvdt * dt
            self.mass     += state.dmdt * dt

            # Advance time by dt
            self.timestamp += datetime.timedelta(seconds = dt)
            self.time += dt
            clock += 1

            if self.check_terminate():
                break

        log.debug(f"Meteor generated ({len(self.frames)} frames)")

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
        if self.velocity.norm() < 1:
            log.debug(f"Survived with final mass {self.mass:12.6f} kg")
            return True

        # If the elevation is below zero, we have an impact
        if self.position.to_WGS84().alt < 0:
            log.debug("IMPACT")
            return True


    def save_snapshot(self, state, *, wgs84):
        coordinates = self.position.to_WGS84() if wgs84 else self.position.to_spherical()

        speed = self.velocity.norm()
        self.air_density = atmosphere.air_density(coordinates.alt)
        self.velocity_altaz = self.velocity.dxdydz_to_altaz_at(self.position)
        self.radius = ((3 * self.mass) / (4 * np.pi * self.density))**(1 / 3)

        self.reynolds_number = atmosphere.Reynolds_number(2 * self.radius, speed, self.air_density)
        self.gamma = atmosphere.drag_coefficient_smooth_sphere(self.reynolds_number)
        self.acceleration = state.dvdt.norm()
        self.mass_change = state.dmdt

        self.luminous_power = -(radiometry.luminous_efficiency(speed) * state.dmdt * speed**2 / 2.0)
        self.absolute_magnitude = radiometry.absolute_magnitude(self.luminous_power)

        self.frames.append(models.frame.Frame(self))

    def print_info(self, spf):
        #print(f"{self.position:g8.6f,6.0f}")
        #return
        print(
            f"{self.time:8.3f} s | "
            f"{self.position:w10.6f,10.3f} | "
            f"{self.velocity_altaz:s10.6f,9.3f} m/s | "
            f"\u03c1 {self.air_density:9.3e} kg/m³ | "
            f"{self.acceleration:13.3f} m/s², "
            #f"{radiometry.luminous_efficiency(self.velocity.norm()):6.4f} "
            f"{self.reynolds_number:8.0f} | "
            f"\u0393 {self.gamma:6.2f} | "
            #f"{self.mass_initial:6.2e} kg, {self.mass:6.2e} kg, {self.mass_change:9.3e} kg/s, "
            f"{self.radius * 1000:7.3f} mm | "
            #f"{self.luminous_power:10.3e} W, "
            f"{self.absolute_magnitude:6.2f}m"
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
