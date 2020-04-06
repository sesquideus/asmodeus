import math

from physics import atmosphere, constants, coord

from integrators.state import State, Diff

EARTH_ROTATION = coord.Vector3D(0, 0, constants.EARTH_ANGULAR_SPEED)


class FlightModel:
    def __init__(self):
        pass

    def evaluate(self, meteor, state, diff, dt):
        pass

    def Newtonian_gravity(self, state):
        return -constants.EARTH_GM / state.position.norm()**3 * state.position

    def Coriolis_vector(self, state):
        return -2 * (EARTH_ROTATION ^ state.velocity)

    def Huygens_vector(self, state):
        return -EARTH_ROTATION ^ (EARTH_ROTATION ^ state.position)


class TextbookFactory:
    def __init__(self, *, use_WGS84=True, use_Coriolis=True, use_Huygens=True, atmospheric_density_function):
        pass
