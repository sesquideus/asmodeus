import datetime
import logging
import math
import io
import os
import numpy as np
import numba
import pickle

import models.frame

from physics import atmosphere, coord, radiometry, constants

log = logging.getLogger('root')


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


class Meteor:
    def __init__(self, *, mass, density, position, velocity, timestamp, dragCoefficient, **kwargs):
        self.mass               = mass
        self.density            = density
        self.radius             = (3 * self.mass / (self.density * math.pi * 4))**(1 / 3)

        self.position           = position
        self.velocity           = velocity

        self.timestamp          = timestamp
        self.time               = 0.0

        self.dragCoefficient    = dragCoefficient
        self.shapeFactor        = kwargs.get('shapeFactor',     1.21)
        self.heatTransfer       = kwargs.get('heatTransfer',    0.5)
        self.ablationHeat       = kwargs.get('ablationHeat',    8e6)

        self.luminousPower      = 0

        self.id                 = self.timestamp.strftime("%Y%m%d-%H%M%S-%f")
        self.frames             = []
        self.massInitial        = self.mass

        log.debug(self.__str__())

    @staticmethod
    def load(filename):
        return Meteor.loadPickle(filename)

    @staticmethod
    def loadPickle(filename):
        return pickle.load(io.FileIO(filename, 'rb'))

    def __str__(self):
        return f"<Meteor {self.id} at {self.position}, velocity {self.velocity} | " \
            f"{self.density:4.0f} kg/m³, Q {self.ablationHeat:8.0f} J/kg, G {self.dragCoefficient:5.3f}, " \
            f"m {self.mass:8.6e} kg, r {self.radius * 1000:10.3f} mm, {len(self.frames)} frames>"

    def save(self, filename):
        pickle.dump(self, io.FileIO(os.path.join(filename, f"{self.id}x{datetime.datetime.now().strftime('%H%M%S%f')}.pickle"), 'wb'))

    def evaluateRK4(self, state, diff, dt, node):
        newState = State(
            state.position + diff.drdt * dt * node,
            state.velocity + diff.dvdt * dt * node,
            max(state.mass + diff.dmdt * dt * node, 1e-12)
        )
        airRho = atmosphere.airDensity(newState.position.norm() - constants.earthRadius)
        speed = newState.velocity.norm()

        return Diff(
            newState.velocity,
            -(self.dragCoefficient * self.shapeFactor * airRho * speed / (newState.mass**(1 / 3) * self.density**(2 / 3))) * newState.velocity
            - constants.gravity * constants.earthMass / newState.position.norm()**3 * newState.position,
            -(self.heatTransfer * self.shapeFactor * airRho * speed**3 * (newState.mass / self.density)**(2 / 3) / (2 * self.ablationHeat)),
        )

    def flyRK4(self, frameRate, stepsPerFrame):
        dt = 1.0 / (frameRate * stepsPerFrame)
        frame = 0

        while True:
            state = State(self.position, self.velocity, self.mass)
            d0 = Diff(coord.Vector3D(0, 0, 0), coord.Vector3D(0, 0, 0), 0.0)
            d1 = self.evaluateRK4(state, d0, dt,   0)
            d2 = self.evaluateRK4(state, d1, dt, 0.5)
            d3 = self.evaluateRK4(state, d2, dt, 0.5)
            d4 = self.evaluateRK4(state, d3, dt,   1)

            drdt = (d1.drdt + 2 * d2.drdt + 2 * d3.drdt + d4.drdt) / 6.0
            dvdt = (d1.dvdt + 2 * d2.dvdt + 2 * d3.dvdt + d4.dvdt) / 6.0
            dmdt = (d1.dmdt + 2 * d2.dmdt + 2 * d3.dmdt + d4.dmdt) / 6.0

            speed = self.velocity.norm()

            self.luminousPower = -(radiometry.luminousEfficiency(speed) * dmdt * speed**2 / 2.0)
            self.entryAngle = math.degrees(math.asin(-self.position * self.velocity / (self.position.norm() * speed)))

            if (frame % stepsPerFrame == 0):
                self.frames.append(models.frame.Frame(self))
                log.debug("{time:6.3f} s | "
                          "{latitude:6.4f} N, {longitude:6.4f} E, {elevation:6.0f} m, {angle:6.2f}° | {density:9.3e} kg/m³ | "
                          "{speed:7.1f} m/s, {acceleration:13.3f} m/s², τ {lumEff:6.4f} | "
                          "{mass:6.2e} kg, {ablation:9.3e} kg/s {radius:7.3f} mm | I {lp:10.3e} W, M {absmag:6.2f}m".format(
                              time            = self.time,
                              latitude        = self.position.latitude(),
                              longitude       = self.position.longitude(),
                              elevation       = self.position.elevation(),
                              angle           = self.entryAngle,
                              density         = atmosphere.airDensity(self.position.elevation()),
                              speed           = self.velocity.norm(),
                              acceleration    = dvdt.norm(),
                              lumEff          = radiometry.luminousEfficiency(self.velocity.norm()),
                              ablation        = dmdt,
                              mass            = self.mass,
                              radius          = ((3 * self.mass) / (4 * np.pi * self.density)) + (1 / 3) * 1000,
                              lp              = self.luminousPower,
                              absmag          = radiometry.absoluteMagnitude(self.luminousPower),
                          ))

            frame += 1

            self.position += drdt * dt
            self.velocity += dvdt * dt
            self.mass     += dmdt * dt

            # Advance time by dt
            self.timestamp += datetime.timedelta(seconds = dt)
            self.time += dt

            # If all mass has been ablated away, the particle is pronounced dead
            if self.mass < 0:
                log.debug("Burnt to death")
                break

            # If the particle flew above 400 km, it will likely leave Earth altogether
            if self.position.elevation() > 400000:
                log.debug("Flew away")
                break

            # If the velocity is very low, it is a meteorite
            if self.velocity.norm() < 6500:
                log.debug(f"Survived with final mass {self.mass:12.6f} kg")
                break

            # If the elevation is below zero, we have an impact
            if self.position.elevation() < 0:
                log.debug("IMPACT")
                break

        log.debug(f"Meteor generated ({len(self.frames)} frames)")

    def reduceToPoint(self):
        maxLight = np.inf
        brightest = None

        for frame in self.frames:
            if frame.absoluteMagnitude < maxLight:
                maxLight = frame.absoluteMagnitude
                brightest = frame

        self.frames = [frame]

    def simulate(self):
        self.flyRK4()
        self.save()
