import logging
import pickle
import io
import copy
import os

from models.sightingframe import SightingFrame

log = logging.getLogger('root')


class Sighting():
    columns = [
        'timestamp',
        'time',
        'altitude',
        'azimuth',
        'distance',
        'elevation',
        'entryAngle',
        'speed',
        'angSpeed',
        'massInitial',
        'mass',
        'density',
        'lumPower',
        'fluxDensity',
        'appMag',
        'absMag',
    ]

    def __init__(self, observer, meteor):
        self.observer           = observer
        self.meteor             = meteor

        self.timestamp          = self.meteor.timestamp
        self.id                 = "{}{}".format(self.observer.id, self.timestamp)

        self.frames             = [SightingFrame(self.observer, meteorFrame) for meteorFrame in self.meteor.frames]

        self.first              = self.frames[0]
        self.last               = self.frames[-1]
        self.brightest          = None

        for frame in self.frames:
            if self.brightest is None or self.brightest.apparentMagnitude > frame.apparentMagnitude:
                self.brightest = frame

        self.massInitial        = self.first.frame.mass
        self.velocityInfinity   = self.first.frame.velocity

    @staticmethod
    def load(filename):
        return pickle.load(io.FileIO(filename, 'rb'))

    def asDict(self):
        return {
            'id':               self.id,
            'timestamp':        self.brightest.frame.timestamp,
            'simulationTime':   (self.last.frame.timestamp - self.first.frame.timestamp).total_seconds(),
        }

    def reduceToPoint(self):
        singleFrame = copy.copy(self.brightest)

        self.frames     = [singleFrame]
        self.first      = singleFrame
        self.last       = singleFrame
        self.brightest  = singleFrame

    def save(self, directory):
        pickle.dump(self, io.FileIO(os.path.join(directory, f"{self.id}.pickle"), 'wb'))

    def applyBias(self, *discriminators):
        self.sighted = self.applyBias(*discriminators)
        return self.sighted

    def __str__(self):
        return f"<Sighting by {self.observer.id} at {self.timestamp}>"
