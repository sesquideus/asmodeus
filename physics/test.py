#!/usr/bin/env python
import unittest, math, datetime
import random
import numpy as np

from physics import atmosphere, coord, constants, radiometry
from core import dataset
from models import observer, meteor, sighting
from discriminator import magnitude

class CaseAtmosphere(unittest.TestCase):
    def testAirmass90(self):
        self.assertAlmostEqual(atmosphere.air_mass(90), 1, delta = 0.001)

    def testAirmass0(self):
        self.assertAlmostEqual(atmosphere.air_mass(0), 38, delta = 0.5)

    def testAirmass45(self):
        self.assertAlmostEqual(atmosphere.air_mass(45), 1.4, delta = 0.02)

    def testDensityTooHigh(self):
        self.assertEqual(atmosphere.air_density(600000), 0)

    def testDensity10km(self):
        self.assertAlmostEqual(atmosphere.air_density(10000), 0.42, delta = 0.01)

    def testAttenuate_1_1(self):
        self.assertEqual(atmosphere.attenuate(1, 1), math.exp(constants.ATTENUATION_ONE_AIR_MASS))

    def testAttenuate_4_7(self):
        self.assertEqual(atmosphere.attenuate(4, 7), 4 * math.exp(constants.ATTENUATION_ONE_AIR_MASS * 7))

    def testAttenuate_5_3(self):
        self.assertEqual(atmosphere.attenuate(5, 3), 5 * math.exp(constants.ATTENUATION_ONE_AIR_MASS * 3))


class CaseRadiometry(unittest.TestCase):
    def testFluxDensityZero(self):
        self.assertEqual(radiometry.flux_density(0, 1), 0)

    def testFluxDensityFar(self):
        self.assertEqual(radiometry.flux_density(1, math.inf), 0)

    def testFluxDensityNormal(self):
        self.assertEqual(radiometry.flux_density(4 * math.pi, 1), 1)

    def testApparentMagnitudeSun(self):
        self.assertAlmostEqual(radiometry.apparent_magnitude(1361), constants.APPARENT_MAGNITUDE_SUN, delta = 0.01)


class CaseMeteor(unittest.TestCase):
    def setUp(self):
        self.observer = observer.Observer(
            'default',
            self.dataset,
            None,
            latitude    = 47,
            longitude   = 18,
            elevation   = 531,
        )
        self.position = coord.Vector3D.fromGeodetic(48, 17, 120000)
        self.meteor = meteor.Meteor(
            mass        = 1,
            density     = 800,
            position    = self.position,
            velocity    = -self.position / self.position.norm() * 50000,
            timestamp   = datetime.datetime.now(),
        )
        self.meteor.flyRK4(10, 10)
        self.sighting = sighting.PointSighting(sighting.Sighting(self.observer, self.meteor))

    def testSimpleMeteor(self):
        pass


class CaseVector3D(unittest.TestCase):
    def setUp(self):
        self.a = coord.Vector3D(57, 38, 49)
        self.b = coord.Vector3D(14, 33, 50)

        self.modra = coord.Vector3D.from_geodetic(48, 17, 531)
        self.modra_meteor_local = -coord.Vector3D.from_spherical(42, 130, 50000)

        self.modra_meteor_ECEF = coord.Vector3D.from_local(self.modra, -coord.modra_meteor_local)

    def testAdd(self):
        self.assertEqual(self.a + self.b, coord.Vector3D(71, 71, 99))

    def testSub(self):
        self.assertEqual(self.a - self.b, coord.Vector3D(43, 5, -1))

    def testNorm(self):
        self.assertEqual(self.a.norm(), math.sqrt(57*57 + 38*38 + 49*49))

    def testLatitude(self):
        self.assertAlmostEqual(self.modra.latitude(), 48, delta = 1e-12)
        
    def testLongitude(self):
        self.assertAlmostEqual(self.modra.longitude(), 17, delta = 1e-12)
        
    def testElevation(self):
        self.assertAlmostEqual(self.modra.elevation(), 531, delta = 1e-12)

    def testENS(self):
        self.assertEqual(self.modra_meteor_ECEF.x, )


class CaseEarthLocation(unittest.TestCase):
    def setUp(self):
        self.el = coord.EarthLocation.from_geodetic(48.313525, 17.315423, 531)
        self.pure1 = coord.Vector3D(10, 20, 30)
        self.pure2 = coord.Vector3D(10, 20, 30)

    def test_add_pure(self):
        a = self.pure1 + self.pure2

    def test_add_EarthLocation(self):
        with self.assertRaises(TypeError):
            a = self.el + self.pure1


if __name__ == '__main__':
    unittest.main()

