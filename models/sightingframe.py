import math
import logging
import copy
import pickle

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

        self.magnitude          = radiometry.apparentMagnitude(self.fluxDensity)
        self.sighted            = False

        log.debug("{timestamp} | {truePos}, {trueSpeed:7.0f} m/s | {altaz}, {angSpeed:6.3f}°/s | {mass:6.4e} kg, {fluxDensity:8.3e} W/m2, {magnitude:6.2f} m".format(
            timestamp           = frame.timestamp.strftime("%Y-%m-%dT%H:%M:%S:%f"),
            mass                = frame.mass,
            angSpeed            = self.angularSpeed,
            fluxDensity         = self.fluxDensity,
            magnitude           = self.magnitude,
            altaz               = self.altAz.strSpherical(),
            truePos             = self.frame.position.strGeodetic(),
            trueSpeed           = self.frame.velocity.norm(),
        ))

    def asDict(self):
        return {
            'timestamp'         : self.frame.timestamp.strftime("%Y-%m-%dT%H:%M:%S:%f"),
            'lifeTime'          : self.frame.lifeTime,
            'trackLength'       : self.frame.trackLength,
            'altitude'          : self.altAz.latitude(),
            'azimuth'           : self.altAz.longitude(),
            'distance'          : self.altAz.norm(),
            'elevation'         : self.frame.position.elevation(),
            'speed'             : self.frame.speed,
            'angularSpeed'      : self.angularSpeed,
            'mass'              : self.frame.mass,
            'luminousPower'     : self.frame.luminousPower,
            'fluxDensity'       : self.fluxDensity,
            'magnitude'         : self.magnitude,
        }

    def asTSV(self):
        return "{timestamp}\t{lifeTime:6.3f}\t{trackLength:7.0f}\t" \
            "{altitude:6.3f}\t{azimuth:7.3f}\t{distance:6.0f}\t" \
            "{elevation:7.0f}\t{speed:6.0f}\t{angularSpeed:7.3f}\t" \
            "{mass:12.6e}\t{luminousPower:9.3e}\t{fluxDensity:9.3e}\t{magnitude:6.2f}".format(
                timestamp           = self.frame.timestamp.strftime("%Y-%m-%dT%H:%M:%S:%f"),
                lifeTime            = self.frame.lifeTime,
                trackLength         = self.frame.trackLength,
                altitude            = self.altAz.latitude(),
                azimuth             = self.altAz.longitude(),
                distance            = self.altAz.norm(),
                elevation           = self.frame.position.elevation(),
                speed               = self.frame.speed,
                angularSpeed        = self.angularSpeed,
                mass                = self.frame.mass,
                luminousPower       = self.frame.luminousPower,
                fluxDensity         = self.fluxDensity,
                magnitude           = self.magnitude,
            )

    def save(self):
        return pickle.dumps(self)
