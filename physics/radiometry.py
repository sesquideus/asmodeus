from physics import constants
import math

def excitationCoefficient(speed: float) -> float:
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

def luminousEfficiency(speed: float) -> float:
    return 2 * 7.668e6 * excitationCoefficient(speed) / speed**2

def fluxDensity(flux, distance):
    return flux / (4 * math.pi * distance**2)

def absoluteMagnitude(flux: float) -> float:
    if flux < 1e-30:
        return math.inf
    return constants.absoluteMagnitudeOneWatt - 2.5 * math.log10(flux) 

def apparentMagnitude(fluxDensity: float) -> float:
    if fluxDensity < 1e-50:
        return math.inf
    return constants.apparentMagnitudeOneWm2 - 2.5 * math.log10(fluxDensity)

