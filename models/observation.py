import datetime
import io
import os
import logging
import random

import time
import multiprocessing as mp

from core.parallel      import parallel
from models             import observer
from physics            import coord
from utilities          import colour as c

class Observation():
    def __init__(self, observer, population):
        pass

    def observe(self):
        log.info(f"Calculating {c.num(total)} observations using {c.num(self.config.mp.processes)} processes")

        meteorFiles = self.dataset.list('meteors')
        self.count = 0

        argList = [(
            self.dataset.path('meteors', meteorFile),
            self.dataset.path('sightings', self.observer.id, meteorFile),
        ) for meteorFile in meteorFiles]
        total = len(argList)


        self.sightings = parallel(
            observe,
            argList,
            initializer = initialize,
            initargs    = (observer, self.config.observations.streaks),
            action      = "Observing meteors",
            period      = self.config.mp.report
        )
        observer.createDataframe()
        observer.saveDataframe()

        self.count += len(observer.sightings)

    def save(self):
        pass
        

def initialize(queuex, observerx, streaksx):
    global queue, observer, streaks
    queue, observer, streaks = queuex, observerx, streaksx

def observe(args):
    filename, out = args

    queue.put(1)
    meteor = Meteor.load(filename)
    sighting = Sighting(observer, meteor)
    sighting.save(out, streak = streaks)

    if streaks:
        return sighting
    else:
        return sighting.asPoint()
