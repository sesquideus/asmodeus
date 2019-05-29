import logging
import pickle
import io

import numpy as np
import pandas as pd

from models.sightingframe import SightingFrame

log = logging.getLogger('root')


class Sighting():
    def __init__(self, observer, meteor):
        self.observer           = observer
        self.meteor             = meteor

        self.timestamp          = self.meteor.timestamp
        self.id                 = "{}{}".format(self.observer.id, self.timestamp)
        self.sighted            = None

        self.frames = [SightingFrame(self.observer, meteorFrame) for meteorFrame in self.meteor.frames]

        #log.debug(self.frames)
    
        self.first          = self.frames[0]
        self.last           = self.frames[-1]
        self.brightest      = None
        #self.firstVisible   = None
        #self.lastVisible    = None

        for frame in self.frames:
            if self.brightest is None or self.brightest.apparentMagnitude > frame.apparentMagnitude:
                self.brightest = frame
            #if frame.apparentMagnitude < 4:
            #    if self.firstVisible is None:
            #        self.firstVisible = frame
            #    self.lastVisible = frame

    @staticmethod
    def load(filename):
        return pickle.load(io.FileIO(filename, 'rb'))

    def asDict(self):
        return {
            'id':               self.id,
            'timestamp':        self.brightest.frame.timestamp,
            'simulationTime':   (self.last.frame.timestamp - self.first.frame.timestamp).total_seconds(),
            #'lightTime':        (self.lastVisible.timestamp - self.firstVisible.timestamp).total_seconds(),
        }

    def asPoint(self):
        return PointSighting(self)

    def printTSV(self, file):
        for frame in self.frames:
            print(frame.asTSV(), file = file)

    def save(self, filename, *, streak = False):
        if streak:
            self.saveStreak(filename)
        else:
            self.savePoint(filename)

    def saveStreak(self, filename):
        pickle.dump(self, io.FileIO(filename, 'wb'))

    def savePoint(self, filename):
        pickle.dump(PointSighting(self), io.FileIO(filename, 'wb'))

    def applyBias(self, *discriminators):
        self.sighted = self.asPoint().applyBias(*discriminators)
        return self.sighted

    def __str__(self):
        return "<Sighting by {observer} at {timestamp}>".format(
            observer        = self.observer.id,
            timestamp       = self.timestamp,
        )

class PointSighting():
    columns = [
        'timestamp',
        'altitude',
        'azimuth',
        'distance',
        'elevation',
        'speed',
        'angSpeed',
        'initMass',
        'mass',
        'lumPower',
        'fluxDensity',
        'absMag',
        'appMag',
    ]

    def __init__(self, sighting):
        self.id                 = sighting.id
        self.timestamp          = sighting.brightest.frame.timestamp
        self.altitude           = sighting.brightest.altAz.latitude()
        self.azimuth            = sighting.brightest.altAz.longitude()
        self.distance           = sighting.brightest.altAz.norm()
        self.position           = sighting.brightest.frame.position
        self.velocity           = sighting.brightest.frame.velocity
        self.velocityInf        = sighting.first.frame.velocity
        self.angularSpeed       = sighting.brightest.angularSpeed
        self.initialMass        = sighting.first.frame.mass
        self.mass               = sighting.brightest.frame.mass
        self.luminousPower      = sighting.brightest.frame.luminousPower
        self.fluxDensity        = sighting.brightest.fluxDensity
        self.absoluteMagnitude  = sighting.brightest.frame.absoluteMagnitude
        self.apparentMagnitude  = sighting.brightest.apparentMagnitude

    def asPoint(self):
        return self

    def asTSV(self):
        return "{timestamp}\t" \
            "{altitude:6.3f}\t" \
            "{azimuth:7.3f}\t" \
            "{distance:6.0f}\t" \
            "{elevation:7.0f}\t" \
            "{speed:6.0f}\t" \
            "{angularSpeed:7.3f}\t" \
            "{initialMass:12.6e}\t" \
            "{luminousPower:9.3e}\t" \
            "{fluxDensity:9.3e}\t" \
            "{absMag:6.2f}\t" \
            "{appMag:6.2f}".format(
                timestamp           = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                altitude            = self.altitude,
                azimuth             = self.azimuth,
                distance            = self.distance,
                elevation           = self.position.elevation(),
                speed               = self.velocity.norm(),
                angularSpeed        = self.angularSpeed,
                initialMass         = self.initialMass,
                luminousPower       = self.luminousPower,
                fluxDensity         = self.fluxDensity,
                absMag              = self.absoluteMagnitude,
                appMag              = self.apparentMagnitude,
            )

    def asDict(self):
        return {
            'timestamp':    self.timestamp,
            'altitude':     self.altitude,
            'azimuth':      self.azimuth,
            'distance':     self.distance,
            'elevation':    self.position.elevation(),
            'speed':        self.velocity.norm(),
            'angSpeed':     self.angularSpeed,
            'initMass':     self.initialMass,
            'mass':         self.mass,
            'lumPower':     self.luminousPower,
            'fluxDensity':  self.fluxDensity,
            'absMag':       self.absoluteMagnitude,
            'appMag':       self.apparentMagnitude,
        }

    def asTuple(self):
        return (
            self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            self.altitude,
            self.azimuth,
            self.distance,
            self.position.elevation(),
            self.velocity.norm(),
            self.angularSpeed,
            self.initialMass,
            self.mass,
            self.luminousPower,
            self.fluxDensity,
            self.absoluteMagnitude,
            self.apparentMagnitude,
        )

    def applyBias(self, *discriminators):
        self.sighted = all(map(lambda dis: dis.apply(self), discriminators))
        return self.sighted

    def printTSV(self, file):
        print(self.asTSV(), file = file)
