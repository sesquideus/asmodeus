import math

from physics import atmosphere, constants, coord

from integrators.state import State, Diff

EARTH_ROTATION = coord.Vector3D(0, 0, constants.EARTH_ANGULAR_SPEED)
#
#
class FlightModel:
    def __init__(self):
        pass

    def evaluate(self, meteor, state, diff, dt):
        pass

#
#class TextbookFactory(FlightModelFactory):
#    def __init__(self, *, use_WGS84=True, use_Coriolis=True, use_Huygens=True, atmospheric_density_function):
#        pass

class TextbookModel(FlightModel):
    def __init__(self):
        self.atmospheric_density_function = atmosphere.air_density

    def drag_vector(self, meteor, state):
        coordinates = state.position.to_WGS84()
        speed = state.velocity.norm()
        air_density = self.atmospheric_density_function(coordinates.alt)
        reynolds = atmosphere.Reynolds_number(meteor.radius, state.velocity.norm(), air_density / constants.AIR_VISCOSITY)
        gamma = atmosphere.drag_coefficient_smooth_sphere(reynolds)
        return -(gamma * meteor.shape_factor * air_density * speed / (math.exp(state.log_mass / 3) * meteor.density**(2 / 3))) * state.velocity

    def gravity_vector(self, state):
        return -constants.EARTH_GM / state.position.norm()**3 * state.position

    def Coriolis_vector(self, state):
        return -2 * (EARTH_ROTATION ^ state.velocity)

    def Huygens_vector(self, state):
        return -EARTH_ROTATION ^ (EARTH_ROTATION ^ state.position)

    def log_mass_change(self, meteor, state):
        coordinates = state.position.to_WGS84()
        air_density = self.atmospheric_density_function(coordinates.alt)
        speed = state.velocity.norm()
        return -(meteor.heat_transfer * meteor.shape_factor * air_density * speed**3 * (-state.log_mass / (meteor.density**2)**(1 / 3) / (2 * meteor.ablation_heat)))

    def evaluate(self, meteor, state, diff, dt):
        new_state = state + diff * dt

        return Diff(
            new_state.velocity,
            self.drag_vector(meteor, state) + self.gravity_vector(new_state) + self.Coriolis_vector(new_state) + self.Huygens_vector(new_state),
            self.log_mass_change(meteor, state),
        )
