#!/usr/bin/env python

from ctypes import CDLL, c_double, Structure
import math
from physics import coord

class Vector(Structure):
    _fields_ = [
        ("x", c_double),
        ("y", c_double),
        ("z", c_double),
    ]

so_file = "physics/wgs84.so"
f = CDLL(so_file)
f.wgs84_to_ecef.restype = Vector

for i in range(0, 10):
    w = f.wgs84_to_ecef(c_double(math.radians(48.3)), c_double(math.radians(17.3)), c_double(531))
    modra_wgs84 = coord.Vector3D(w.x, w.y, w.z)
    modra_sphere = coord.Vector3D.from_geodetic(48.3, 17.3, 531)

    w = f.wgs84_to_ecef(c_double(math.radians(48.3 + i)), c_double(math.radians(17.3)), c_double(531))
    meteor_wgs84 = coord.Vector3D(w.x, w.y, w.z)
    meteor_sphere = coord.Vector3D.from_geodetic(48.3 + i, 17.3, 531)

    diff_sphere = (meteor_sphere - modra_sphere)
    diff_wgs84 = (meteor_wgs84 - modra_wgs84)

    print(modra_wgs84, modra_sphere, diff_sphere, diff_wgs84, (diff_sphere - diff_wgs84).norm())

