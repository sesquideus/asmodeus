import math

from physics import constants


def excitation_coefficient(speed: float) -> float:
    if speed < 6200:
        return 0
    elif speed < 20000:
        return (-2.1887e-9 + 4.2903e-13 * speed - 1.2447e-17 * speed**2) * speed**2
    elif speed < 60000:
        return 2.37044e-6 * speed**1.25
    elif speed < 100000:
        return -12.835 + speed * (6.7672e-4 + speed * (-1.163076e-8 + speed * (9.191681e-14 + speed * -2.7465805e-19)))
    else:
        return 1.615 + speed * 1.3725e-5


def luminous_efficiency(speed: float) -> float:
    if speed > 1000:
        return 2 * 7.668e6 * excitation_coefficient(speed) / speed**2
    else:
        return 0


def flux_density(flux, distance):
    return flux / (4 * math.pi * distance**2)


def absolute_magnitude(flux: float) -> float:
    if flux == 0:
        return -math.inf
    return constants.ABSOLUTE_MAGNITUDE_ONE_WATT - 2.5 * math.log10(flux)


def apparent_magnitude(flux_density: float) -> float:
    if flux_density == 0:
        return 30
    return constants.APPARENT_MAGNITUDE_ONE_WM2 - 2.5 * math.log10(flux_density)


