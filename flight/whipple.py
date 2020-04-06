import math

from physics import atmosphere, constants, coord

from .base import FlightModel

from integrators.state import State, Diff


class Whipple(FlightModel):
    def __init__(self):
        self.atmospheric_density_function = atmosphere.air_density

    def drag_vector(self, meteor, state):
        coordinates = state.position.to_WGS84()
        speed = state.velocity.norm()
        air_density = self.atmospheric_density_function(coordinates.alt)

        mass = math.exp(state.log_mass)
        radius = ((3 * mass) / (4 * math.pi * meteor.density))**(1 / 3)
        #reynolds = atmosphere.Reynolds_number(2 * radius, state.velocity.norm(), air_density)
        gamma = meteor.drag_coefficient #atmosphere.drag_coefficient_smooth_sphere(reynolds)
        drag = -(gamma * meteor.shape_factor * air_density * speed * mass**(-1 / 3) * meteor.density**(-2 / 3)) * state.velocity
        return drag

    def log_mass_change(self, meteor, state):
        coordinates = state.position.to_WGS84()
        air_density = self.atmospheric_density_function(coordinates.alt)
        speed = state.velocity.norm()
        mass_change = -meteor.ablation_const * air_density * speed**3 * math.exp(-state.log_mass / 3)
        return mass_change

    def get_acting_forces(self, meteor, state):
        #print(meteor, state)
        #print(self.Newtonian_gravity(state))
        #print(self.Coriolis_vector(state))
        #print(self.Huygens_vector(state))
        #print(self.drag_vector(meteor, state))
        force = self.Newtonian_gravity(state) + self.drag_vector(meteor, state)
            #self.Coriolis_vector(state) + \
            #self.Huygens_vector(state) + \
            #self.drag_vector(meteor, state)
        return force

    def evaluate(self, meteor, state, diff, dt):
        new_state = state + diff * dt

        return Diff(
            new_state.velocity,
            self.get_acting_forces(meteor, new_state),
            self.log_mass_change(meteor, new_state),
        )
