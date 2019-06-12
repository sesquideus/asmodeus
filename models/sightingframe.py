import math
import logging
import copy
import pickle
import dotmap

from physics import atmosphere, radiometry

log = logging.getLogger('root')


class SightingFrame():
    def __init__(self, observer, frame):
        self.observer           = observer
        self.frame              = copy.copy(frame)

        self.altAz              = observer.altAz(frame.position)
        self.relativePosition   = self.frame.position - self.observer.position

        dot                     = self.relativePosition * self.frame.velocity
        projection              = dot / (self.relativePosition.norm() ** 2) * self.relativePosition
        rejection               = self.frame.velocity - projection
        self.angularSpeed       = math.degrees(rejection.norm() / self.relativePosition.norm())

        airMass                 = atmosphere.airMass(self.altAz.latitude(), self.observer.position.elevation())
        attenuatedPower         = atmosphere.attenuate(self.frame.luminousPower, airMass)
        self.fluxDensity        = radiometry.fluxDensity(attenuatedPower, self.altAz.norm())

        self.apparentMagnitude  = radiometry.apparentMagnitude(self.fluxDensity)
        self.absoluteMagnitude  = self.frame.absoluteMagnitude
        log.debug(self)

    def __str__(self):
        return "{timestamp} | {truePos}, {trueSpeed:7.0f} m/s | {altaz}, {angSpeed:6.3f}°/s | {mass:6.4e} kg, {fluxDensity:8.3e} W/m2, {magnitude:6.2f} m".format(
            timestamp           = self.frame.timestamp.strftime("%Y-%m-%dT%H:%M:%S:%f"),
            mass                = self.frame.mass,
            angSpeed            = self.angularSpeed,
            fluxDensity         = self.fluxDensity,
            magnitude           = self.apparentMagnitude,
            altaz               = self.altAz.strSpherical(),
            truePos             = self.frame.position.strGeodetic(),
            trueSpeed           = self.frame.velocity.norm(),
        )

    def asDict(self):
        return {
            'timestamp'         : self.frame.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            'altitude'          : self.altAz.latitude(),
            'azimuth'           : self.altAz.longitude(),
            'distance'          : self.altAz.norm(),
            'elevation'         : self.frame.position.elevation(),
            'entryAngle'        : self.frame.entryAngle,
            'speed'             : self.frame.speed,
            'angularSpeed'      : self.angularSpeed,
            'mass'              : self.frame.mass,
            'luminousPower'     : self.frame.luminousPower,
            'fluxDensity'       : self.fluxDensity,
            'apparentMagnitude' : self.apparentMagnitude,
            'absoluteMagnitude' : self.absoluteMagnitude,
        }

    def asDotMap(self):
        return dotmap.DotMap(self.asDict())

    def asTuple(self):
        return (
            self.frame.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            self.altAz.latitude(),
            self.altAz.longitude(),
            self.altAz.norm(),
            self.frame.position.elevation(),
            self.frame.entryAngle,
            self.frame.speed,
            self.angularSpeed,
            self.frame.mass,
            self.frame.mass,
            self.frame.luminousPower,
            self.fluxDensity,
            self.apparentMagnitude,
            self.absoluteMagnitude,
        )

    def save(self):
        return pickle.dumps(self)
