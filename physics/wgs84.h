#pragma once
#include "wgs84def.h"

double degrees(double rad);
double radians(double deg);

ECEF wgs84_to_ecef(double lat, double lon, double alt);
WGS84 ecef_to_wgs84(double x, double y, double z);

