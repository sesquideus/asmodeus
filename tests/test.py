import unittest, math

from physics import atmosphere, constants, radiometry

class TestAtmosphere(unittest.TestCase):
    def testAirmass90(self):
        self.assertAlmostEqual(atmosphere.airMass(90), 1, delta = 0.001)

    def testAirmass0(self):
        self.assertAlmostEqual(atmosphere.airMass(0), 38, delta = 0.5)

    def testAirmass45(self):
        self.assertAlmostEqual(atmosphere.airMass(45), 1.4, delta = 0.02)

    def testDensityTooHigh(self):
        self.assertEqual(atmosphere.airDensity(300000), 0)

    def testDensity10km(self):
        self.assertAlmostEqual(atmosphere.airDensity(10000), 0.42, delta = 0.01)

    def testAttenuate_1_1(self):
        self.assertEqual(atmosphere.attenuate(1, 1), math.exp(constants.attenuationOneAirMass))

    def testAttenuate_4_7(self):
        self.assertEqual(atmosphere.attenuate(4, 7), 4 * math.exp(constants.attenuationOneAirMass * 7))

    def testAttenuate_5_3(self):
        self.assertEqual(atmosphere.attenuate(5, 3), 5 * math.exp(constants.attenuationOneAirMass * 3))

class TestRadiometry(unittest.TestCase):
    def testFluxDensityZero(self):
        self.assertEqual(radiometry.fluxDensity(0, 1), 0)

    def testFluxDensityFar(self):
        self.assertEqual(radiometry.fluxDensity(1, math.inf), 0)

    def testFluxDensityNormal(self):
        self.assertEqual(radiometry.fluxDensity(4 * math.pi, 1), 1)

    def testApparentMagnitudeSun(self):
        self.assertAlmostEqual(radiometry.apparentMagnitude(546.8), constants.apparentMagnitudeSun, delta = 0.001)

if __name__ == '__main__':
    unittest.main()
