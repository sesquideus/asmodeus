#!/usr/bin/env python3

from physics import atmosphere, coord


EARTH_GRAVITY = 9.81
GAMMA = 0.47


class State():
    def __init__(self, l, h, x, dl, dh, dx):
        self.l = l
        self.h = h
        self.x = x
        self.dl = dl
        self.dh = dh
        self.dx = dx

    def __str__(self):
        return f"Position {self.l:7.2f} {self.h:7.2f} {self.x:7.2f}, velocity {self.dl:7.2f} {self.dh:7.2f} {self.dx:7.2f}"


class Meteorite():
    def __init__(self, mass, area, l, h, x, dl, dh, dx):
        self.mass = mass
        self.area = area
        self.l = l
        self.h = h
        self.x = x
        self.dl = dl
        self.dh = dh
        self.dx = dx

    def step_euler(self, state, diff, dt):
        new_state = State(
            state.l + diff.l * dt,
            state.h + diff.h * dt,
            state.x + diff.x * dt,
            state.dl + diff.dl * dt,
            state.dh + diff.dh * dt,
            state.dx + diff.dx * dt,
        )
        air_density = atmosphere.air_density(state.h)

        return State(
            new_state.dl,
            new_state.dh,
            new_state.dx,
            (GAMMA * air_density * self.area * new_state.dl**2) / self.mass,
            (GAMMA * air_density * self.area * new_state.dh**2) / self.mass - EARTH_GRAVITY,
            (GAMMA * air_density * self.area * new_state.dx**2) / self.mass,
        )
        
    def fly_euler(self, *, fps=100, spf=1):
        dt = 1.0 / (spf * fps)
        time = 0
        step = 0

        while True:
            state = State(self.l, self.h, self.x, self.dl, self.dh, self.dx)
            diff = self.step_euler(state, State(0, 0, 0, 0, 0, 0), dt)

            if step % spf == 0:
                print(f"Time {time:8.02f} s: {self}")

            self.l += diff.l * dt
            self.h += diff.h * dt
            self.x += diff.x * dt

            self.dl += diff.dl * dt
            self.dh += diff.dh * dt
            self.dx += diff.dx * dt

            time += dt
            step += 1

            if self.h < 0:
                print("Impact!")
                break

    def __str__(self):
        return f"{self.l:9.2f} m, {self.h:9.2f} m, {self.x:7.2f} m, speed {self.dl:9.2f} m/s, {self.dh:9.2f} m/s, {self.dx:9.2f} m/s"


def main():
    meteorite = Meteorite(1, 0.01, 0, 36000, 0, 0, 100, 0)
    meteorite.fly_euler(fps=1, spf=100)

main()
