import unittest, math

from physics import atmosphere
from core import constants

class TestAtmosphere(unittest.TestCase):
    def testAirmass(self):
        self.assertLess(abs(atmosphere.airMass(90) - 1), 0.01)
        self.assertLess(abs(atmosphere.airMass(0) - 37.92), 0.01)

    def testDensity(self):
        self.assertEqual(atmosphere.airDensity(300000), 0)
        self.assertLess(abs(atmosphere.airDensity(10000) - 0.42), 0.01)

    def testAttenuate(self):
        self.assertEqual(atmosphere.attenuate(1, 1), math.exp(-constants.AIRMASS_ATTENUATION))
        self.assertEqual(atmosphere.attenuate(4, 7), 4 * math.exp(-constants.AIRMASS_ATTENUATION * 7))
        self.assertEqual(atmosphere.attenuate(5, 3), 5 * math.exp(-constants.AIRMASS_ATTENUATION * 3))

if __name__ == '__main__':
    unittest.main()
