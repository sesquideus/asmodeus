#!/usr/bin/env python
import unittest, math, datetime
import random
import numpy as np

from core import dataset, histogram
from models import observer, meteor, sighting
from discriminator import magnitude


class CaseHistogram(unittest.TestCase):
    def setUp(self):
        self.h1 = histogram.FloatHistogram(0, 100, 1)
        self.h2 = histogram.FloatHistogram(0, 100, 1)
        self.h3 = histogram.FloatHistogram(0, 100, 2)
        self.h4 = histogram.FloatHistogram(0, 100, 3)

        self.h1.add(55)
        self.h2.add(45)

    def testChiSquareDistinct(self):
        self.assertEqual(self.h1 @ self.h2, 2) 

    def testChiSquareSelf(self):
        self.assertEqual(self.h1 @ self.h1, 0)
        self.assertEqual(self.h2 @ self.h2, 0)

    def testHistogramOutOfRange(self):
        self.assertRaisesRegexp(KeyError, "outside permissible range", self.h1.add, 105)

    def testChiSquareIncompatible(self):
        self.assertRaisesRegexp(TypeError, "Incompatible histograms", self.h3.__matmul__, self.h4)
