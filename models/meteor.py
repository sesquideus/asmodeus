import datetime
import logging
import math
import io
import os
import pickle

import models.frame

from physics        import atmosphere, coord, radiometry, constants

log = logging.getLogger('root')


class State:
    def __init__(self, position, velocity, mass):
        self.position = position
        self.velocity = velocity
        self.mass = mass


class Diff:
    def __init__(self, drdt, dvdt, dmdt):
        self.drdt = drdt
        self.dvdt = dvdt
        self.dmdt = dmdt


class Meteor:
    def __init__(self, **kwargs):
        self.mass               = kwargs.get('mass',            1)
        self.density            = kwargs.get('density',         800)
        self.radius             = (3 * self.mass / (self.density * math.pi * 4))**(1 / 3)

        self.position           = kwargs.get('position',        coord.Vector3D.fromGeodetic(48, 17, 120000))
        self.velocity           = kwargs.get('velocity',        coord.Vector3D(0, 0, 0))

        self.timestamp          = kwargs.get('timestamp',       datetime.datetime.now())

        self.dragCoefficient    = kwargs.get('dragCoefficient', 0.6)
        self.shapeFactor        = kwargs.get('shapeFactor',     1.21)
        self.heatTransfer       = kwargs.get('heatTransfer',    0.5)
        self.ablationHeat       = kwargs.get('ablationHeat',    8e6)

        self.luminousPower      = 0

        self.id                 = self.timestamp.strftime("%Y%m%d-%H%M%S-%f")
        self.frames             = []

        log.debug(self.__str__())

    @staticmethod
    def load(filename):
        return Meteor.loadPickle(filename)

    @staticmethod
    def loadPickle(filename):
        return pickle.load(io.FileIO(filename, 'rb'))

    @staticmethod
    def loadHDF5(filename):
        return pickle.load(io.FileIO(filename, 'rb'))

    def __str__(self):
        return "<Meteor {id} at {position}, velocity {velocity} | " \
            "rho {density:4.0f} kg/m3, Q {ablationHeat:8.0f} J/kg, " \
            "m {mass:10.6e} kg, r {radius:10.3f} mm>".format(
                id              = self.id,
                position        = self.position,
                velocity        = self.velocity,
                mass            = self.mass,
                radius          = self.radius * 1000,
                density         = self.density,
                ablationHeat    = self.ablationHeat,
            )

    def saveHDF5(self, dataset):
        pass        

    def save(self, dataset):
        fileIO = io.FileIO(os.path.join('datasets', dataset, 'meteors', '{}.{}'.format(self.id, 'pickle')), 'wb')
        pickle.dump(self, fileIO)

    def saveKML(self, dataset):
        print(
            jinjaEnv('templates').get_template('meteor.kml').render({'meteor': self}),
            file = open(os.path.join(dataset, 'meteors', '{}.kml'.format(self.id)), 'w')
        )

    def pickle(self):
        return pickle.dumps(self)

    def acceleration(self, state):
        airRho = atmosphere.airDensity(state.position.norm() - constants.earthRadius)
        speed = state.velocity.norm()
        return -(self.dragCoefficient * self.shapeFactor * airRho * speed**2 / (state.mass**(1 / 3) * self.density**(2 / 3))) * state.velocity / speed

    def ablation(self, state):
        airRho = atmosphere.airDensity(state.position.norm() - 6371000)
        speed = state.velocity.norm()
        return -(self.heatTransfer * self.shapeFactor * airRho * speed**3 * (state.mass / self.density)**(2 / 3) / (2 * self.ablationHeat))

    def evaluate(self, state, diff, dt):
        newState = State(
            state.position + diff.drdt * dt,
            state.velocity + diff.dvdt * dt,
            max(state.mass + diff.dmdt * dt, 1e-8)
        )

        return Diff(
            newState.velocity,
            self.acceleration(newState),
            self.ablation(newState)
        )

    def flyRK4(self, frameRate, stepsPerFrame):
        dt = 1.0 / (frameRate * stepsPerFrame)
        frame = 0

        while True:
            state = State(self.position, self.velocity, self.mass)
            d0 = Diff(coord.Vector3D(0, 0, 0), coord.Vector3D(0, 0, 0), 0.0)
            d1 = self.evaluate(state, d0, 0.0)
            d2 = self.evaluate(state, d1, dt / 2)
            d3 = self.evaluate(state, d2, dt / 2)
            d4 = self.evaluate(state, d3, dt)

            drdt = (d1.drdt + 2 * d2.drdt + 2 * d3.drdt + d4.drdt) / 6.0
            dvdt = (d1.dvdt + 2 * d2.dvdt + 2 * d3.dvdt + d4.dvdt) / 6.0
            dmdt = (d1.dmdt + 2 * d2.dmdt + 2 * d3.dmdt + d4.dmdt) / 6.0

            self.luminousPower = -(radiometry.luminousEfficiency(self.velocity.norm()) * dmdt * self.velocity.norm()**2 / 2.0)

            if (frame % stepsPerFrame == 0):
                self.frames.append(models.frame.Frame(self))
                log.debug("{frame:04d} {time:6.3f} s | "
                          "{latitude:6.4f} °N, {longitude:6.4f} °E, {elevation:6.0f} m | {density:9.3e} kg/m³ | "
                          "v {speed:9.3f} m/s, dv {acceleration:13.3f} m/s², τ {lumEff:6.4f} | "
                          "m {mass:8.4e} kg, dm {ablation:10.4e} kg/s | I {lp:10.3e} W, M {absmag:6.2f}m".format(
                              frame           = frame,
                              time            = frame * dt,
                              latitude        = self.position.latitude(),
                              longitude       = self.position.longitude(),
                              elevation       = self.position.elevation(),
                              density         = atmosphere.airDensity(self.position.elevation()),
                              speed           = self.velocity.norm(),
                              acceleration    = -dvdt.norm(),
                              lumEff          = radiometry.luminousEfficiency(self.velocity.norm()),
                              ablation        = dmdt,
                              mass            = self.mass,
                              lp              = self.luminousPower,
                              absmag          = radiometry.absoluteMagnitude(self.luminousPower),
                          ))

            frame += 1

            self.timestamp += datetime.timedelta(seconds = dt)

            self.position += drdt * dt
            self.velocity += dvdt * dt
            self.mass     += dmdt * dt

            # Advance time by dt
            self.timestamp += datetime.timedelta(seconds = dt)

            # If all mass has been ablated away, the particle is pronounced dead
            if self.mass < 0:
                log.debug("Burnt to death")
                self.fate = "Ablated"
                break

            if self.position.elevation() > 200000:
                log.debug("Flew away")
                self.fate = "Flew away"
                break

            if self.velocity.norm() < 2500:
                log.debug("Survived with final mass {:12.6f} kg".format(self.mass))
                self.fate = "Meteorite"
                break

            if self.position.elevation() < 0:
                log.debug("IMPACT")
                self.fate = "Crater"
                break

    def simulate(self):
        self.flyRK4()
        self.save()
