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
        'entry_angle',
        'speed',
        'angular_speed',
        'massInitial',
        'mass',
        'density',
        'ablation_heat',
        'luminous_power',
        'fluxDensity',
        'apparent_magnitude',
        'absolute_magnitude',
        'is_brightest',
        'is_abs_brightest',
    ]

    def __init__(self, observer, meteor):
        self.observer               = observer
        self.meteor                 = meteor

        self.timestamp              = self.meteor.timestamp
        self.id                     = "{}{}".format(self.observer.id, self.timestamp)

        self.frames                 = [SightingFrame(self.observer, frame) for frame in self.meteor.frames]

        self.first                  = self.frames[0]
        self.last                   = self.frames[-1]
        self.brightest              = None
        self.abs_brightest          = None

        for frame in self.frames:
            if self.brightest is None or self.brightest.apparent_magnitude > frame.apparent_magnitude:
                self.brightest = frame

            if self.abs_brightest is None or self.abs_brightest.absolute_magnitude > frame.absolute_magnitude:
                self.abs_brightest = frame

        self.brightest.is_brightest = 1
        self.abs_brightest.is_abs_brightest = 1

        self.mass_initial           = self.first.frame.mass
        self.velocity_initial       = self.first.frame.velocity

    @staticmethod
    def load(filename):
        return pickle.load(io.FileIO(filename, 'rb'))

    def as_dict(self):
        return {
            'id':               self.id,
            'timestamp':        self.brightest.frame.timestamp,
            'simulationTime':   (self.last.frame.timestamp - self.first.frame.timestamp).total_seconds(),
        }

    def reduce_to_point(self):
        single_frame = copy.copy(self.abs_brightest)

        self.frames     = [single_frame]
        self.first      = single_frame
        self.last       = single_frame
        self.brightest  = single_frame

    def save(self, directory):
        pickle.dump(self, io.FileIO(os.path.join(directory, f"{self.id}.pickle"), 'wb'))

    def apply_bias(self, *discriminators):
        self.sighted = self.apply_bias(*discriminators)
        return self.sighted

    def __str__(self):
        return f"<Sighting by {self.observer.id} at {self.timestamp}>"
