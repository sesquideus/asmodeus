#pragma once
#define MIN_LAT -90
#define MAX_LAT 90
#define MIN_LON -360
#define MAX_LON 360
typedef struct {
    double x, y, z;
} ECEF;

typedef struct {
    double lat, lon, alt;
} WGS84;

