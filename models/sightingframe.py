import numpy as np
import datetime, argparse, math, sys, datetime, random, pprint, logging, copy, pickle, io, os

from core import atmosphere

log = logging.getLogger('root')

class SightingFrame():
    def __init__(self, observer, frame):
        self.observer           = observer
        self.frame              = copy.copy(frame)
        
        self.altAz              = observer.altAz(frame.position)
        self.relativePosition   = self.frame.position - self.observer.position
        
        dot                     = self.relativePosition * self.frame.velocity
        proj                    = dot / (self.relativePosition.norm() ** 2) * self.relativePosition
        perp                    = self.frame.velocity - proj

        self.angularSpeed       = math.degrees(perp.norm() / self.relativePosition.norm())
        try:
            self.lightFlux      = self.frame.luminousPower * math.exp(-0.294 * atmosphere.airMass(self.altAz.latitude(), self.observer.position.elevation())) / (self.altAz.norm()**2 * 4 * math.pi)
        except OverflowError:
            log.error("Light flux overflow: luminous power {}, air mass {}, alt-az {}".format(self.frame.luminousPower, airMass(self.altAz.latitude(), self.observer.position.elevation()), self.altAz))

        self.magnitude          = math.inf if self.lightFlux == 0 else -19.989 - 2.5 * math.log10(self.lightFlux)
        self.sighted            = False
            
        log.debug("{timestamp} | {truePos}, {trueSpeed:7.0f} m/s | {altaz}, {angSpeed:6.3f}°/s | {mass:6.4e} kg, {lightFlux:8.3e} W/m2, {magnitude:6.2f} m".format(
            timestamp           = frame.timestamp,
            mass                = frame.mass,
            angSpeed            = self.angularSpeed,
            lightFlux           = self.lightFlux,
            magnitude           = self.magnitude,
            altaz               = self.altAz.strSpherical(),
            truePos             = self.frame.position.strGeodetic(),
            trueSpeed           = self.frame.velocity.norm(),
        ))

    def dictionary(self):
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
            'lightFlux'         : self.lightFlux,
            'magnitude'         : self.magnitude,
        }
    
    def tsv(self):
        return "{timestamp}\t{lifeTime:6.3f}\t{trackLength:7.0f}\t" \
            "{altitude:6.3f}\t{azimuth:7.3f}\t{distance:6.0f}\t" \
            "{elevation:7.0f}\t{speed:6.0f}\t{angularSpeed:7.3f}\t" \
            "{mass:12.6e}\t{luminousPower:9.3e}\t{lightFlux:9.3e}\t{magnitude:6.2f}".format(
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
            lightFlux           = self.lightFlux,
            magnitude           = self.magnitude,
        )

    def pickle(self):
        return pickle.dumps(self)

