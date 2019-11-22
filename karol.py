#!/usr/bin/env python3

from physics import atmosphere, coord


EARTH_GRAVITY = 9.81
GAMMA = 0.47

def get_wind(vector):
    return coord.Vector3D(0, 0, 0)


class State():
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity

    def __str__(self):
        return f"State {self.position}, {self.velocity}"


class Meteorite():
    def __init__(self, mass, area, position, velocity):
        self.mass = mass
        self.area = area
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

        return State(
            new_state.velocity,
            coord.Vector3D(
                -(GAMMA * air_density * (self.area / self.mass) * speed * (new_state.velocity.x + wind.x)),
                -(GAMMA * air_density * (self.area / self.mass) * speed * (new_state.velocity.y + wind.y)),
                -(GAMMA * air_density * (self.area / self.mass) * speed * (new_state.velocity.z + wind.z)) - EARTH_GRAVITY,
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

        next_step = {
            'euler': self.next_euler,
            'rk4': self.next_RK4,
        }[integrator]

        while True:
            dpos, dvel = next_step(State(self.position, self.velocity), dt)

            if step % spf == 0:
                print(f"Time {time:8.02f} s: {self}")

            self.position += dpos * dt
            self.velocity += dvel * dt

            time += dt
            step += 1

            if self.position.z < 0:
                print(f"Impact at {time:6.3f} s, {self.velocity.norm():8.3f} m/s!")
                break

    def __str__(self):
        return f"{self.position.x:9.3f} {self.position.y:9.3f} {self.position.z:9.3f} | {self.velocity.x:9.3f} {self.velocity.y:9.3f} {self.velocity.z:9.3f}"


def main():
    meteorite = Meteorite(1, 0.01,
        coord.Vector3D(0, 0, 36000),
        coord.Vector3D(0, 100, 0),
    )
    meteorite.fly(fps=1, spf=1, integrator='rk4')

main()
