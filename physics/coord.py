import math, numbers
import numpy as np

from astropy.time import Time


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
        return self.norm() - 6371000

    @classmethod
    def fromSpherical(cls, lat, lon, r = 1):
        return Vector3D(
            r * math.cos(math.radians(lat)) * math.cos(math.radians(lon)),
            r * math.cos(math.radians(lat)) * math.sin(math.radians(lon)),
            r * math.sin(math.radians(lat))
        )

    @classmethod
    def fromGeodetic(cls, lat, lon, alt = 0):
        return Vector3D.fromSpherical(lat, lon, alt + 6371000)

    @classmethod
    def fromNumpyVector(cls, npv):
        return Vector3D(npv[0, 0], npv[1, 0], npv[2, 0])

    def toNumpyVector(self):
        return np.array([[self.x], [self.y], [self.z]])

    def __str__(self):
        return self.strCartesian()

    def strCartesian(self):
        return "({:7.0f}, {:7.0f}, {:7.0f})".format(
            self.x,
            self.y,
            self.z,
        )

    def strSpherical(self):
        return "{:5.2f}° {:6.2f}° {:7.0f} m".format(
            self.latitude(),
            self.longitude(),
            self.norm(),
        )

    def strGeodetic(self):
        return "{lat:9.6f}° {ns} {lon:9.6f}° {ew} {ele:6.0f} m".format(
            lat     = self.latitude(),
            ns      = 'N' if self.latitude() > 0 else 'S',
            lon     = self.longitude(),
            ew      = 'E' if self.longitude() > 0 else 'W',
            ele     = self.elevation(),
        )

def cosSin(angle):
    return np.cos(np.radians(angle)), np.sin(np.radians(angle))
   
def rotMatrixX(angle):
    c, s = cosSin(angle)
    return np.ndarray((3, 3), dtype = float, buffer = np.array([
        1,  0,  0,
        0,  c, -s,
        0,  s,  c,
    ]))

def rotMatrixY(angle):
    c, s = cosSin(angle)
    return np.ndarray((3, 3), dtype = float, buffer = np.array([
        c,  0, -s,
        0,  1,  0,
        s,  0,  c,
    ]))

def rotMatrixZ(angle):
    c, s = cosSin(angle)
    return np.ndarray((3, 3), dtype = float, buffer = np.array([
        c, -s,  0,
        s,  c,  0,
        0,  0,  1,
    ]))


def fastSun(time):
    obliquity           = 0.40908772
    mjd                 = Time(time).jd - 2451545.0
    meanLongitude       = math.radians((280.459 + 0.98564736 * mjd) % 360.0)
    meanAnomaly         = math.radians((357.529 + 0.98560028 * mjd) % 360.0)

    eclipticLongitude   = meanLongitude + 0.0334230551756 * math.sin(meanAnomaly) + 3.490658503988e-4 * math.sin(2 * meanAnomaly)

    rightAscension      = (math.degrees(math.atan2(math.cos(obliquity()) * math.sin(eclipticLongitude), math.cos(eclipticLongitude)))) % 360
    declination         = math.degrees(math.asin(math.sin(obliquity()) * math.sin(eclipticLongitude)))
    distance            = (1.00014 - 0.01671 * math.cos(meanAnomaly) - 0.00014 * math.cos(2 * meanAnomaly)) * 149597870700

    return Vector3D.fromSpherical(declination, rightAscension, distance)


def earthRotationAngle(time):
    mjd = Time(time).jd - 2451545.0
    return -360 * ((0.779057273264 + 1.00273781191135448 * mjd) % 1)
