#!/usr/bin/env python3

import numpy as np
import pandas

from matplotlib import pyplot

from physics import atmosphere, coord, constants


def get_wind(vector):
    return coord.Vector3D(0, 0, 0)

def reynolds_number(length, speed, density):
    return length * speed * density / constants.AIR_VISCOSITY

def drag_coefficient(reynolds):
    a = reynolds / 5
    b = reynolds / 263000
    c = reynolds / 1000000

    return 24 / reynolds \
        + 2.6 * a / (1 + a)**1.52 \
        + 0.411 * b**-7.94 / (1 + b**-8) \
        + 0.25 * c / (1 + c)


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
        new_state = State(
            state.position + diff.position * dt * node,
            state.velocity + diff.velocity * dt * node,
        )
        air_density = atmosphere.air_density(state.position.z)
        speed = new_state.velocity.norm()
        wind = get_wind(new_state.position)
        reynolds = reynolds_number(self.radius, state.velocity.norm(), air_density / constants.AIR_VISCOSITY
        gamma = drag_coefficient(reynolds)

        return State(
            new_state.velocity,
            coord.Vector3D(
                -(gamma * air_density * (self.area / self.mass) * speed * (new_state.velocity.x - wind.x)),
                -(gamma * air_density * (self.area / self.mass) * speed * (new_state.velocity.y - wind.y)),
                -(gamma * air_density * (self.area / self.mass) * speed * (new_state.velocity.z - wind.z)) - constants.EARTH_GRAVITY,
            )
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
            reynolds = 2 * self.radius * self.velocity.norm() * air_density / constants.AIR_VISCOSITY
            gamma = drag_coefficient(reynolds)

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
                print(f"Time {time:8.02f} s: {self}, Re {reynolds:10.2f} \u0393 {gamma:5.3f}")


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
        
        figure, axes = pyplot.subplots()

        figure.tight_layout(rect = (0.05, 0.0, 1.0, 1.0))
        figure.set_size_inches(9, 8)

        axes.tick_params(axis='x', which='major', labelsize=16)
        axes.tick_params(axis='y', which='major', labelsize=16)
        axes.grid(linewidth = 0.2, color = 'black')

        axes.set_xlabel('speed', fontdict = {'fontsize': 16})
        axes.set_ylabel('altitude', fontdict = {'fontsize': 16})
        axes.plot(self.dataframe.x, self.dataframe.z)
        pyplot.show()

    def __str__(self):
        return f"{self.position.x:9.3f} {self.position.y:9.3f} {self.position.z:9.3f} | {self.velocity.x:12.3f} {self.velocity.y:12.3f} {self.velocity.z:12.3f}"


def main():
    meteorite = Meteorite(1, 0.1, 1.21,
        coord.Vector3D(0, 0, 106000),
        coord.Vector3D(500, 0, -1000),
    )
    meteorite.fly(fps=10, spf=10, integrator='rk4')
    meteorite.to_dataframe()
    meteorite.plot()

main()
