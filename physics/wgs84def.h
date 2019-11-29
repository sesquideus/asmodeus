#pragma once
// Set to 1 to use degrees in WGS84GEO structure
// constants to convert between degrees and radians
// Design limits
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

