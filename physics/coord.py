import math
import numbers
import functools
import numpy as np

from astropy.time import Time
from physics import constants

#EARTH_ROTATION_VECTOR       = Vector3D(0, 0, 7.292115855e-5)


class Vector3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __add__(self, other):
        if not isinstance(other, Vector3D):
            raise TypeError(f"Vector3D: cannot __add__ {type(other)}")
        return Vector3D(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        )

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        if not isinstance(other, Vector3D):
            raise TypeError(f"Vector3D: cannot __iadd__ {type(other)}")
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __sub__(self, other):
        if not isinstance(other, Vector3D):
            raise TypeError(f"Vector3D: cannot __sub__ {type(other)}")
        return Vector3D(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z
        )
    
    def __isub__(self, other):
        if not isinstance(other, Vector3D):
            raise TypeError(f"Vector3D: cannot __isub__ {type(other)}")
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
            raise TypeError(f"Vector3D: cannot __mul__ with {type(other)}")

    def __imul__(self, other):
        if not isinstance(other, numbers.Number):
            raise TypeError(f"Vector3D: cannot __imul__ with {type(other)}")
        self.x *= other
        self.y *= other
        self.z *= other
        return self

    __rmul__ = __mul__

    def __matmul__(self, other):
        if isinstance(other, Vector3D):
            return self.as_numpy_vector() @ other.as_numpy_vector()
        return self.as_numpy_vector() @ other

    def __rmatmul__(self, other):
        return other @ self.as_numpy_vector()

    def __neg__(self):
        return Vector3D(
            -self.x,
            -self.y,
            -self.z,
        )

    def __truediv__(self, other):
        if not isinstance(other, numbers.Number):
            raise TypeError(f"Vector3D: Cannot __truediv__ with {type(other)}")

        return Vector3D(
            self.x / other,
            self.y / other,
            self.z / other,
        )

    def __xor__(self, other):
        """Computes 3D cross product of two Vector3D"""
        if isinstance(other, Vector3D):
            return __class__.from_numpy_vector(np.cross(self.as_numpy_vector(), other.as_numpy_vector()))
        else:
            raise TypeError(f"Vector3D: Cannot __xor__ (cross-product) with {type(other)}")

    def norm(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def latitude(self):
        return math.degrees(math.asin(self.z / self.norm()))

    def longitude(self):
        return math.degrees(math.atan2(self.y, self.x)) % 360

    def elevation(self):
        return self.norm() - constants.EARTH_RADIUS

    def unit(self):
        return self / self.norm()

    def derotation_matrix(self):
        """Get an inverse transformation matrix (this location to ECEF)"""
        return functools.reduce(np.dot, [
            np.fliplr(np.eye(3)),
            rot_matrix_y(-self.latitude()),
            rot_matrix_z(-self.longitude()),
        ])

    def rotation_matrix(self):
        """Get a rotation matrix (ECEF to this location)"""
        return functools.reduce(np.dot, [
            rot_matrix_z(self.longitude()),
            rot_matrix_y(self.latitude()),
            np.fliplr(np.eye(3)),
        ])

    @classmethod
    def from_spherical(cls, lat, lon, r = 1):
        """Create a new Vector3D from spherical coordinates
            lat:        latitude in degrees, north positive
            lon:        longitude in degrees, east positive
            r:          distance from the centre
        """
        return Vector3D(
            r * math.cos(math.radians(lat)) * math.cos(math.radians(lon)),
            r * math.cos(math.radians(lat)) * math.sin(math.radians(lon)),
            r * math.sin(math.radians(lat))
        )

    @classmethod
    def from_geodetic(cls, lat, lon, alt = 0):
        """Create a new Vector3D from geodetic coordinates
            lat:        latitude in degrees, north positive
            lon:        longitude in degrees, east positive
            r:          distance from the surface, up positive
        """
        return __class__.from_spherical(lat, lon, alt + constants.EARTH_RADIUS)

    def from_local(self: 'Vector3D', local: 'Vector3D') -> 'Vector3D':
        """Transform vector `local` as perceived at `position` from alt-az to ECEF frame
            alt-az (where x -> north, y -> east, z -> up) to
            ECEF (where x -> (0° N, 0° E), y -> (0° N, 90° E), z -> (90° N, 0° E))
        """
        return Vector3D.from_numpy_vector(self.rotation_matrix() @ local.as_numpy_vector())

    def to_local(self, ecef):
        """Transform vector `ecef` to local observer coordinate system"""
        return Vector3D.from_numpy_vector(self.derotation_matrix() @ ecef.as_numpy_vector())

    @classmethod
    def from_numpy_vector(cls, npv):
        return Vector3D(*npv)

    def as_numpy_vector(self):
        return np.array([self.x, self.y, self.z])

    def __str__(self):
        return self.str_cartesian()

    def str_cartesian(self, fmt='.0f'):
        return f"({self.x:{fmt}}, {self.y:{fmt}}, {self.z:{fmt}})"

    def str_spherical(self, fmta='9.6f', fmtd='6.0f'):
        return f"{self.latitude():{fmta}}° {self.longitude():{fmta}}° {self.norm():{fmtd}} m"

    def str_geodetic(self, fmta='9.6f', fmtd='6.0f'):
        lat = (self.latitude() + 90) % 180 - 90
        lon = (self.longitude() + 180) % 360 - 180
        ns = 'N' if self.latitude() >= 0 else 'S'
        ew = 'E' if lon <= 180 else 'W'
        return f"{self.latitude():{fmta}}° {ns}, {lon:{fmta}}° {ew}, {self.elevation():{fmtd}} m"

    def __format__(self, formatstr=''):
        if formatstr == '':
            return self.__str__()

        system, inner = formatstr[:1], formatstr[1:].split(',')
        print(inner, system)
        if system == 'c':
            return self.str_cartesian(*inner)
        elif system == 's':
            return self.str_spherical(fmt=inner[0])
        elif system == 'g':
            return self.str_geodetic(fmta=inner[0], fmtd=inner[1])

class Local(Vector3D):
    pass

class EarthLocation(Vector3D):
    @classmethod
    def from_spherical(cls, lat, lon, r = 1):
        return EarthLocation(
            r * math.cos(math.radians(lat)) * math.cos(math.radians(lon)),
            r * math.cos(math.radians(lat)) * math.sin(math.radians(lon)),
            r * math.sin(math.radians(lat))
        )

    @classmethod
    def from_geodetic(cls, lat, lon, alt = 0):
        return EarthLocation.from_spherical(lat, lon, alt + constants.EARTH_RADIUS)

    @classmethod
    def from_pure(cls, pure):
        return __class__(pure.x, pure.y, pure.z)

    def as_pure(self):
        return Vector3D(self.x, self.y, self.z)

    def __add__(self, other):
        if isinstance(other, EarthLocation):
            raise TypeError("Cannot add two EarthLocations")
        elif not isinstance(other, Vector3D):
            raise TypeError(f"EarthLocation: Cannot __add__ {type(other)}")
        else:
            return __class__.from_pure(self.as_pure() + other)

    def __str__(self):
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
