import numpy as np
import datetime, argparse, math, yaml, sys, datetime, random, pprint, logging, copy, pickle, io, os
import functools, operator

from models.frame import Frame
from models.sightingframe import SightingFrame
from physics import atmosphere

log = logging.getLogger('root')

class Sighting():
    def __init__(self, observer, meteor):
        self.observer           = observer
        self.meteor             = meteor
        
        self.timestamp          = self.meteor.timestamp
        self.id                 = "{}{}".format(self.observer.id, self.timestamp)
        self.frames             = []
        self.firstFrame         = None
        self.brightestFrame     = None
        self.lastFrame          = None
        self.sighted            = None
        
        for frame in meteor.frames:
            currentFrame = SightingFrame(self.observer, frame)
            self.frames.append(currentFrame)

            if self.firstFrame == None:
                self.firstFrame = currentFrame
            if self.brightestFrame == None or currentFrame.fluxDensity > self.brightestFrame.fluxDensity:
                self.brightestFrame = currentFrame
            self.lastFrame = currentFrame
        

        for frame in self.frames:
            frame.sighted = self.sighted

    @staticmethod
    def load(filename):
        fileIO = io.FileIO(filename, 'rb')
        return pickle.load(fileIO)

    def printSkyPlot(self, streaks = False):
        file = open(self.observer.skyPlotFile, 'a')
        if streaks:
            print("# timestamp                      t        s    alt       az      d      ele      v       as            m           F0           F      mag", file = file)
            for frame in sighting.frames:
                print(frame.toTSV(), file = file)
        else:
            print(self.asPointTSV(), file = file)

    def save(self, filename):
        pickle.dump(PointSighting(self), io.FileIO(filename, 'wb'))

    def __str__(self):
        return "<Sighting by {observer} at {timestamp}>".format(
            observer        = self.observer.id,
            timestamp       = self.timestamp,
        )

class PointSighting():
    def __init__(self, sighting):
        self.id                 = sighting.id
        self.timestamp          = sighting.brightestFrame.frame.timestamp
        self.lifeTime           = sighting.lastFrame.frame.lifeTime
        self.trackLength        = sighting.lastFrame.frame.trackLength
        self.altitude           = sighting.brightestFrame.altAz.latitude()
        self.azimuth            = sighting.brightestFrame.altAz.longitude()
        self.distance           = sighting.brightestFrame.altAz.norm()
        self.elevation          = sighting.brightestFrame.frame.position.elevation()
        self.speed              = sighting.brightestFrame.frame.speed
        self.angularSpeed       = sighting.brightestFrame.angularSpeed
        self.initialMass        = sighting.firstFrame.frame.mass
        self.mass               = sighting.brightestFrame.frame.mass
        self.luminousPower      = sighting.brightestFrame.frame.luminousPower
        self.fluxDensity        = sighting.brightestFrame.fluxDensity
        self.magnitude          = sighting.brightestFrame.magnitude

        self.frames             = [frame.tsv() for frame in sighting.frames]

    def tsv(self):
        return "{timestamp}\t{lifeTime:6.3f}\t{trackLength:7.0f}\t" \
            "{altitude:6.3f}\t{azimuth:7.3f}\t{distance:6.0f}\t" \
            "{elevation:7.0f}\t{speed:6.0f}\t{angularSpeed:7.3f}\t" \
            "{initialMass:12.6e}\t{luminousPower:9.3e}\t{fluxDensity:9.3e}\t{magnitude:6.2f}\t{sighted}".format(
            timestamp           = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S:%f"),
            lifeTime            = self.lifeTime,
            trackLength         = self.trackLength,
            altitude            = self.altitude,
            azimuth             = self.azimuth,
            distance            = self.distance,
            elevation           = self.elevation,
            speed               = self.speed,
            angularSpeed        = self.angularSpeed,
            initialMass         = self.initialMass,
            mass                = self.mass,
            luminousPower       = self.luminousPower,
            fluxDensity         = self.fluxDensity,
            magnitude           = self.magnitude,
            sighted             = int(self.sighted),
        )

    def applyBias(self, *discriminators):
        self.sighted            = all(map(lambda dis: dis.apply(self), discriminators))
        return self.sighted

    def printSkyPlot(self, filename, streaks):
        file = open(filename, 'a')
        if streaks:
            print("# timestamp                      t        s    alt       az      d      ele      v       as            m           F0           F      mag", file = file)
            for frame in self.frames:
                print(frame, file = file)
        else:
            print(self.tsv(), file = file)


