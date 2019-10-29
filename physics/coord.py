import math, numbers
import numpy as np

from astropy.time import Time
from physics import constants


class Vector3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __add__(self, other):
        if not isinstance(other, Vector3D):
            raise TypeError("Vector3D: cannot __add__ {}".format(type(other)))
        return Vector3D(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        )

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        if not isinstance(other, Vector3D):
            raise TypeError("Vector3D: cannot __iadd__ {}".format(type(other)))
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __sub__(self, other):
        if not isinstance(other, Vector3D):
            raise TypeError("Vector3D: cannot __sub__ {}".format(type(other)))
        return Vector3D(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z
        )
    
    def __isub__(self, other):
        if not isinstance(other, Vector3D):
            raise TypeError("Vector3D: cannot __isub__ {}".format(type(other)))
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __mul__(self, other):
        if isinstance(other, Vector3D):
            return self.x * other.x + self.y * other.y + self.z * other.z
        elif isinstance(other, numbers.Number):
            return Vector3D(
                self.x * other,
                self.y * other,
                self.z * other,
            )
        else:
            raise TypeError("Vector3D: cannot __mul__ {}".format(type(other)))

    def __imul__(self, other):
        if not isinstance(other, numbers.Number):
            raise TypeError("Vector3D: cannot __imul__ {}".format(type(other)))
        self.x *= other
        self.y *= other
        self.z *= other
        return self

    __rmul__ = __mul__

    def __matmul__(self, other):
        return self.toNumpyVector() @ other

    def __neg__(self):
        return Vector3D(
            -self.x,
            -self.y,
            -self.z,
        )

    def __truediv__(self, other):
        if not isinstance(other, numbers.Number):
            raise TypeError("Vector3D: Cannot __truediv__ with {}".format(type(other)))

        return Vector3D(
            self.x / other,
            self.y / other,
            self.z / other,
        )

    def norm(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def latitude(self):
        return math.degrees(math.asin(self.z / self.norm()))

    def longitude(self):
        return math.degrees(math.atan2(self.y, self.x)) % 360

    def elevation(self):
        return self.norm() - constants.EARTH_RADIUS

    @classmethod
    def from_spherical(cls, lat, lon, r = 1):
        return Vector3D(
            r * math.cos(math.radians(lat)) * math.cos(math.radians(lon)),
            r * math.cos(math.radians(lat)) * math.sin(math.radians(lon)),
            r * math.sin(math.radians(lat))
        )

    @classmethod
    def from_geodetic(cls, lat, lon, alt = 0):
        return Vector3D.from_spherical(lat, lon, alt + constants.EARTH_RADIUS)

    @classmethod
    def from_numpy_vector(cls, npv):
        return Vector3D(npv[0, 0], npv[1, 0], npv[2, 0])

    def to_numpy_vector(self):
        return np.array([[self.x], [self.y], [self.z]])

    def __str__(self):
        return self.str_cartesian()

    def str_cartesian(self):
        return "({:7.0f}, {:7.0f}, {:7.0f})".format(
            self.x,
            self.y,
            self.z,
        )

    def str_spherical(self):
        return "{:5.2f}° {:6.2f}° {:7.0f} m".format(
            self.latitude(),
            self.longitude(),
            self.norm(),
        )

    def str_geodetic(self):
        return "{lat:9.6f}° {ns}, {lon:9.6f}° {ew}, {ele:6.0f} m".format(
            lat     = self.latitude(),
            ns      = 'N' if self.latitude() >= 0 else 'S',
            lon     = self.longitude(),
            ew      = 'E' if self.longitude() >= 0 else 'W',
            ele     = self.elevation(),
        )

def cos_sin(angle):
    return np.cos(np.radians(angle)), np.sin(np.radians(angle))
   
def rot_matrix_x(angle):
    c, s = cos_sin(angle)
    return np.ndarray((3, 3), dtype = float, buffer = np.array([
        1,  0,  0,
        0,  c, -s,
        0,  s,  c,
    ]))

def rot_matrix_y(angle):
    c, s = cos_sin(angle)
    return np.ndarray((3, 3), dtype = float, buffer = np.array([
        c,  0, -s,
        0,  1,  0,
        s,  0,  c,
    ]))

def rot_matrix_z(angle):
    c, s = cos_sin(angle)
    return np.ndarray((3, 3), dtype = float, buffer = np.array([
        c, -s,  0,
        s,  c,  0,
        0,  0,  1,
    ]))


def fast_sun(time):
    obliquity           = 0.40908772
    mjd                 = Time(time).jd - 2451545.0
    mean_longitude      = math.radians((280.459 + 0.98564736 * mjd) % 360.0)
    mean_anomaly        = math.radians((357.529 + 0.98560028 * mjd) % 360.0)

    ecliptic_longitude  = mean_longitude + 0.0334230551756 * math.sin(mean_anomaly) + 3.490658503988e-4 * math.sin(2 * mean_anomaly)

    ra                  = (math.degrees(math.atan2(math.cos(obliquity()) * math.sin(ecliptic_longitude), math.cos(ecliptic_longitude)))) % 360
    dec                 = math.degrees(math.asin(math.sin(obliquity()) * math.sin(ecliptic_longitude)))
    distance            = (1.00014 - 0.01671 * math.cos(mean_anomaly) - 0.00014 * math.cos(2 * mean_anomaly)) * 149597870700

    return Vector3D.from_spherical(dec, ra, distance)


def earth_rotation_angle(time):
    mjd = Time(time).jd - 2451545.0
    return -360 * ((0.779057273264 + 1.00273781191135448 * mjd) % 1)
