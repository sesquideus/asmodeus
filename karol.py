#!/usr/bin/env python3

import numpy as np
import pandas

from matplotlib import pyplot

from physics import atmosphere, coord, constants

def get_wind(vector):
    return coord.Vector3D(0, 0, 0)

GRAVITY_VECTOR = coord.Vector3D(0, 0, -constants.EARTH_GRAVITY)


class State():
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity

    def __str__(self):
        return f"State {self.position}, {self.velocity}"


class Meteorite():
    columns = ('time', 'x', 'y', 'z', 'vx', 'vy', 'vz', 'wx', 'wy', 'wz', 're', 'gamma')

    def __init__(self, mass, radius, shape_factor, position, velocity):
        self.mass = mass
        self.radius = radius
        self.area = 4 * self.radius**2 * shape_factor
        self.position = position
        self.velocity = velocity

    def step(self, state, diff, dt, node):
        new_position = state.position + diff.position * dt * node
        new_velocity = state.velocity + diff.velocity * dt * node

        air_density = atmosphere.air_density(new_position.z)
        speed = new_velocity.norm()
        wind = get_wind(new_position)
        reynolds = atmosphere.Reynolds_number(self.radius, new_velocity.norm(), air_density / constants.AIR_VISCOSITY)
        gamma = atmosphere.drag_coefficient_smooth_sphere(reynolds)

        air_velocity = new_velocity - wind
        air_speed_squared = air_velocity * air_velocity

        force = -gamma * air_density * (self.area / self.mass) * air_speed_squared * new_velocity.unit() + GRAVITY_VECTOR

        return State(
            new_velocity,
            force,
        )

    def next_euler(self, state, dt):
        d1 = self.step(state, State(coord.Vector3D(0, 0, 0), coord.Vector3D(0, 0, 0)), dt, 1)
        return d1.position, d1.velocity
        
    def next_RK4(self, state, dt):
        d1 = self.step(state, State(coord.Vector3D(0, 0, 0), coord.Vector3D(0, 0, 0)), dt, 0)
        d2 = self.step(state, d1, dt, 0.5)
        d3 = self.step(state, d2, dt, 0.5)
        d4 = self.step(state, d3, dt,   1)

        pos = (d1.position + 2 * d2.position + 2 * d3.position + d4.position) / 6.0
        vel = (d1.velocity + 2 * d2.velocity + 2 * d3.velocity + d4.velocity) / 6.0
        return pos, vel

    def fly(self, *, fps=100, spf=1, integrator='euler'):
        dt = 1.0 / (spf * fps)
        time = 0
        step = 0
        self.frames = []

        next_step = {
            'euler': self.next_euler,
            'rk4': self.next_RK4,
        }[integrator]

        while True:
            dpos, dvel = next_step(State(self.position, self.velocity), dt)

            air_density = atmosphere.air_density(self.position.z)
            wind = get_wind(self.position)
            reynolds = atmosphere.Reynolds_number(2 * self.radius, self.velocity.norm(), air_density)
            gamma = atmosphere.drag_coefficient_smooth_sphere(reynolds)

            if step % spf == 0:
                self.frames.append((
                    time,
                    self.position.x,
                    self.position.y,
                    self.position.z,
                    self.velocity.x,
                    self.velocity.y,
                    self.velocity.z,
                    wind.x,
                    wind.y,
                    wind.z,
                    reynolds,
                    gamma,
                ))
                print(f"Time {time:8.02f} s: {self}, {dvel.norm():8.02f} m/s² | Re {reynolds:10.2f} \u0393 {gamma:5.3f}")

            self.position += dpos * dt
            self.velocity += dvel * dt

            time += dt
            step += 1

            if self.position.z < 0:
                print(f"Impact at {time:6.3f} s, {self.velocity.norm():8.3f} m/s!")
                break

    def to_dataframe(self):
        self.dataframe = pandas.DataFrame.from_records(
            self.frames,
            columns=self.columns,
        )

    def plot(self):
        pyplot.rcParams['font.family'] = "Minion Pro"
        pyplot.rcParams['mathtext.fontset'] = "dejavuserif"
        
        figure, axes = pyplot.subplots(3, 3)

        figure.tight_layout(rect=(0.05, 0.0, 1.0, 1.0))
        figure.set_size_inches(9, 8)

        axes[0, 0].tick_params(axis='x', which='major')
        axes[0, 0].tick_params(axis='y', which='major')
        axes[0, 0].grid(linewidth=0.2, color='black')

        axes[0, 0].set_xlabel('speed')
        axes[0, 0].set_ylabel('altitude')
#        axes.set_ylim(bottom=0)
        axes[0, 0].plot(self.dataframe.vx, self.dataframe.z)
        axes[0, 1].plot(self.dataframe.vy, self.dataframe.z)
        axes[0, 2].plot(self.dataframe.vz, self.dataframe.z)
        pyplot.show()

    def __str__(self):
        return f"{self.position.x:12.3f} {self.position.y:12.3f} {self.position.z:12.3f} | {self.velocity.x:12.3f} {self.velocity.y:12.3f} {self.velocity.z:12.3f} ({self.velocity.norm():12.3f} m/s)"


def main():
    meteorite = Meteorite(0.2286, 0.0253, np.pi / 4,
        coord.Vector3D(0, 0, 18000),
        coord.Vector3D(1100, 0, -2200 * np.cos(np.radians(30))),
    )
    meteorite.fly(fps=1, spf=10, integrator='rk4')
    meteorite.to_dataframe()
    meteorite.plot()

main()
