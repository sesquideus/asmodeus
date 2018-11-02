#!/usr/bin/env python
import unittest, math, datetime
import random
import numpy as np

from core.histogram import FloatHistogram, TimeHistogram
from models import observer, meteor, sighting
from core import dataset
from physics import coord
from discriminator import magnitude


class CaseDiscriminator(unittest.TestCase):
    
    def testSigmoidPlusInf(self):
        self.sigmoidPlusInf = magnitude.MagnitudeDiscriminator('sigmoid', limit = math.inf, width = 3)
        self.assertEqual(self.sigmoidPlusInf.function(self.sighting.magnitude), 1)

    def testSigmoidMinusInf(self):
        self.sigmoidMinusInf = magnitude.MagnitudeDiscriminator('sigmoid', limit = -math.inf, width = 1)
        self.assertEqual(self.sigmoidMinusInf.function(self.sighting.magnitude), 0)

    def testSigmoidCenter(self):
        limit = random.uniform(-5, 5)
        self.sigmoid = magnitude.MagnitudeDiscriminator('sigmoid', limit = limit, width = 6)
        self.assertAlmostEqual(self.sigmoid.function(limit), 0.5, delta = 1e-10)

    def testSigmoidDecreasing(self):
        self.sigmoid = magnitude.MagnitudeDiscriminator('sigmoid', limit = random.uniform(-5, 5), width = random.uniform(1, 2))
        for i in np.arange(-10, 10, 0.1):
            self.assertGreater(self.sigmoid.function(i), self.sigmoid.function(i + 0.1))

class CaseHistogram(unittest.TestCase):
    def setUp(self):
        self.histogram = FloatHistogram('test', 0, 10, 1)

    def testHistogramOutOfRange(self):
        try:
            self.assertRaises(self.histogram.add(10.5), KeyError)
        except:
            pass

if __name__ == '__main__':
    unittest.main()
