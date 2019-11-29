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


#class CaseMeteor(unittest.TestCase):
#    def setUp(self):
#        self.observer = observer.Observer(
#            'default',
#            self.dataset,
#            None,
#            latitude    = 47,
#            longitude   = 18,
#            elevation   = 531,
#        )
#        self.position = coord.Vector3D.fromGeodetic(48, 17, 120000)
#        self.meteor = meteor.Meteor(
#            mass        = 1,
#            density     = 800,
#            position    = self.position,
#            velocity    = -self.position / self.position.norm() * 50000,
#            timestamp   = datetime.datetime.now(),
#        )
#        self.meteor.flyRK4(10, 10)
#        self.sighting = sighting.PointSighting(sighting.Sighting(self.observer, self.meteor))
#
#    def testSimpleMeteor(self):
#        pass


class CaseVector3D(unittest.TestCase):
    def setUp(self):
        self.a = coord.Vector3D(57, 38, 49)
        self.b = coord.Vector3D(14, 33, 50)

        self.meteor_local = -coord.Vector3D.from_spherical(42, 130, 50000)
        self.meteor_down = -coord.Vector3D.from_spherical(90, 0, 50000)
        self.meteor_to_north = -coord.Vector3D.from_spherical(0, 0, 20000)
        self.meteor_arbitrary = -coord.Vector3D.from_spherical(15.2645, 231.8453, 36256)

        self.modra = coord.Vector3D.from_geodetic(48.352, 17.313, 531)
        self.null_island = coord.Vector3D.from_geodetic(0, 0, 0)
        self.north_pole = coord.Vector3D.from_geodetic(90, 0, 0)
        self.south_pole = coord.Vector3D.from_geodetic(-90, 0, 0)

        self.modra_meteor_ECEF = coord.Vector3D.from_local(self.modra, -self.meteor_local)


    def testAdd(self):
        self.assertEqual(self.a + self.b, coord.Vector3D(71, 71, 99))

    def testSub(self):
        self.assertEqual(self.a - self.b, coord.Vector3D(43, 5, -1))

    def testNorm(self):
        self.assertEqual(self.a.norm(), math.sqrt(57*57 + 38*38 + 49*49))

    def testLatitude(self):
        self.assertAlmostEqual(self.modra.latitude(), 48.352, delta = 1e-12)
        
    def testLongitude(self):
        self.assertAlmostEqual(self.modra.longitude(), 17.313, delta = 1e-12)
        
    def testElevation(self):
        self.assertAlmostEqual(self.modra.elevation(), 531, delta = 1e-12)

    def test_null_island_arbitrary(self):
        meteor_local = coord.Vector3D.from_local(self.null_island, self.meteor_local)
        self.assertAlmostEqual(meteor_local.x, -np.sin(np.radians(42)) * 50000, delta = 1e-10)
        self.assertAlmostEqual(meteor_local.y, -np.cos(np.radians(42)) * np.sin(np.radians(130)) * 50000, delta = 1e-10)
        self.assertAlmostEqual(meteor_local.z, -np.cos(np.radians(42)) * np.cos(np.radians(130)) * 50000, delta = 1e-10)

    def test_modra_down(self):
        meteor_local = coord.Vector3D.from_local(self.modra, self.meteor_down)
        self.assertAlmostEqual(meteor_local.x, -np.cos(np.radians(48.352)) * np.cos(np.radians(17.313)) * 50000, delta = 1e-10)
        self.assertAlmostEqual(meteor_local.y, -np.cos(np.radians(48.352)) * np.sin(np.radians(17.313)) * 50000, delta = 1e-10)
        self.assertAlmostEqual(meteor_local.z, -np.sin(np.radians(48.352)) * 50000, delta = 1e-10)

    def test_arbitrary(self):
        meteor_local_np = coord.Vector3D.from_local(self.north_pole, self.meteor_down)
        meteor_local_ni = coord.Vector3D.from_local(self.null_island, self.meteor_down)
        meteor_local_sp = coord.Vector3D.from_local(self.south_pole, self.meteor_down)
    
        diff = (meteor_local_np - meteor_local_ni).norm()
        self.assertAlmostEqual(diff, 50000 * np.sqrt(2))

    def test_poles(self):
        north = coord.Vector3D.from_local(self.north_pole, self.meteor_down)
        south = coord.Vector3D.from_local(self.south_pole, self.meteor_down)
        summed = north + south
        
        self.assertAlmostEqual(summed.x, 0, delta=1e-10)
        self.assertAlmostEqual(summed.y, 0, delta=1e-10)
        self.assertAlmostEqual(summed.z, 0, delta=1e-10)
         

class CaseVector3DFormatting(unittest.TestCase):
    def setUp(self):
        self.vector = coord.Vector3D.from_geodetic(0, 0, 0)

    def test_default(self):
        self.assertEqual(
            f"{self.vector}",
            "(6371000, 0, 0)"
        )

    def test_cartesian_default(self):
        self.assertEqual(
            f"{self.vector:c}",
            "(6371000, 0, 0)"
        )

    def test_cartesian_digits(self):
        self.assertEqual(
            f"{self.vector:c12.6f}",
            "(6371000.000000,     0.000000,     0.000000)"
        )

    def test_spherical_default(self):
        self.assertEqual(
            f"{self.vector:s}",
            "0.000000° 0.000000° 6371000.000000"
        )
            
    def test_spherical_digits(self):
        self.assertEqual(
            f"{self.vector:sf}",
            "0.000000° 0.000000° 6371000.000000"
        )
            
    def test_spherical_digits2(self):
        self.assertEqual(
            f"{self.vector:s.3f}",
            "0.000° 0.000° 6371000.000"
        )

    def test_spherical_digits3(self):
        self.assertEqual(
            f"{self.vector:s.3f,12.3f}",
            "0.000° 0.000°  6371000.000"
        )
    
    def test_spherical_sci(self):
        self.assertEqual(
            f"{self.vector:s10.6f,10.3e}",
            "  0.000000°   0.000000°  6.371e+06"
        )

    def test_geodetic_default(self):
        self.assertEqual(
            f"{self.vector:g}",
            "0.000000° N 0.000000° E 0.000000"
        )


class CaseEarthLocation(unittest.TestCase):
    def setUp(self):
        self.el = coord.EarthLocation.from_geodetic(48.313525, 17.315423, 531)
        self.pure1 = coord.Vector3D(10, 20, 30)
        self.pure2 = coord.Vector3D(10, 20, 30)

    def test_add_pure(self):
        a = self.pure1 + self.pure2
        self.assertEqual(a.x, 20)
        self.assertEqual(a.y, 40)
        self.assertEqual(a.z, 60)

  #  def test_add_EarthLocation(self):
  #      with self.assertRaises(TypeError):
  #          a = self.el + self.pure1


if __name__ == '__main__':
    unittest.main()

